"""
Synthetic Reef Data Generator & Database Seeder
Generates 90 days of realistic, sparse reef parameter data and uploads to Supabase.
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

def generate_sparse_reef_data(days=90):
    print(f"Generating {days} days of synthetic data...")
    
    # End date: April 17, 2026
    end_date = pd.to_datetime("2026-04-17 12:00:00")
    dates = pd.date_range(end=end_date, periods=days, freq='D')
    
    df = pd.DataFrame({'timestamp': dates})
    
    # 1. Generate Realistic Baselines with slight daily noise
    np.random.seed(42) # Ensures reproducibility
    df['Alkalinity'] = np.random.normal(8.5, 0.15, days)
    df['Calcium'] = np.random.normal(440, 8, days)
    df['Magnesium'] = np.random.normal(1350, 15, days)
    df['pH'] = np.random.normal(8.1, 0.05, days)
    df['Temperature'] = np.random.normal(78.0, 0.4, days)
    df['Nitrate'] = np.random.normal(5.0, 0.5, days)
    df['Phosphate'] = np.random.normal(0.05, 0.01, days)
    
    # 2. Apply Missing Data Masks
    
    # Alk, Ca, Mg: Miss roughly 1 in 10 days
    for col in ['Alkalinity', 'Calcium', 'Magnesium']:
        mask = np.random.rand(days) < 0.10
        df.loc[mask, col] = np.nan
        
    # pH, Temp: Miss roughly 2 days a week (28% of the time)
    for col in ['pH', 'Temperature']:
        mask = np.random.rand(days) < 0.28
        df.loc[mask, col] = np.nan
        
    # Nitrate, Phosphate: Tested exactly once a week
    weekly_mask = np.ones(days, dtype=bool)
    weekly_mask[::7] = False # Keep only every 7th day
    df.loc[weekly_mask, 'Nitrate'] = np.nan
    df.loc[weekly_mask, 'Phosphate'] = np.nan
    
    # Round the values for cleaner display
    for col in df.columns:
        if col != 'timestamp':
            df[col] = df[col].round(2)
            
    return df

def seed_database():
    df = generate_sparse_reef_data(days=90)
    
    # Save to CSV
    csv_path = "test_data.csv"
    df.to_csv(csv_path, index=False)
    print(f"Saved wide-format data to {csv_path}")
    
    # Melt to Long Format for the database
    df_long = pd.melt(
        df, 
        id_vars=["timestamp"], 
        var_name="parameter", 
        value_name="value"
    )
    
    # Drop the NaNs so they don't upload to the database
    # (The AI will calculate the missing gaps via features.py)
    df_long = df_long.dropna(subset=["value"])
    
    print("Clearing old database logs...")
    supabase.table("metrics_log").delete().eq("user_id", TEMP_USER_ID).execute()
    
    print(f"Uploading {len(df_long)} valid records to Supabase...")
    
    batch_size = 100
    records = df_long.to_dict("records")
    
    # Convert timestamps to string format for JSON serialization
    for row in records:
        row["timestamp"] = str(row["timestamp"])
        row["user_id"] = TEMP_USER_ID
    
    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        supabase.table("metrics_log").insert(batch).execute()
        
    print("Seeding complete! Refresh your React frontend to see the updated metrics.")

if __name__ == "__main__":
    seed_database()