import urllib.request
import json
import sys

ip = "192.168.4.21"
url = f"http://{ip}/cgi-bin/status.json"

try:
    print(f"Fetching from {url}...")
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=5) as response:
        data = json.loads(response.read().decode())
        with open("apex_status.json", "w") as f:
            json.dump(data, f, indent=2)
    print("Success! Saved to apex_status.json")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
