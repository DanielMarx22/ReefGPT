import os
import random
import time
from datetime import datetime, timedelta
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.environ.get('SUPABASE_URL', ''), os.environ.get('SUPABASE_KEY', ''))

# Scenarios
SCENARIOS = [
    {
        "email": "perfect@reefgpt.com",
        "password": "password123",
        "name": "Perfect Tank",
        "livestock": "Mixed Reef (SPS dominant). Established 3 years.",
        "logic": lambda hrs_ago: {
            "pH": 8.1 + 0.1 * __import__("math").sin(hrs_ago / 24 * 3.14 * 2), # Daily swing
            "Alkalinity": 8.5 + random.uniform(-0.1, 0.1),
            "Calcium": 440 + random.uniform(-5, 5),
            "Magnesium": 1350 + random.uniform(-10, 10),
            "Temperature": 78.0 + 0.5 * __import__("math").sin(hrs_ago / 24 * 3.14 * 2)
        }
    },
    {
        "email": "crash@reefgpt.com",
        "password": "password123",
        "name": "Crashing Tank",
        "livestock": "New SPS frags, a few LPS. Dosing pump broke 3 days ago.",
        "logic": lambda hrs_ago: {
            "pH": 7.8 - max(0, (72 - hrs_ago) * 0.005) + random.uniform(-0.05, 0.05), # Drops after day 3
            "Alkalinity": 7.0 - max(0, (72 - hrs_ago) * 0.02) + random.uniform(-0.1, 0.1), # Dropping fast
            "Calcium": 380 - max(0, (72 - hrs_ago) * 0.5) + random.uniform(-5, 5),
            "Magnesium": 1200 + random.uniform(-10, 10),
            "Temperature": 78.0
        }
    },
    {
        "email": "lowcalc@reefgpt.com",
        "password": "password123",
        "name": "Low Calcium",
        "livestock": "Heavy SPS load. Fast growth.",
        "logic": lambda hrs_ago: {
            "pH": 8.2,
            "Alkalinity": 9.0,
            "Calcium": max(300, 400 - (336 - hrs_ago) * 0.3) + random.uniform(-2, 2), # Dropping steadily
            "Magnesium": 1400,
            "Temperature": 77.5
        }
    },
    {
        "email": "hot@reefgpt.com",
        "password": "password123",
        "name": "Temp Spike",
        "livestock": "Fish only with live rock.",
        "logic": lambda hrs_ago: {
            "pH": 8.0,
            "Alkalinity": 8.0,
            "Calcium": 400,
            "Magnesium": 1300,
            "Temperature": 78.0 if hrs_ago > 48 else min(85.0, 78.0 + (48 - hrs_ago) * 0.2) + random.uniform(-0.2, 0.2)
        }
    },
    {
        "email": "swing@reefgpt.com",
        "password": "password123",
        "name": "pH Swings",
        "livestock": "Heavy fish bioload, no refugium, windows closed.",
        "logic": lambda hrs_ago: {
            "pH": 7.9 + 0.5 * __import__("math").sin(hrs_ago / 24 * 3.14 * 2) + random.uniform(-0.1, 0.1), # Massive 1.0 swing
            "Alkalinity": 8.5,
            "Calcium": 420,
            "Magnesium": 1300,
            "Temperature": 78.0
        }
    }
]

def main():
    print("Starting seed process...")
    for s in SCENARIOS:
        print(f"\\n--- Creating Account: {s['email']} ---")
        try:
            # Attempt to sign in first
            res = None
            try:
                res = supabase.auth.sign_in_with_password({
                    "email": s['email'],
                    "password": s['password']
                })
            except Exception:
                pass
            
            if not res or not res.user:
                # Sign up if doesn't exist
                res = supabase.auth.sign_up({
                    "email": s['email'],
                    "password": s['password']
                })
                
            if not res or not res.user:
                print(f"Skipping {s['email']} (email confirmation required or unknown error).")
                continue
            
            user_id = res.user.id
            print(f"Created/Logged in user {user_id}")
            
            # Wipe existing data for this user
            supabase.table('metrics_log').delete().eq('user_id', user_id).execute()
            supabase.table('tank_settings').delete().eq('user_id', user_id).execute()
            
            # Insert tank settings
            supabase.table('tank_settings').insert({
                "user_id": user_id,
                "livestock": s['livestock'],
                "dashboard_layout": {"graphs": [], "telemetry": []}
            }).execute()
            
            # Generate 2 weeks of hourly data (336 hours)
            metrics_to_insert = []
            now = datetime.utcnow()
            for hrs_ago in range(336, -1, -1):
                dt = now - timedelta(hours=hrs_ago)
                vals = s['logic'](hrs_ago)
                for param, val in vals.items():
                    metrics_to_insert.append({
                        "user_id": user_id,
                        "parameter": param,
                        "value": round(val, 2),
                        "timestamp": dt.isoformat()
                    })
            
            # Insert in chunks of 500
            for i in range(0, len(metrics_to_insert), 500):
                supabase.table('metrics_log').insert(metrics_to_insert[i:i+500]).execute()
                
            print(f"Inserted {len(metrics_to_insert)} records for {s['name']}.")
            
        except Exception as e:
            print(f"Error processing {s['email']}: {e}")
            
    print("\\nSeed process complete!")

if __name__ == "__main__":
    main()
