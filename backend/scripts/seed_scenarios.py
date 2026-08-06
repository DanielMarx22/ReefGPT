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
    "alk_spike@test.com": "11111111-1111-1111-1111-111111111111",
    "amino_toxicity@test.com": "22222222-2222-2222-2222-222222222222",
    "rogue_fish@test.com": "33333333-3333-3333-3333-333333333333",
    "heater_failure@test.com": "44444444-4444-4444-4444-444444444444",
    "alk_depletion@test.com": "55555555-5555-5555-5555-555555555555"
}

def clear_user_data(user_id):
    supabase.table("metrics_log").delete().eq("user_id", user_id).execute()
    supabase.table("inhabitants").delete().eq("user_id", user_id).execute()
    supabase.table("chat_history").delete().eq("user_id", user_id).execute()
    supabase.table("tank_events").delete().eq("user_id", user_id).execute()
    supabase.table("tank_settings").delete().eq("user_id", user_id).execute()

def generate_telemetry(user_id, base_params, days=90, anomaly_fn=None):
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(days=days)
    
    total_readings = days * 4 # Every 6 hours
    records = []
    ideal_params = base_params.copy()
    
    for i in range(total_readings):
        current_time = start_time + timedelta(hours=i*6)
        
        if anomaly_fn:
            ideal_params = anomaly_fn(i, total_readings, ideal_params)
            
        current_params = ideal_params.copy()
        
        # Add slight non-cumulative noise for realism
        for p in current_params:
            if p == "pH": current_params[p] += random.uniform(-0.02, 0.02)
            if p == "Temperature": current_params[p] += random.uniform(-0.1, 0.1)
            if p == "Alkalinity": current_params[p] += random.uniform(-0.05, 0.05)
            if p == "Calcium": current_params[p] += random.uniform(-2, 2)
            if p == "Magnesium": current_params[p] += random.uniform(-5, 5)
            if p == "Nitrate": current_params[p] += random.uniform(-0.5, 0.5)
            if p == "Phosphate": current_params[p] += random.uniform(-0.01, 0.01)
            
        for param, val in current_params.items():
            records.append({
                "user_id": user_id,
                "parameter": param,
                "value": round(val, 2),
                "timestamp": current_time.isoformat()
            })
            
    for i in range(0, len(records), 500):
        chunk = records[i:i+500]
        supabase.table("metrics_log").insert(chunk).execute()


def generate_notes(user_id, ai_summaries, user_notes):
    now = datetime.now(timezone.utc)
    events = []
    
    # Generate 12 weeks of AI Summaries
    for w in range(12, 0, -1):
        summary = random.choice(ai_summaries)
        events.append({
            "user_id": user_id, 
            "summary": summary,
            "event_type": "AI Summary", 
            "date": (now - timedelta(weeks=w)).isoformat()
        })
        
    # Generate user notes interspersed
    for note in user_notes:
        events.append({
            "user_id": user_id, 
            "summary": note["summary"],
            "event_type": "User Note", 
            "date": (now - timedelta(days=note["days_ago"])).isoformat()
        })
        
    events = sorted(events, key=lambda x: x["date"])
    supabase.table("tank_events").insert(events).execute()


