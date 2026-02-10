import subprocess
import json
import time

print("--- PipeWire Diagnostic Scanner ---")
print("Play some audio now. Scanning for active streams...\n")

while True:
    try:
        # Dump the current PipeWire graph
        result = subprocess.run(['pw-dump'], capture_output=True, text=True)
        data = json.loads(result.stdout)
        
        found_something = False

        for obj in data:
            # We are looking for Nodes (apps and devices)
            if obj.get('type') == 'PipeWire:Interface:Node':
                info = obj.get('info', {})
                props = info.get('props', {})
                state = info.get('state')
                
                # Check if it is running (playing audio)
                if state == "running":
                    name = props.get('node.name', 'Unknown')
                    media_class = props.get('media.class', 'No Class')
                    rate = props.get('audio.rate', 'No Rate')
                    
                    print(f"[ACTIVE NODE FOUND]")
                    print(f"  Name:  {name}")
                    print(f"  Class: {media_class}")
                    print(f"  Rate:  {rate}")
                    print(f"  ID:    {obj.get('id')}")
                    print("-" * 30)
                    found_something = True

        if not found_something:
            print("No 'running' nodes found. Is music definitely playing?")
        
        print("\nScanning again in 3 seconds... (Ctrl+C to stop)\n")
        time.sleep(3)

    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f"Error: {e}")
        break
