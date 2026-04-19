"""
Advanced Synthetic Reef Data Generator & Database Seeder (CS 551 Edition)
Generates 13,000+ rows of high-frequency IoT data mixed with human-error manual testing.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Connect to Supabase
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)
TEMP_USER_ID = "00000000-0000-0000-0000-000000000000"

def generate_complex_reef_data(days=90):
    print(f"Generating {days} days of 10-minute IoT data...")
    
    # End date: April 17, 2026. 10-minute frequency = 144 readings/day
    end_date = pd.to_datetime("2026-04-19 12:00:00")
    timestamps = pd.date_range(end=end_date, periods=days * 24 * 6, freq='10min')
    df = pd.DataFrame({'timestamp': timestamps})
    
    # Time variable for continuous functions
    days_elapsed = (df['timestamp'] - df['timestamp'].min()).dt.total_seconds() / 86400.0
    hour_of_day = df['timestamp'].dt.hour + df['timestamp'].dt.minute / 60.0

    # 1. Base Chemistry (The hidden "true" state of the tank)
    np.random.seed(42)
    
    # Alk slowly wanders over the 90 days
    true_alk = 8.5 + np.sin(days_elapsed * 0.1) * 0.6 + np.random.normal(0, 0.05, len(df))
    df['Alkalinity'] = true_alk
    df['Calcium'] = 420 + (true_alk - 8.5) * 20 + np.random.normal(0, 5, len(df))
    df['Magnesium'] = 1350 + np.random.normal(0, 10, len(df))
    
    # 2. Diurnal pH Cycle (Tied to light cycle AND Alkalinity)
    # Trough at 6 AM (lights off), Peak at 6 PM (lights on)
    diurnal_swing = np.sin((hour_of_day - 12) * (np.pi / 12)) * 0.15 
    alk_influence = (true_alk - 8.5) * 0.08 # Higher Alk = slightly higher baseline pH
    df['pH'] = 8.1 + diurnal_swing + alk_influence + np.random.normal(0, 0.01, len(df))
    
    # Temperature (Heater cycles)
    df['Temperature'] = 78.0 + np.sin(hour_of_day * np.pi) * 0.3 + np.random.normal(0, 0.1, len(df))
    
    # 3. Apply the Sampling Masks (Converting "True" state to "Observed" state)
    
    # IoT Probes (pH, Temp): Logged every 10 minutes. 1% random sensor drop.
    df.loc[np.random.rand(len(df)) < 0.01, ['pH', 'Temperature']] = np.nan
    
    # Manual Tests (Alk, Ca, Mg): Erase all data EXCEPT specific testing times
    is_alk_time = (df['timestamp'].dt.hour.isin([8, 20])) & (df['timestamp'].dt.minute == 0) # 8 AM & 8 PM
    is_camg_time = (df['timestamp'].dt.hour == 20) & (df['timestamp'].dt.minute == 0) # 8 PM only
    
    df.loc[~is_alk_time, 'Alkalinity'] = np.nan
    df.loc[~is_camg_time, ['Calcium', 'Magnesium']] = np.nan
    
    # 4. Human Error Simulation: "Forgot to buy reagents"
    # Create 3 distinct periods where manual testing stops for 1-3 days
    outage_start_days = np.random.choice(range(10, 80), size=3, replace=False)
    for start_day in outage_start_days:
        outage_length = np.random.randint(1, 4) # 1 to 3 days missing
        start_idx = start_day * 144
        end_idx = start_idx + (outage_length * 144)
        df.loc[start_idx:end_idx, ['Alkalinity', 'Calcium', 'Magnesium']] = np.nan

    # Final 1% random drop for human forgetfulness on normal days
    df.loc[np.random.rand(len(df)) < 0.01, ['Alkalinity', 'Calcium', 'Magnesium']] = np.nan

    # Clean up formatting
    for col in ['Alkalinity', 'pH']:
        df[col] = df[col].round(3)
    for col in ['Calcium', 'Magnesium', 'Temperature']:
        df[col] = df[col].round(1)

    return df

def seed_database():
    df = generate_complex_reef_data(days=90)
    
    # Melt to Long Format for the database
    df_long = pd.melt(
        df, 
        id_vars=["timestamp"], 
        var_name="parameter", 
        value_name="value"
    )
    
    # Drop the NaNs to create the sparse IoT dataset
    df_long = df_long.dropna(subset=["value"])
    
    print(f"Dataset generated: {len(df_long)} valid measurements.")
    
    # Save a local copy for ML Training
    df_long.to_csv("test_data.csv", index=False)
    
    print("Clearing old database logs...")
    supabase.table("metrics_log").delete().eq("user_id", TEMP_USER_ID).execute()
    
    print(f"Uploading to Supabase in batches...")
    
    batch_size = 500 # Larger batches for 20k+ rows
    records = df_long.to_dict("records")
    
    for row in records:
        row["timestamp"] = str(row["timestamp"])
        row["user_id"] = TEMP_USER_ID
    
    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        supabase.table("metrics_log").insert(batch).execute()
        if i % 5000 == 0 and i > 0:
            print(f"Uploaded {i} records...")
            
    print("Database seeding complete! You are ready for CS 551.")

if __name__ == "__main__":
    seed_database()