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
res = sb.table("inhabitants").select("*").limit(1).execute()
print("Data:", res.data)
