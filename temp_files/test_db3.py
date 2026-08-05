import os
import sys
from supabase import create_client

url = ""
key = ""
with open("backend/.env", "r") as f:
    for line in f:
        if line.startswith("SUPABASE_URL"):
            url = line.split("=")[1].strip().strip('"').strip("'")
        elif line.startswith("SUPABASE_KEY"):
            key = line.split("=")[1].strip().strip('"').strip("'")

if not url or not key:
    print("No credentials found")
    sys.exit(1)

sb = create_client(url, key)
res = sb.table("inhabitants").select("*").execute()
print(f"Total Inhabitants: {len(res.data)}")
for r in res.data:
    print(f"[{r.get('id')}] Category: {r.get('category')} | Species: {r.get('species')} | Name: {r.get('name')}")