# ===============================
# SCENARIO 1: The Nano Mixed Reef
# ===============================
def seed_nano_mixed_reef():
    user_id = UUIDS["alk_spike@test.com"]
    print(f"Seeding Nano Mixed Reef - {user_id}")
    clear_user_data(user_id)
    
    def anomaly(i, total, params):
        if i >= total - 4: # Last 24 hours spike
            params["Calcium"] += 20.0
            params["Alkalinity"] += 1.0
        return params
        
    generate_telemetry(user_id, {"pH": 8.0, "Temperature": 78.5, "Alkalinity": 8.2, "Calcium": 420, "Magnesium": 1350, "Nitrate": 40.0, "Phosphate": 0.5}, anomaly_fn=anomaly)
    
    now = datetime.now(timezone.utc)
    inhabitants = [
        {"user_id": user_id, "name": "Clownfish Pair", "species": "Amphiprion ocellaris", "category": "Fish", "count": 2, "size": "Small", "date_added": (now - timedelta(days=90)).isoformat()},
        {"user_id": user_id, "name": "Watchman Goby", "species": "Cryptocentrus cinctus", "category": "Fish", "count": 1, "size": "Small", "date_added": (now - timedelta(days=80)).isoformat()},
        {"user_id": user_id, "name": "Pistol Shrimp", "species": "Alpheus sp.", "category": "Invertebrate", "count": 1, "size": "Small", "date_added": (now - timedelta(days=80)).isoformat()},
        {"user_id": user_id, "name": "Rasta Zoanthids", "species": "Zoanthid sp.", "category": "Coral", "count": 1, "size": "Frag", "date_added": (now - timedelta(days=70)).isoformat()},
        {"user_id": user_id, "name": "Duncan Coral", "species": "Duncanopsammia axifuga", "category": "Coral", "count": 3, "size": "3 Heads", "date_added": (now - timedelta(days=60)).isoformat()},
        {"user_id": user_id, "name": "Green Star Polyps", "species": "Pachyclavularia violacea", "category": "Coral", "count": 1, "size": "Frag", "date_added": (now - timedelta(days=50)).isoformat()},
        {"user_id": user_id, "name": "Kenya Tree Coral", "species": "Capnella sp.", "category": "Coral", "count": 1, "size": "Medium", "date_added": (now - timedelta(days=45)).isoformat()},
        {"user_id": user_id, "name": "Frogspawn Coral", "species": "Euphyllia divisa", "category": "Coral", "count": 1, "size": "2 Heads", "date_added": (now - timedelta(days=40)).isoformat()},
        {"user_id": user_id, "name": "Xenia", "species": "Xenia sp.", "category": "Coral", "count": 1, "size": "Small Colony", "date_added": (now - timedelta(days=35)).isoformat()},
        {"user_id": user_id, "name": "Astrea Snails", "species": "Astrea tecta", "category": "Invertebrate", "count": 5, "size": "Small", "date_added": (now - timedelta(days=90)).isoformat()},
        {"user_id": user_id, "name": "Blue Leg Hermit Crabs", "species": "Clibanarius tricolor", "category": "Invertebrate", "count": 3, "size": "Small", "date_added": (now - timedelta(days=90)).isoformat()},
        {"user_id": user_id, "name": "20g AIO Tank", "species": "Tank", "category": "Equipment", "count": 1, "notes": "No ATO. Manual Top Offs."},
        {"user_id": user_id, "name": "AI Prime 16HD", "species": "Light", "category": "Equipment", "count": 1, "date_added": (now - timedelta(days=45)).isoformat()},
        {"user_id": user_id, "name": "Cobalt Neo-Therm 75W", "species": "Heater", "category": "Equipment", "count": 1, "date_added": (now - timedelta(days=90)).isoformat()},
        {"user_id": user_id, "name": "Hydor Koralia Nano 240", "species": "Powerhead", "category": "Equipment", "count": 1, "notes": "Cheap nonadjustable powerhead", "date_added": (now - timedelta(days=90)).isoformat()},
        {"user_id": user_id, "name": "Biocube Protein Skimmer", "species": "Skimmer", "category": "Equipment", "count": 1, "notes": "Small air-driven skimmer", "date_added": (now - timedelta(days=30)).isoformat()}
    ]
    supabase.table("inhabitants").insert(inhabitants).execute()
    
    ai_summaries = [
        "Tank parameters remain stable. No major fluctuations detected this week.",
        "Nitrates slightly elevated, but within acceptable range for soft corals.",
        "Manual top-off frequency is consistent. Salinity proxy looks stable.",
        "No new inhabitants logged. Ecosystem appears balanced.",
        "Minor pH drop overnight, but nothing critical.",
        "Tank health is good. Calcium and Alkalinity consumption is low."
    ]
    user_notes = [
        {"summary": "Scraped the glass and did a 2g water change.", "days_ago": 60},
        {"summary": "Upgraded light to AI Prime 16HD today. Running at 40% intensity.", "days_ago": 45},
        {"summary": "Added a pistol shrimp to pair with the watchman goby.", "days_ago": 20},
        {"summary": "Did a 10% water change. Corals look happy.", "days_ago": 7},
        {"summary": "Accidentally used saltwater instead of RODI for top off! Oh no!", "days_ago": 1}
    ]
    generate_notes(user_id, ai_summaries, user_notes)

