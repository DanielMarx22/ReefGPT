import os
import sys
import uuid
import random
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from supabase import create_client, Client

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

UUIDS = {
    "salinity@test.com": "11111111-1111-1111-1111-111111111111",
    "aminos@test.com": "22222222-2222-2222-2222-222222222222",
    "flameangel@test.com": "33333333-3333-3333-3333-333333333333",
    "heater_failure@test.com": "44444444-4444-4444-4444-444444444444",
    "alk_depletion@test.com": "55555555-5555-5555-5555-555555555555"
}

def generate_telemetry(user_id, base_params, days=90, anomaly_fn=None):
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(days=days)
    
    # We will generate 4 readings per day (every 6 hours)
    total_readings = days * 4
    
    records = []
    
    current_params = base_params.copy()
    
    for i in range(total_readings):
        current_time = start_time + timedelta(hours=i*6)
        
        # Apply standard noise
        for p in current_params:
            if p == "pH": current_params[p] = max(7.6, min(8.6, current_params[p] + random.uniform(-0.02, 0.02)))
            if p == "Temperature": current_params[p] = max(76.0, min(82.0, current_params[p] + random.uniform(-0.1, 0.1)))
            if p == "Alkalinity": current_params[p] = max(6.0, min(12.0, current_params[p] + random.uniform(-0.05, 0.05)))
            if p == "Calcium": current_params[p] = max(300, min(600, current_params[p] + random.uniform(-2, 2)))
            if p == "Magnesium": current_params[p] = max(1100, min(1600, current_params[p] + random.uniform(-5, 5)))
            if p == "Nitrate": current_params[p] = max(0, min(100, current_params[p] + random.uniform(-0.5, 0.5)))
            if p == "Phosphate": current_params[p] = max(0, min(2.0, current_params[p] + random.uniform(-0.01, 0.01)))
            
        # Apply any anomaly function (e.g. salinity spike on day 89)
        if anomaly_fn:
            current_params = anomaly_fn(i, total_readings, current_params)
            
        for param, val in current_params.items():
            records.append({
                "user_id": user_id,
                "parameter": param,
                "value": round(val, 2),
                "timestamp": current_time.isoformat()
            })
            
    # Insert in chunks of 500
    for i in range(0, len(records), 500):
        chunk = records[i:i+500]
        supabase.table("metrics_log").insert(chunk).execute()

def seed_salinity():
    user_id = UUIDS["salinity@test.com"]
    print(f"Seeding Salinity Spike (Customer A) - {user_id}")
    
    # 1. Clean DB
    supabase.table("metrics_log").delete().eq("user_id", user_id).execute()
    supabase.table("inhabitants").delete().eq("user_id", user_id).execute()
    supabase.table("chat_history").delete().eq("user_id", user_id).execute()
    supabase.table("tank_events").delete().eq("user_id", user_id).execute()
    
    # 2. Telemetry (Ca and Mg spike on last day)
    def anomaly(i, total, params):
        if i >= total - 4: # Last day
            params["Calcium"] += 20
            params["Magnesium"] += 40
        return params
        
    generate_telemetry(user_id, {"pH": 8.1, "Temperature": 78.5, "Alkalinity": 8.5, "Calcium": 420, "Magnesium": 1350}, anomaly_fn=anomaly)
    
    # 3. Events
    now = datetime.now(timezone.utc)
    supabase.table("tank_events").insert({
        "user_id": user_id,
        "summary": "Replaced ATO reservoir with fresh bucket",
        "event_type": "Maintenance",
        "date": (now - timedelta(days=1)).isoformat()
    }).execute()
    
    # Inhabitants
    inhabitants_data = [
        {"user_id": user_id, "name": "Clownfish Pair", "species": "Amphiprion ocellaris", "category": "Fish", "count": 2, "size": "Medium", "date_added": (now - timedelta(days=100)).isoformat()},
        {"user_id": user_id, "name": "Bicolor Blenny", "species": "Ecsenius bicolor", "category": "Fish", "count": 1, "size": "2 inches", "date_added": (now - timedelta(days=80)).isoformat()},
        {"user_id": user_id, "name": "Green Star Polyps", "species": "Pachyclavularia violacea", "category": "Coral", "count": 1, "size": "Small", "date_added": (now - timedelta(days=60)).isoformat()},
        {"user_id": user_id, "name": "Toadstool Leather", "species": "Sarcophyton sp.", "category": "Coral", "count": 1, "size": "Medium", "date_added": (now - timedelta(days=50)).isoformat()}
    ]
    supabase.table("inhabitants").insert(inhabitants_data).execute()
    


