import urllib.request
import json
try:
    req = urllib.request.Request("http://192.168.4.21/cgi-bin/status.json")
    with urllib.request.urlopen(req, timeout=5) as response:
        data = json.loads(response.read().decode())
        print(json.dumps(data.get("istat", {}), indent=2))
except Exception as e:
    print("Error:", e)