# ===============================
# SCENARIO 2: High-End SPS Reef
# ===============================
def seed_sps_reef():
    user_id = UUIDS["amino_toxicity@test.com"]
    print(f"Seeding SPS Reef - {user_id}")
    clear_user_data(user_id)
    
    generate_telemetry(user_id, {"pH": 8.3, "Temperature": 78.0, "Alkalinity": 8.5, "Calcium": 440, "Magnesium": 1400, "Nitrate": 5.0, "Phosphate": 0.05})
    
    now = datetime.now(timezone.utc)
    inhabitants = [
        {"user_id": user_id, "name": "Yellow Tang", "species": "Zebrasoma flavescens", "category": "Fish", "count": 1, "size": "4 inches", "date_added": (now - timedelta(days=200)).isoformat()},
        {"user_id": user_id, "name": "Purple Tang", "species": "Zebrasoma xanthurum", "category": "Fish", "count": 1, "size": "3 inches", "date_added": (now - timedelta(days=150)).isoformat()},
        {"user_id": user_id, "name": "Lyretail Anthias", "species": "Pseudanthias squamipinnis", "category": "Fish", "count": 7, "size": "2 inches", "date_added": (now - timedelta(days=100)).isoformat()},
        {"user_id": user_id, "name": "Bimaculatus Anthias", "species": "Pseudanthias bimaculatus", "category": "Fish", "count": 3, "size": "3 inches", "date_added": (now - timedelta(days=90)).isoformat()},
        {"user_id": user_id, "name": "Leopard Wrasse", "species": "Macropharyngodon meleagris", "category": "Fish", "count": 1, "size": "3 inches", "date_added": (now - timedelta(days=120)).isoformat()},
        {"user_id": user_id, "name": "Melanurus Wrasse", "species": "Halichoeres melanurus", "category": "Fish", "count": 1, "size": "4 inches", "date_added": (now - timedelta(days=130)).isoformat()},
        {"user_id": user_id, "name": "Mated Mandarin Pair", "species": "Synchiropus splendidus", "category": "Fish", "count": 2, "size": "Medium", "date_added": (now - timedelta(days=250)).isoformat()},
        {"user_id": user_id, "name": "Jawbreaker Mushroom", "species": "Discosoma sp.", "category": "Coral", "count": 2, "size": "Medium", "date_added": (now - timedelta(days=250)).isoformat()},
        {"user_id": user_id, "name": "Bounce Mushroom", "species": "Rhodactis sp.", "category": "Coral", "count": 1, "size": "Small", "date_added": (now - timedelta(days=150)).isoformat()},
        {"user_id": user_id, "name": "Florida Ricordea", "species": "Ricordea florida", "category": "Coral", "count": 5, "size": "Small", "date_added": (now - timedelta(days=200)).isoformat()},
        {"user_id": user_id, "name": "Strawberry Shortcake Acropora", "species": "Acropora microclados", "category": "Coral", "count": 1, "size": "Large Colony", "date_added": (now - timedelta(days=365)).isoformat()},
        {"user_id": user_id, "name": "Walt Disney Acropora", "species": "Acropora tenuis", "category": "Coral", "count": 1, "size": "Mini Colony", "date_added": (now - timedelta(days=250)).isoformat()},
        {"user_id": user_id, "name": "Homewrecker Acropora", "species": "Acropora tenuis", "category": "Coral", "count": 1, "size": "Frag", "date_added": (now - timedelta(days=150)).isoformat()},
        {"user_id": user_id, "name": "PC Rainbow Acropora", "species": "Acropora sp.", "category": "Coral", "count": 1, "size": "Medium Colony", "date_added": (now - timedelta(days=200)).isoformat()},
        {"user_id": user_id, "name": "Trochus Snails", "species": "Trochus sp.", "category": "Invertebrate", "count": 30, "size": "Medium", "date_added": (now - timedelta(days=360)).isoformat()},
        {"user_id": user_id, "name": "Cerith Snails", "species": "Cerithium sp.", "category": "Invertebrate", "count": 20, "size": "Small", "date_added": (now - timedelta(days=360)).isoformat()},
        {"user_id": user_id, "name": "Scarlet Hermit Crabs", "species": "Paguristes cadenati", "category": "Invertebrate", "count": 15, "size": "Small", "date_added": (now - timedelta(days=350)).isoformat()},
        {"user_id": user_id, "name": "Blue Leg Hermit Crabs", "species": "Clibanarius tricolor", "category": "Invertebrate", "count": 15, "size": "Small", "date_added": (now - timedelta(days=350)).isoformat()},
        {"user_id": user_id, "name": "Cleaner Shrimp", "species": "Lysmata amboinensis", "category": "Invertebrate", "count": 2, "size": "Large", "date_added": (now - timedelta(days=300)).isoformat()},
        {"user_id": user_id, "name": "Red Sea Reefer 525XL", "species": "Tank", "category": "Equipment", "count": 1, "notes": "139 Gallons total. 40g Sump.", "date_added": (now - timedelta(days=400)).isoformat()},
        {"user_id": user_id, "name": "Radion XR30 Blue G6", "species": "Light", "category": "Equipment", "count": 3, "date_added": (now - timedelta(days=400)).isoformat()},
        {"user_id": user_id, "name": "Reef Octopus Elite 200", "species": "Skimmer", "category": "Equipment", "count": 1, "date_added": (now - timedelta(days=400)).isoformat()},
        {"user_id": user_id, "name": "Neptune Apex A3 Pro", "species": "Controller", "category": "Equipment", "count": 1, "date_added": (now - timedelta(days=400)).isoformat()},
        {"user_id": user_id, "name": "Neptune Trident", "species": "Testing", "category": "Equipment", "count": 1, "date_added": (now - timedelta(days=390)).isoformat()},
        {"user_id": user_id, "name": "Neptune DOS", "species": "Doser", "category": "Equipment", "count": 2, "date_added": (now - timedelta(days=390)).isoformat()},
        {"user_id": user_id, "name": "Ecotech MP40mQD", "species": "Powerhead", "category": "Equipment", "count": 4, "date_added": (now - timedelta(days=400)).isoformat()},
        {"user_id": user_id, "name": "Ecotech Vectra L2", "species": "Return Pump", "category": "Equipment", "count": 1, "date_added": (now - timedelta(days=400)).isoformat()},
        {"user_id": user_id, "name": "AquaUV 57W Sterilizer", "species": "UV", "category": "Equipment", "count": 1, "date_added": (now - timedelta(days=300)).isoformat()},
        {"user_id": user_id, "name": "Clarisea SK-5000", "species": "Fleece Roller", "category": "Equipment", "count": 1, "date_added": (now - timedelta(days=400)).isoformat()},
        {"user_id": user_id, "name": "Tunze Osmolator 3155", "species": "ATO", "category": "Equipment", "count": 1, "date_added": (now - timedelta(days=400)).isoformat()},
        {"user_id": user_id, "name": "BRS Titanium Heater 600W", "species": "Heater", "category": "Equipment", "count": 2, "date_added": (now - timedelta(days=400)).isoformat()}
    ]
    supabase.table("inhabitants").insert(inhabitants).execute()
    
    ai_summaries = [
        "Core parameters (Alk/Ca/Mg) are locked in. Excellent stability.",
        "Nutrient levels are incredibly low and stable (Nitrate 5ppm).",
        "No major equipment alarms. Skimmer functioning normally.",
        "Consistent daily trends in pH. Good gas exchange.",
        "No new additions in the last week. Maturing ecosystem."
    ]
    user_notes = [
        {"summary": "Cleaned skimmer cup. It was pulling some dark, nasty skimmate.", "days_ago": 70},
        {"summary": "Started feeding LRS Reef Frenzy twice a day for the Anthias.", "days_ago": 40},
        {"summary": "Began dosing Acropower aminos heavily every day to boost growth.", "days_ago": 10},
        {"summary": "Some of the mushrooms look a bit lighter in color, maybe need more aminos?", "days_ago": 2}
    ]
    generate_notes(user_id, ai_summaries, user_notes)

