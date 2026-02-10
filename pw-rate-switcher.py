#!/usr/bin/env python3
import sys
import subprocess
import threading
import json
import time
import re
import os
import signal
import gi

# ==============================================================================
# === TRAY ICON PROCESS (GTK 3) ===
# ==============================================================================
if len(sys.argv) > 1 and sys.argv[1] == "--tray":
    try:
        gi.require_version('Gtk', '3.0')
        gi.require_version('AppIndicator3', '0.1')
        from gi.repository import Gtk as Gtk3, AppIndicator3 as AppIndicator
    except ValueError:
        try:
            from gi.repository import AyatanaAppIndicator3 as AppIndicator
        except:
            sys.exit(0)

    def open_main_window(source):
        subprocess.Popen([sys.executable, sys.argv[0]])

    def quit_all(source):
        Gtk3.main_quit()
        sys.exit(0)

    icon_name = "pw-rate-switcher"
    indicator = AppIndicator.Indicator.new(
        "pw-rate-switcher-tray",
        icon_name,
        AppIndicator.IndicatorCategory.APPLICATION_STATUS
    )
    indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)

    menu = Gtk3.Menu()
    item_show = Gtk3.MenuItem(label="Open Settings")
    item_show.connect('activate', open_main_window)
    menu.append(item_show)
    menu.append(Gtk3.SeparatorMenuItem())
    item_quit = Gtk3.MenuItem(label="Quit")
    item_quit.connect('activate', quit_all)
    menu.append(item_quit)
    menu.show_all()
    indicator.set_menu(menu)
    Gtk3.main()
    sys.exit(0)

# ==============================================================================
# === MAIN APP WINDOW (GTK 4) ===
# ==============================================================================

try:
    gi.require_version('Gtk', '4.0')
    gi.require_version('Adw', '1')
except ValueError:
    print("Error: GTK4 or Libadwaita not found.")
    sys.exit(1)

from gi.repository import Gtk, Adw, GLib

