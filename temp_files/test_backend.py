import urllib.request
import json

data = json.dumps({
    "category": "Coral",
    "species": "Torch",
    "name": "",
    "size": "",
    "notes": "",
    "image_url": "",
    "care_info": ""
}).encode("utf-8")

req = urllib.request.Request(
    "http://127.0.0.1:8000/add-inhabitant",
    data=data,
    headers={"Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req) as response:
        print("Status:", response.status)
        print("Body:", response.read().decode())
except urllib.error.HTTPError as e:
    print("HTTP Error:", e.code)
    print("Error Body:", e.read().decode())
except Exception as e:
    print("Other error:", e)