# ===============================
# SCENARIO 3: Massive FOWLR
# ===============================
def seed_massive_fowlr():
    user_id = UUIDS["rogue_fish@test.com"]
    print(f"Seeding Massive FOWLR - {user_id}")
    clear_user_data(user_id)
    
    generate_telemetry(user_id, {"pH": 8.0, "Temperature": 77.8, "Alkalinity": 7.0, "Calcium": 380, "Magnesium": 1250, "Nitrate": 20.0, "Phosphate": 0.1})
    
    now = datetime.now(timezone.utc)
    inhabitants = [
        {"user_id": user_id, "name": "Niger Triggerfish", "species": "Odonus niger", "category": "Fish", "count": 1, "size": "6 inches", "date_added": (now - timedelta(days=400)).isoformat()},
        {"user_id": user_id, "name": "Porcupine Puffer", "species": "Diodon holocanthus", "category": "Fish", "count": 1, "size": "7 inches", "date_added": (now - timedelta(days=350)).isoformat()},
        {"user_id": user_id, "name": "Emperor Angelfish", "species": "Pomacanthus imperator", "category": "Fish", "count": 1, "size": "8 inches", "date_added": (now - timedelta(days=300)).isoformat()},
        {"user_id": user_id, "name": "Clown Triggerfish", "species": "Balistoides conspicillum", "category": "Fish", "count": 1, "size": "5 inches", "date_added": (now - timedelta(days=250)).isoformat()},
        {"user_id": user_id, "name": "Snowflake Eel", "species": "Echidna nebulosa", "category": "Fish", "count": 1, "size": "18 inches", "date_added": (now - timedelta(days=380)).isoformat()},
        {"user_id": user_id, "name": "Sohal Tang", "species": "Acanthurus sohal", "category": "Fish", "count": 1, "size": "7 inches", "date_added": (now - timedelta(days=200)).isoformat()},
        {"user_id": user_id, "name": "Flame Angelfish", "species": "Centropyge loricula", "category": "Fish", "count": 1, "size": "3 inches", "date_added": (now - timedelta(days=14)).isoformat()},
        {"user_id": user_id, "name": "Harlequin Tusk", "species": "Choerodon fasciatus", "category": "Fish", "count": 1, "size": "6 inches", "date_added": (now - timedelta(days=150)).isoformat()},
        {"user_id": user_id, "name": "210g Glass Tank", "species": "Tank", "category": "Equipment", "count": 1, "notes": "FOWLR setup. 200lbs Live Rock.", "date_added": (now - timedelta(days=450)).isoformat()},
        {"user_id": user_id, "name": "Fluval FX6", "species": "Filter", "category": "Equipment", "count": 2, "date_added": (now - timedelta(days=450)).isoformat()},
        {"user_id": user_id, "name": "Bashsea Twisted Skimmer", "species": "Skimmer", "category": "Equipment", "count": 1, "date_added": (now - timedelta(days=400)).isoformat()},
        {"user_id": user_id, "name": "Current USA Orbit Marine", "species": "Light", "category": "Equipment", "count": 2, "date_added": (now - timedelta(days=450)).isoformat()},
        {"user_id": user_id, "name": "Maxspect Gyre XF350", "species": "Powerhead", "category": "Equipment", "count": 2, "date_added": (now - timedelta(days=400)).isoformat()}
    ]
    supabase.table("inhabitants").insert(inhabitants).execute()
    
    ai_summaries = [
        "Nutrient levels extremely high, typical for heavy FOWLR bioloads.",
        "Temperature and pH remain stable despite high nitrates.",
        "Filter maintenance logged successfully this month.",
        "No parameter alarms triggered. System is stable."
    ]
    user_notes = [
        {"summary": "Fed whole silversides and clams. Puffer ate aggressively.", "days_ago": 50},
        {"summary": "Did a 30g water change to try to bring nitrates down a bit.", "days_ago": 25},
        {"summary": "Added a new Flame Angelfish from quarantine.", "days_ago": 14},
        {"summary": "Noticed the Niger Triggerfish chasing the new Flame Angel.", "days_ago": 5}
    ]
    generate_notes(user_id, ai_summaries, user_notes)

