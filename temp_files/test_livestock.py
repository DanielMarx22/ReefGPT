import json
from supabase import create_client

url = ""
key = ""
with open("backend/.env", "r") as f:
    for line in f:
        if line.startswith("SUPABASE_URL"):
            url = line.split("=")[1].strip().strip('"').strip("'")
        elif line.startswith("SUPABASE_KEY"):
            key = line.split("=")[1].strip().strip('"').strip("'")

sb = create_client(url, key)
TEMP_USER_ID = "00000000-0000-0000-0000-000000000000"
profile = sb.table("inhabitants").select("*").eq("user_id", TEMP_USER_ID).execute()

livestock_items = []
for item in profile.data:
    name = item.get("name") or item.get("species")
    cat = item.get("category")
    item_id = item.get("id")
    count = item.get("count", 1)
    added = item.get("date_added")
    notes = item.get("notes") or "none"
    livestock_items.append(f"ID: {item_id} | Name: {name} | Category: {cat} | Count: {count} | Added: {added} | Notes: {notes}")

tank_livestock = "\n".join(livestock_items)
print("TANK LIVESTOCK STRING:")
print(tank_livestock)
