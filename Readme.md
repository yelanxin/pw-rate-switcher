



Here is the updated `README.md`.

I have rewritten the **First-Time Setup** section to be much stricter. It now explicitly warns users **NOT** to use ALSA, Jack, or direct hardware outputs, as that will break the app.

Copy and paste this into your `README.md`.

---

# 🎧 PipeWire Bit-Perfect Switcher

**A lightweight, automatic sample rate switcher for Audiophiles on Linux.**

<a href="https://github.com/yelanxin/pw-rate-switcher/raw/main/Screenshot%20from%202026-02-09%2023-20-57.png" target="_blank">
  <img src="https://github.com/yelanxin/pw-rate-switcher/raw/main/Screenshot%20from%202026-02-09%2023-20-57.png" width="50%" alt="Click to zoom in">
</a>

**PipeWire Rate Switcher** detects the sample rate of your currently playing music (Spotify, Chrome, MPD, etc.) and automatically adjusts the PipeWire clock to match it. This prevents audio resampling, ensuring a **Bit-Perfect** audio path to your DAC.

## 📋 Prerequisites

This app requires **PipeWire** to be your active sound server. It controls the PipeWire core directly.

To check if your system is compatible, run this in a terminal:

```bash
pactl info | grep "Server Name"

```

* **✅ Compatible:** `PulseAudio (on PipeWire x.x.x)`
*(This means you are using PipeWire with the PulseAudio compatibility layer. This is perfect.)*
* **❌ Incompatible:** `PulseAudio`
*(This means you are using the old legacy sound server. This app will not work.)*

## ✨ Features

* **Automatic Sample Rate Switching:** Instantly switches between 44.1kHz, 48kHz, 96kHz, 192kHz, and more based on the active stream.
* **Spotify & Browser Support:** Includes smart detection for apps that report non-standard rates (fixes the "Fractional Rate" issue in Spotify).
* **Strict Bit-Perfect Mode:** An optional "Audiophile Mode" that locks both the **Sample Rate** and **Quantum (Buffer Size)** for 1:1 hardware matching.
* **Real-Time Stats:** Displays the current Bit Depth (e.g., 32-bit Float) and Latency in milliseconds.
* **Flicker Protection:** Intelligent "Grace Period" logic prevents the clock from bouncing when tracks change.
* **System Tray Integration:** Runs silently in the background with a quick-access menu.

## 📥 Installation

### Option 1: Install via .deb (Ubuntu / Debian / Mint)

Download the latest release from the **[Releases Page](https://www.google.com/search?q=../../releases)**.

Open a terminal and install it:

```bash
sudo apt install ./pw-rate-switcher_0.1_all.deb

```

*(Note: If you get a dependency error, run `sudo apt --fix-broken install` and try again.)*

### Option 2: Run from Source

If you prefer to run the Python script directly:

1. **Install Dependencies:**
```bash
sudo apt install python3 python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 pipewire-bin gir1.2-ayatanaappindicator3-0.1

```


2. **Clone & Run:**
```bash
git clone https://github.com/yelanxin/pw-rate-switcher.git
cd pw-rate-switcher
chmod +x pw-rate-switcher.py
./pw-rate-switcher.py

```



## ⚙️ First-Time Setup (Important!)

To make this app work, you **MUST** configure your music player correctly.

1. **Set Audio Output to "PulseAudio" or "PipeWire"**
* In your music player (Strawberry, Deadbeef, MPD, etc.), go to settings and select **PulseAudio** or **PipeWire** as the output plugin.
* **⛔ DO NOT USE:** ALSA, ALSA Direct, Hardware Device (hw:0,0), or Jack.
* *Why?* If you select "ALSA Direct", the player steals the hardware from PipeWire. This prevents the app from controlling the clock.


2. **Verify System Output:**
* Open your OS **Settings** -> **Sound**.
* Select your DAC/Headphones here. The app will automatically control whatever device is selected in the system settings.



## 🎛️ Usage Guide

### 1. Standard Auto-Switching (Default)

Just play music! The app will detect the stream and switch the rate.

* **Best for:** Daily usage, Spotify, YouTube, Background music.
* **Behavior:** Switches Sample Rate (Hz) only. Leaves Buffer Size (Quantum) to the system default for stability.

### 2. Strict Bit-Perfect Mode

Toggle the **"Strict Bit-Perfect Mode"** switch for critical listening.

* **Best for:** High-Res lossless files, Audiophile DACs.
* **Behavior:** Locks **Sample Rate (Hz)** AND **Quantum (Buffer Size)** to match the source file exactly.
* *Warning:* This forces the hardware to change buffers instantly. If your audio crackles or pops, disable this mode.

### 3. Manual Override

Click any of the Hz buttons (44.1kHz, 96kHz, etc.) to force the system to a specific rate. This disables automatic switching until you re-enable it.

## ❓ FAQ

**Q: Does this app work with PulseAudio?**
**A:** No, it works with **PipeWire-Pulse**. Modern distros use PipeWire to "imitate" PulseAudio so your apps work, but the backend is PipeWire. This app talks to that backend. If you are on an old distro with legacy PulseAudio, this app cannot control it.

**Q: Why does it say "32-bit Float" when playing a 16-bit file?**
**A:** This is normal PipeWire behavior. PipeWire uses a 32-bit Floating Point container for all internal mixing to preserve quality and volume precision. Your DAC still receives the audio data perfectly intact (lossless).

**Q: The Latency number isn't moving. Is it broken?**
**A:** No, that is a good sign! Audio latency (buffer size) should be constant. If this number fluctuates wildly, it means your audio is unstable. A steady number (e.g., `21.3 ms`) means your connection is solid.

**Q: My screen flashes when the rate changes.**
**A:** Some DACs need a split second to change their internal clock. This is a hardware limitation, not a software bug.

## 🛠️ Building the Package

To build the `.deb` file yourself:

```bash
# 1. Create build structure
mkdir -p build/pw-rate-switcher/DEBIAN
mkdir -p build/pw-rate-switcher/usr/bin
mkdir -p build/pw-rate-switcher/usr/share/applications
mkdir -p build/pw-rate-switcher/usr/share/icons/hicolor/512x512/apps

# 2. Copy files
cp pw-rate-switcher.py build/pw-rate-switcher/usr/bin/pw-rate-switcher
cp pw-rate-switcher.png build/pw-rate-switcher/usr/share/icons/hicolor/512x512/apps/
chmod +x build/pw-rate-switcher/usr/bin/pw-rate-switcher

# 3. Build
dpkg-deb --build build/pw-rate-switcher pw-rate-switcher_0.1_all.deb

```

## 📄 License

MIT License. Feel free to modify and distribute.