# ===============================
# SCENARIO 4: Beginner LPS & Heater Failure
# ===============================
def seed_heater_failure():
    user_id = UUIDS["heater_failure@test.com"]
    print(f"Seeding Beginner LPS (Heater Failure) - {user_id}")
    clear_user_data(user_id)
    
    def anomaly(i, total, params):
        if i >= total - 2: # Last 12 hours
            params["Temperature"] -= 4.0 # Rapid drop of 8 degrees total
        return params
        
    generate_telemetry(user_id, {"pH": 8.1, "Temperature": 78.5, "Alkalinity": 8.7, "Calcium": 430, "Magnesium": 1350, "Nitrate": 15.0, "Phosphate": 0.1}, anomaly_fn=anomaly)
    
    now = datetime.now(timezone.utc)
    inhabitants = [
        {"user_id": user_id, "name": "Royal Gramma", "species": "Gramma loreto", "category": "Fish", "count": 1, "size": "Small", "date_added": (now - timedelta(days=90)).isoformat()},
        {"user_id": user_id, "name": "Banggai Cardinal", "species": "Pterapogon kauderni", "category": "Fish", "count": 1, "size": "Small", "date_added": (now - timedelta(days=80)).isoformat()},
        {"user_id": user_id, "name": "Six Line Wrasse", "species": "Pseudocheilinus hexataenia", "category": "Fish", "count": 1, "size": "Small", "date_added": (now - timedelta(days=60)).isoformat()},
        {"user_id": user_id, "name": "Hammer Coral", "species": "Euphyllia ancora", "category": "Coral", "count": 1, "size": "2 heads", "date_added": (now - timedelta(days=40)).isoformat()},
        {"user_id": user_id, "name": "Torch Coral", "species": "Euphyllia glabrescens", "category": "Coral", "count": 1, "size": "1 head", "date_added": (now - timedelta(days=30)).isoformat()},
        {"user_id": user_id, "name": "Acan Lord", "species": "Micromussa lordhowensis", "category": "Coral", "count": 2, "size": "Frags", "date_added": (now - timedelta(days=20)).isoformat()},
        {"user_id": user_id, "name": "40g Breeder Tank", "species": "Tank", "category": "Equipment", "count": 1, "notes": "No sump. HOB filter only.", "date_added": (now - timedelta(days=120)).isoformat()},
        {"user_id": user_id, "name": "Tidal 55 HOB Filter", "species": "Filter", "category": "Equipment", "count": 1, "date_added": (now - timedelta(days=120)).isoformat()},
        {"user_id": user_id, "name": "Single 300W Glass Heater", "species": "Heater", "category": "Equipment", "count": 1, "notes": "No external controller. Bought used.", "date_added": (now - timedelta(days=80)).isoformat()},
        {"user_id": user_id, "name": "Fluval Sea Marine Nano", "species": "Light", "category": "Equipment", "count": 2, "date_added": (now - timedelta(days=120)).isoformat()},
        {"user_id": user_id, "name": "Jebao SLW-10", "species": "Powerhead", "category": "Equipment", "count": 1, "date_added": (now - timedelta(days=100)).isoformat()}
    ]
    supabase.table("inhabitants").insert(inhabitants).execute()
    
    ai_summaries = [
        "Tank stabilizing. Temperature holding steady at 78.5.",
        "Moderate nutrient levels recorded, good for LPS.",
        "No parameter swings this week. Setup is performing well."
    ]
    user_notes = [
        {"summary": "Bought a used 300W glass heater from a friend and installed it.", "days_ago": 80},
        {"summary": "Added a new hammer coral frag.", "days_ago": 40},
        {"summary": "Changed filter floss in the HOB filter. Torches look fully extended.", "days_ago": 10},
        {"summary": "Water feels really cold to the touch and corals are shriveled. Fish hiding.", "days_ago": 1}
    ]
    generate_notes(user_id, ai_summaries, user_notes)