class AutoRateSwitcher(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(application_id='com.eason.RateSwitcher', **kwargs)
        self.current_rate = "Unknown"
        self.running = True
        self.auto_mode = True
        self.strict_mode = False 
        self.tray_process = None
        self.manual_buttons = [] # Store buttons to disable them later
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        self.start_tray_icon()
        self.window = Adw.ApplicationWindow(application=app)
        self.window.set_title("PipeWire Rate Switcher")
        self.window.set_default_size(400, 620)
        self.window.set_icon_name("pw-rate-switcher")
        self.window.connect('close-request', self.on_window_close_request)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.window.set_content(root)
        root.append(Adw.HeaderBar())

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        content.set_margin_top(20)
        content.set_margin_bottom(20)
        content.set_margin_start(20)
        content.set_margin_end(20)
        root.append(content)

        # 1. INFO DISPLAY
        self.rate_label = Gtk.Label(label="Scanning...")
        self.rate_label.add_css_class("title-1")
        content.append(self.rate_label)
        
        self.status_label = Gtk.Label(label="Initializing...")
        self.status_label.add_css_class("title-3") 
        self.status_label.set_opacity(0.7)
        content.append(self.status_label)
        
        # Stats Badge Row
        stats_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        stats_box.set_halign(Gtk.Align.CENTER)
        
        self.bit_depth_label = Gtk.Label(label="-- bit")
        self.bit_depth_label.add_css_class("card")
        stats_box.append(self.bit_depth_label)

        self.latency_label = Gtk.Label(label="-- ms")
        self.latency_label.add_css_class("card")
        stats_box.append(self.latency_label)
        
        content.append(stats_box)
        content.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        
        # 2. STRICT BIT-PERFECT MODE (Master Switch)
        strict_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        strict_box.set_halign(Gtk.Align.CENTER)
        strict_label = Gtk.Label(label="Strict Bit-Perfect Mode")
        strict_label.add_css_class("heading")
        strict_label.set_tooltip_text("Enable exclusive 1:1 hardware matching.\nDisables manual controls.")
        self.strict_switch = Gtk.Switch()
        self.strict_switch.set_active(False)
        self.strict_switch.connect("state-set", self.on_strict_toggled)
        strict_box.append(strict_label)
        strict_box.append(self.strict_switch)
        content.append(strict_box)

        content.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # 3. STANDARD CONTROLS (Group to disable)
        self.standard_controls_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        content.append(self.standard_controls_box)

        # A. Auto Switch
        auto_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        auto_box.set_halign(Gtk.Align.CENTER)
        auto_label = Gtk.Label(label="Standard Auto-Switch")
        self.auto_switch = Gtk.Switch()
        self.auto_switch.set_active(True)
        self.auto_switch.connect("state-set", self.on_auto_toggled)
        auto_box.append(auto_label)
        auto_box.append(self.auto_switch)
        self.standard_controls_box.append(auto_box)

        # B. Manual Override
        grid_label = Gtk.Label(label="Manual Override")
        grid_label.add_css_class("heading")
        self.standard_controls_box.append(grid_label)

        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)
        grid.set_halign(Gtk.Align.CENTER)
        rates = ["44100", "48000", "88200", "96000", "176400", "192000"]
        for i, rate in enumerate(rates):
            btn = Gtk.Button(label=f"{int(rate)//1000} kHz")
            btn.connect("clicked", self.on_manual_click, rate)
            btn.set_size_request(100, 40)
            grid.attach(btn, i % 2, i // 2, 1, 1)
            self.manual_buttons.append(btn)

        self.standard_controls_box.append(grid)
        
        self.window.present()
        threading.Thread(target=self.monitor_pipewire, daemon=True).start()

    def start_tray_icon(self):
        if self.tray_process is None:
            self.tray_process = subprocess.Popen([sys.executable, sys.argv[0], "--tray"])

    def on_window_close_request(self, window):
        print("[UI] Window hidden (Check System Tray)")
        window.hide()
        return True

    def on_strict_toggled(self, switch, state):
        self.strict_mode = state
        
        # UI LOGIC: Gray out everything else when Strict Mode is ON
        self.standard_controls_box.set_sensitive(not state)
        
        if state:
            print("[UI] Strict Mode ON: Taking full control.")
            # Force Auto Mode ON internally (Strict implies Auto)
            self.auto_mode = True
            # Visual feedback
            self.rate_label.add_css_class("accent") 
        else:
            print("[UI] Strict Mode OFF: Restoring controls.")
            # Restore Auto Mode to whatever the switch says
            self.auto_mode = self.auto_switch.get_active()
            self.rate_label.remove_css_class("accent")

        # Reset monitoring to force immediate re-scan
        self.current_rate = "Unknown" 
        return False

    def on_auto_toggled(self, switch, state):
        # Only works if Strict Mode is OFF
        if not self.strict_mode:
            self.auto_mode = state
        return False

    def on_manual_click(self, button, rate):
        # Only works if Strict Mode is OFF
        if not self.strict_mode:
            self.auto_mode = False
            self.auto_switch.set_active(False)
            self.apply_rate(rate, 0)

    def get_dynamic_info(self, node_id):
        rate = None
        fmt = "Unknown"
        try:
            cmd = ["pw-cli", "enum-params", str(node_id), "Format"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            output = result.stdout.strip()
            if output:
                match_rate = re.search(r'rate.*?Int\s+(\d+)', output, re.DOTALL | re.IGNORECASE)
                if match_rate: rate = match_rate.group(1)
                
                match_fmt = re.search(r'AudioFormat:([a-zA-Z0-9]+)', output)
                if match_fmt: fmt = match_fmt.group(1)
                else:
                    match_simple = re.search(r'\((F32LE|S16LE|S24LE|S32LE|S24_32LE)\)', output)
                    if match_simple: fmt = match_simple.group(1)
        except: pass
        return rate, fmt

    def monitor_pipewire(self):
        idle_counter = 0
        MAX_IDLE_CYCLES = 3 
        
        while self.running:
            if self.tray_process and self.tray_process.poll() is not None:
                self.running = False
                self.quit()
                sys.exit(0)

            try:
                # If Strict Mode is ON, we are ALWAYS in Auto Mode
                effective_auto = self.auto_mode or self.strict_mode
                
                if not effective_auto:
                    time.sleep(1)
                    continue

                result = subprocess.run(['pw-dump'], capture_output=True, text=True)
                if result.stdout:
                    data = json.loads(result.stdout)
                    target_rate = None
                    target_quantum = 0 # 0 means Auto
                    active_app_name = None
                    active_format = "--"
                    active_latency = "--"

                    for obj in data:
                        if obj.get('type') != 'PipeWire:Interface:Node': continue
                            
                        props = obj.get('info', {}).get('props', {})
                        state = obj.get('info', {}).get('state', '').lower()
                        media_class = props.get('media.class', '')
                        node_id = obj.get('id')
                        name = props.get('node.name', 'Unknown')
                        app_name = props.get('application.name', name)

                        if state == "running" and "Stream/Output/Audio" in media_class:
                            rate = None
                            fmt = props.get('audio.format')
                            
                            if props.get('audio.rate'): rate = props.get('audio.rate')

                            if not rate:
                                node_rate = props.get('node.rate')
                                if node_rate and isinstance(node_rate, str):
                                    if '/' in node_rate:
                                        try:
                                            denom = node_rate.split('/')[1].strip()
                                            if denom.isdigit(): rate = denom
                                        except: pass
                                    elif node_rate.strip().isdigit():
                                        rate = node_rate.strip()

                            if not rate or str(rate) == "0" or not fmt or fmt == "Unknown":
                                dyn_rate, dyn_fmt = self.get_dynamic_info(node_id)
                                if not rate or str(rate) == "0": rate = dyn_rate
                                if dyn_fmt != "Unknown": fmt = dyn_fmt
                                
                            lat_str = props.get('node.latency')
                            current_quantum = 0
                            latency_ms = "-- ms"
                            
                            if lat_str and '/' in str(lat_str):
                                try:
                                    parts = str(lat_str).split('/')
                                    samples = float(parts[0])
                                    freq = float(parts[1])
                                    ms = (samples / freq) * 1000
                                    latency_ms = f"{ms:.1f} ms"
                                    current_quantum = int(samples)
                                except: pass

                            if rate and str(rate).isdigit() and int(rate) > 0:
                                target_rate = rate
                                target_quantum = current_quantum
                                active_app_name = app_name
                                active_format = fmt
                                active_latency = latency_ms
                                break 
                    
                    if target_rate:
                        idle_counter = 0
                        rate_changed = (target_rate != self.current_rate)
                        
                        # In strict mode, we always re-apply if quantum changes
                        if rate_changed or self.strict_mode:
                            quantum_to_set = target_quantum if self.strict_mode else 0
                            print(f"[System] Locked to {active_app_name}: {target_rate}Hz")
                            self.apply_rate(target_rate, quantum_to_set)
                        
                        GLib.idle_add(self.update_ui, str(target_rate), active_app_name, str(active_format), str(active_latency))
                    
                    else:
                        idle_counter += 1
                        if idle_counter >= MAX_IDLE_CYCLES:
                            if self.current_rate != "Unknown":
                                print("[System] Idle confirmed.")
                                self.current_rate = "Unknown"
                                GLib.idle_add(self.update_status, "Idle")
                                subprocess.run(["pw-metadata", "-n", "settings", "0", "clock.force-quantum", "0"])
                
                time.sleep(1.5)

            except Exception as e:
                print(f"[Error] {e}")
                time.sleep(5)

    def apply_rate(self, rate, quantum=0):
        try:
            subprocess.run(["pw-metadata", "-n", "settings", "0", "clock.force-rate", str(rate)])
            
            if quantum > 0 and (quantum & (quantum-1) == 0) and quantum >= 32 and quantum <= 8192:
                 subprocess.run(["pw-metadata", "-n", "settings", "0", "clock.force-quantum", str(quantum)])
            else:
                 subprocess.run(["pw-metadata", "-n", "settings", "0", "clock.force-quantum", "0"])

            self.current_rate = str(rate)
        except Exception as e:
            pass

    def update_ui(self, rate, app_name, fmt, latency):
        self.rate_label.set_label(f"{rate} Hz")
        self.status_label.set_label(f"{app_name}")
        
        if fmt == "F32LE": fmt_text = "32-bit Float"
        elif fmt == "S32LE": fmt_text = "32-bit Int"
        elif fmt == "S24LE": fmt_text = "24-bit"
        elif fmt == "S16LE": fmt_text = "16-bit"
        elif fmt == "S24_32LE": fmt_text = "24/32-bit"
        else: fmt_text = fmt if fmt else "Unknown"
        
        self.bit_depth_label.set_label(f" {fmt_text} ")
        self.latency_label.set_label(f" {latency} ")
        return False

    def update_status(self, text):
        self.status_label.set_label(text)
        self.rate_label.set_label("Scanning...")
        self.bit_depth_label.set_label("--")
        self.latency_label.set_label("--")
        return False

if __name__ == "__main__":
    app = AutoRateSwitcher()
    app.run(sys.argv)