def seed_aminos():
    user_id = UUIDS["aminos@test.com"]
    print(f"Seeding Amino Overdose (Customer B) - {user_id}")
    
    supabase.table("metrics_log").delete().eq("user_id", user_id).execute()
    supabase.table("inhabitants").delete().eq("user_id", user_id).execute()
    supabase.table("chat_history").delete().eq("user_id", user_id).execute()
    supabase.table("tank_events").delete().eq("user_id", user_id).execute()
    
    # Very stable telemetry, but high nutrients due to aminos
    generate_telemetry(user_id, {"pH": 8.3, "Temperature": 78.0, "Alkalinity": 9.0, "Calcium": 440, "Magnesium": 1400, "Nitrate": 45.0, "Phosphate": 0.25})
    
    now = datetime.now(timezone.utc)
    
    # Weekly Amino Events
    for w in range(12, 0, -1):
        supabase.table("tank_events").insert({
            "user_id": user_id,
            "summary": "Dosed 15ml Brightwell Coral Aminos",
            "event_type": "Dosing",
            "date": (now - timedelta(weeks=w)).isoformat()
        }).execute()
        
    # Inhabitants
    supabase.table("inhabitants").insert([
        {"user_id": user_id, "name": "Zoanthids", "species": "Zoanthid sp.", "category": "Coral", "count": 2, "date_added": (now - timedelta(days=90)).isoformat()},
        {"user_id": user_id, "name": "Ricordea Mushroom", "species": "Ricordea florida", "category": "Coral", "count": 3, "date_added": (now - timedelta(days=90)).isoformat()}
    ]).execute()
    


def seed_flameangel():
    user_id = UUIDS["flameangel@test.com"]
    print(f"Seeding Flame Angelfish (Customer C) - {user_id}")
    
    supabase.table("metrics_log").delete().eq("user_id", user_id).execute()
    supabase.table("inhabitants").delete().eq("user_id", user_id).execute()
    supabase.table("chat_history").delete().eq("user_id", user_id).execute()
    supabase.table("tank_events").delete().eq("user_id", user_id).execute()
    
    generate_telemetry(user_id, {"pH": 8.2, "Temperature": 77.8, "Alkalinity": 8.8, "Calcium": 430, "Magnesium": 1380})
    
    now = datetime.now(timezone.utc)
    
    supabase.table("inhabitants").insert([
        {"user_id": user_id, "name": "Acan Lord", "species": "Micromussa lordhowensis", "category": "Coral", "count": 5, "date_added": (now - timedelta(days=90)).isoformat()},
        {"user_id": user_id, "name": "Flame Angelfish", "species": "Centropyge loricula", "category": "Fish", "count": 1, "date_added": (now - timedelta(days=30)).isoformat()}
    ]).execute()
    
    supabase.table("tank_events").insert({
        "user_id": user_id,
        "summary": "Acans looking a bit closed today.",
        "event_type": "Observation",
        "date": (now - timedelta(days=10)).isoformat()
    }).execute()
    