# ===============================
# SCENARIO 5: Frag Tank Alk Depletion
# ===============================
def seed_frag_tank():
    user_id = UUIDS["alk_depletion@test.com"]
    print(f"Seeding Frag Tank (Alk Depletion) - {user_id}")
    clear_user_data(user_id)
    
    def anomaly(i, total, params):
        if i >= total - 4: # Last 24 hours
            params["Alkalinity"] -= 0.5
            params["Calcium"] -= 10
        return params
        
    generate_telemetry(user_id, {"pH": 8.2, "Temperature": 78.0, "Alkalinity": 9.0, "Calcium": 450, "Magnesium": 1420, "Nitrate": 5.0, "Phosphate": 0.05}, anomaly_fn=anomaly)
    
    now = datetime.now(timezone.utc)
    inhabitants = [
        {"user_id": user_id, "name": "Six Line Wrasse", "species": "Pseudocheilinus hexataenia", "category": "Fish", "count": 1, "size": "Small", "date_added": (now - timedelta(days=200)).isoformat()},
        {"user_id": user_id, "name": "Yellow Coris Wrasse", "species": "Halichoeres chrysus", "category": "Fish", "count": 1, "size": "Medium", "date_added": (now - timedelta(days=180)).isoformat()},
        {"user_id": user_id, "name": "Assorted SPS Frags", "species": "Acropora sp.", "category": "Coral", "count": 150, "size": "Frags", "date_added": (now - timedelta(days=30)).isoformat()},
        {"user_id": user_id, "name": "Montipora Digitata", "species": "Montipora sp.", "category": "Coral", "count": 40, "size": "Frags", "date_added": (now - timedelta(days=60)).isoformat()},
        {"user_id": user_id, "name": "Birdsnest", "species": "Seriatopora hystrix", "category": "Coral", "count": 25, "size": "Frags", "date_added": (now - timedelta(days=45)).isoformat()},
        {"user_id": user_id, "name": "Astrea Snails", "species": "Astrea tecta", "category": "Invertebrate", "count": 30, "size": "Medium", "date_added": (now - timedelta(days=200)).isoformat()},
        {"user_id": user_id, "name": "50g Lowboy Tank", "species": "Tank", "category": "Equipment", "count": 1, "notes": "Bare bottom frag tank. Heavy SPS consumption.", "date_added": (now - timedelta(days=250)).isoformat()},
        {"user_id": user_id, "name": "Geo Calcium Reactor", "species": "Dosing", "category": "Equipment", "count": 1, "notes": "Clogs occasionally.", "date_added": (now - timedelta(days=250)).isoformat()},
        {"user_id": user_id, "name": "Radion XR15 Pro", "species": "Light", "category": "Equipment", "count": 4, "date_added": (now - timedelta(days=250)).isoformat()},
        {"user_id": user_id, "name": "Nero 5", "species": "Powerhead", "category": "Equipment", "count": 2, "date_added": (now - timedelta(days=250)).isoformat()},
        {"user_id": user_id, "name": "Kamoer X1 PRO", "species": "Doser", "category": "Equipment", "count": 1, "notes": "Dosing aminos", "date_added": (now - timedelta(days=150)).isoformat()}
    ]
    supabase.table("inhabitants").insert(inhabitants).execute()
    
    ai_summaries = [
        "Rapid coral growth detected based on historical alk consumption.",
        "Alkalinity demand increasing steadily.",
        "Parameters highly stable. Calcium reactor performing well."
    ]
    user_notes = [
        {"summary": "Cut 20 new frags of Acropora and glued them to plugs. Frag tank running great.", "days_ago": 30},
        {"summary": "Frags are encrusting nicely over the plugs.", "days_ago": 15},
        {"summary": "Increased alk dosing from 5 to 7ml a day to keep up with demand.", "days_ago": 10},
        {"summary": "Noticed CaRx effluent was barely dripping. I think the line is clogged.", "days_ago": 1}
    ]
    generate_notes(user_id, ai_summaries, user_notes)


if __name__ == "__main__":
    print("Beginning Deep Sandbox Seeding Process...")
    seed_nano_mixed_reef()
    seed_sps_reef()
    seed_massive_fowlr()
    seed_heater_failure()
    seed_frag_tank()
    print("Seeding Complete!")
