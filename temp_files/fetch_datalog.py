import urllib.request
import sys

ip = "192.168.4.21"
url = f"http://{ip}/cgi-bin/datalog.xml"

try:
    print(f"Fetching from {url}...")
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=5) as response:
        data = response.read().decode()
        with open("apex_datalog.xml", "w") as f:
            f.write(data)
    print("Success! Saved to apex_datalog.xml. Snippet:")
    print(data[:500])
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