def seed_heater_failure():
    user_id = UUIDS["heater_failure@test.com"]
    print(f"Seeding Heater Failure (Customer D) - {user_id}")
    
    supabase.table("metrics_log").delete().eq("user_id", user_id).execute()
    supabase.table("inhabitants").delete().eq("user_id", user_id).execute()
    supabase.table("chat_history").delete().eq("user_id", user_id).execute()
    supabase.table("tank_events").delete().eq("user_id", user_id).execute()
    supabase.table("tank_settings").delete().eq("user_id", user_id).execute()
    
    supabase.table("tank_settings").insert({"user_id": user_id, "livestock": "120 Gallon Mixed Reef. Lots of tangs, some LPS corals."}).execute()
    
    # 2. Telemetry (Temperature crash on last day)
    def anomaly(i, total, params):
        if i >= total - 4: # Last day
            params["Temperature"] -= 1.5 # cumulative drop over 4 periods = 6 degrees drop
        return params
        
    generate_telemetry(user_id, {"pH": 8.2, "Temperature": 78.5, "Alkalinity": 8.7, "Calcium": 430, "Magnesium": 1350}, anomaly_fn=anomaly)
    
    now = datetime.now(timezone.utc)
    
    # Inhabitants: very rich
    inhabitants_data = [
        {"user_id": user_id, "name": "Powder Blue Tang", "species": "Acanthurus leucosternon", "category": "Fish", "count": 1, "size": "4 inches", "date_added": (now - timedelta(days=180)).isoformat()},
        {"user_id": user_id, "name": "Yellow Tang", "species": "Zebrasoma flavescens", "category": "Fish", "count": 1, "size": "3 inches", "date_added": (now - timedelta(days=200)).isoformat()},
        {"user_id": user_id, "name": "Ocellaris Clownfish", "species": "Amphiprion ocellaris", "category": "Fish", "count": 2, "size": "2 inches", "date_added": (now - timedelta(days=365)).isoformat()},
        {"user_id": user_id, "name": "Coral Beauty Angelfish", "species": "Centropyge bispinosa", "category": "Fish", "count": 1, "size": "3 inches", "date_added": (now - timedelta(days=100)).isoformat()},
        {"user_id": user_id, "name": "Six Line Wrasse", "species": "Pseudocheilinus hexataenia", "category": "Fish", "count": 1, "size": "2 inches", "date_added": (now - timedelta(days=90)).isoformat()},
        {"user_id": user_id, "name": "Hammer Coral", "species": "Euphyllia ancora", "category": "Coral", "count": 3, "size": "Large colony", "date_added": (now - timedelta(days=150)).isoformat()},
        {"user_id": user_id, "name": "Frogspawn Coral", "species": "Euphyllia divisa", "category": "Coral", "count": 2, "size": "Medium", "date_added": (now - timedelta(days=150)).isoformat()},
        {"user_id": user_id, "name": "Green Star Polyps", "species": "Pachyclavularia violacea", "category": "Coral", "count": 5, "size": "Mat", "date_added": (now - timedelta(days=300)).isoformat()},
        {"user_id": user_id, "name": "Duncan Coral", "species": "Duncanopsammia axifuga", "category": "Coral", "count": 8, "size": "8 heads", "date_added": (now - timedelta(days=210)).isoformat()},
        {"user_id": user_id, "name": "Titanium Heater 300W", "species": "Equipment", "category": "Equipment", "count": 2, "date_added": (now - timedelta(days=400)).isoformat()}
    ]
    supabase.table("inhabitants").insert(inhabitants_data).execute()
    
    supabase.table("tank_events").insert({
        "user_id": user_id,
        "summary": "Replaced failed titanium heater with a new Eheim Jager",
        "event_type": "Maintenance",
        "date": (now - timedelta(hours=2)).isoformat()
    }).execute()
    


