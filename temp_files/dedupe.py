import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

res = supabase.table("metrics_log").select("id, timestamp, parameter, value").execute()
logs = res.data

to_delete = []

for param in ["Alkalinity", "Calcium", "Magnesium"]:
    param_logs = [l for l in logs if l["parameter"] == param]
    if not param_logs: continue
    
    # Sort chronological
    param_logs.sort(key=lambda x: x["timestamp"])
    
    last_val = None
    for l in param_logs:
        if last_val is None:
            last_val = l["value"]
            continue
        if l["value"] == last_val:
            to_delete.append(l["id"])
        else:
            last_val = l["value"]

print(f"Found {len(to_delete)} duplicate Trident logs to delete.")

# Delete in batches
batch_size = 100
for i in range(0, len(to_delete), batch_size):
    batch = to_delete[i:i+batch_size]
    print(f"Deleting batch of {len(batch)}...")
    supabase.table("metrics_log").delete().in_("id", batch).execute()

print("Deduplication complete.")