def seed_alk_depletion():
    user_id = UUIDS["alk_depletion@test.com"]
    print(f"Seeding Alk Depletion (Customer E) - {user_id}")
    
    supabase.table("metrics_log").delete().eq("user_id", user_id).execute()
    supabase.table("inhabitants").delete().eq("user_id", user_id).execute()
    supabase.table("chat_history").delete().eq("user_id", user_id).execute()
    supabase.table("tank_events").delete().eq("user_id", user_id).execute()
    supabase.table("tank_settings").delete().eq("user_id", user_id).execute()
    
    supabase.table("tank_settings").insert({"user_id": user_id, "livestock": "180 Gallon SPS Dominant Reef. High light, high flow."}).execute()
    
    # 2. Telemetry (Alk depletes over 90 days as SPS grow, Ca and Mg also deplete slightly)
    def anomaly(i, total, params):
        # Gradual depletion
        params["Alkalinity"] -= (2.5 / total) # Drops 2.5 dKH over 90 days (from 9.0 to 6.5)
        params["Calcium"] -= (40 / total) # Drops 40 ppm over 90 days
        params["Magnesium"] -= (30 / total)
        return params
        
    generate_telemetry(user_id, {"pH": 8.3, "Temperature": 77.5, "Alkalinity": 9.0, "Calcium": 440, "Magnesium": 1400}, anomaly_fn=anomaly)
    
    now = datetime.now(timezone.utc)
    
    # Inhabitants: Heavy SPS load
    inhabitants_data = [
        {"user_id": user_id, "name": "Strawberry Shortcake Acropora", "species": "Acropora microclados", "category": "Coral", "count": 1, "size": "Mini colony", "date_added": (now - timedelta(days=90)).isoformat()},
        {"user_id": user_id, "name": "Walt Disney Acropora", "species": "Acropora tenuis", "category": "Coral", "count": 1, "size": "Frag", "date_added": (now - timedelta(days=90)).isoformat()},
        {"user_id": user_id, "name": "PC Rainbow Acropora", "species": "Acropora sp.", "category": "Coral", "count": 1, "size": "Mini colony", "date_added": (now - timedelta(days=90)).isoformat()},
        {"user_id": user_id, "name": "Oregon Tort Acropora", "species": "Acropora tortuosa", "category": "Coral", "count": 1, "size": "Branch", "date_added": (now - timedelta(days=90)).isoformat()},
        {"user_id": user_id, "name": "Green Bali Slimer", "species": "Acropora yongei", "category": "Coral", "count": 1, "size": "Large branch", "date_added": (now - timedelta(days=90)).isoformat()},
        {"user_id": user_id, "name": "Red Planet Acropora", "species": "Acropora sp.", "category": "Coral", "count": 1, "size": "Table", "date_added": (now - timedelta(days=90)).isoformat()},
        {"user_id": user_id, "name": "Pink Birdsnest", "species": "Seriatopora hystrix", "category": "Coral", "count": 1, "size": "Fist size", "date_added": (now - timedelta(days=90)).isoformat()},
        {"user_id": user_id, "name": "Green Montipora Capricornis", "species": "Montipora capricornis", "category": "Coral", "count": 3, "size": "Plates", "date_added": (now - timedelta(days=90)).isoformat()},
        {"user_id": user_id, "name": "Red Montipora Digitata", "species": "Montipora digitata", "category": "Coral", "count": 2, "size": "Branches", "date_added": (now - timedelta(days=90)).isoformat()},
        {"user_id": user_id, "name": "Space Invader Pectinia", "species": "Pectinia sp.", "category": "Coral", "count": 1, "size": "Medium", "date_added": (now - timedelta(days=90)).isoformat()},
        {"user_id": user_id, "name": "Bowerbanki", "species": "Homophyllia bowerbanki", "category": "Coral", "count": 2, "size": "3 heads", "date_added": (now - timedelta(days=90)).isoformat()},
        {"user_id": user_id, "name": "Yellow Tang", "species": "Zebrasoma flavescens", "category": "Fish", "count": 1, "size": "4 inches", "date_added": (now - timedelta(days=120)).isoformat()},
        {"user_id": user_id, "name": "Purple Tang", "species": "Zebrasoma xanthurum", "category": "Fish", "count": 1, "size": "3 inches", "date_added": (now - timedelta(days=110)).isoformat()},
        {"user_id": user_id, "name": "Lyretail Anthias", "species": "Pseudanthias squamipinnis", "category": "Fish", "count": 5, "size": "2 inches", "date_added": (now - timedelta(days=100)).isoformat()},
        {"user_id": user_id, "name": "GHL Doser 2.1", "species": "Equipment", "category": "Equipment", "count": 1, "date_added": (now - timedelta(days=150)).isoformat()}
    ]
    supabase.table("inhabitants").insert(inhabitants_data).execute()
    
    # Weekly events of just looking at corals
    for w in range(12, 0, -2):
        supabase.table("tank_events").insert({
            "user_id": user_id,
            "summary": "Corals are encrusting nicely.",
            "event_type": "Observation",
            "date": (now - timedelta(weeks=w)).isoformat()
        }).execute()
        


def seed_all():
    print("Starting 90-Day Deep Data Generation...")
    seed_salinity()
    seed_aminos()
    seed_flameangel()
    seed_heater_failure()
    seed_alk_depletion()
    print("Done! Database fully populated with months of data.")

if __name__ == "__main__":
    seed_all()
