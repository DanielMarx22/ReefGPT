"""
ReefOS Model - Feature Engineering
Calculates velocity, acceleration, and handles missing data with LOCF Decay.
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional

PARAMETERS = ["Alkalinity", "Calcium", "Magnesium", "pH", "Temperature"]

PARAMETER_ALIASES = {
    "alk": "Alkalinity", "alkalinity": "Alkalinity",
    "calcium": "Calcium", "ca": "Calcium",
    "magnesium": "Magnesium", "mg": "Magnesium",
    "ph": "pH", "temperature": "Temperature",
    "temp": "Temperature", "tds": "Temperature",
}

IDEAL_RANGES = {
    "Alkalinity": (7.5, 9.5),
    "Calcium": (400, 450),
    "Magnesium": (1250, 1450),
    "pH": (8.0, 8.4),
    "Temperature": (76, 80),
}

PHYSICAL_LIMITS = {
    "pH": (0.0, 14.0),
    "Temperature": (32.0, 120.0),
    "Calcium": (0, 5000),
    "Magnesium": (0, 5000),
    "Alkalinity": (0, 20.0),
}

def normalize_param_name(name: str) -> str:
    if not name: return None
    return PARAMETER_ALIASES.get(name.strip().lower(), None)

def validate_parameter(param: str, value: float) -> Tuple[bool, Optional[str]]:
    # Testing mode: We keep this simple to allow any custom entry 
    # but still check the big physical ones.
    p_min, p_max = PHYSICAL_LIMITS.get(param, (0, 9999))
    if value < p_min or value > p_max:
        return False, f"{param} {value} is physically impossible."
    return True, None

class FeatureEngineer:
    def __init__(self, max_staleness_hours: int = 168):
        self.max_staleness = max_staleness_hours

    def create_all_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        The Core Math Engine.
        1. Applies LOCF (Last Observation Carried Forward)
        2. Applies Time-Decay (Masks data older than 7 days)
        3. Calculates Velocity (dX/dt)
        """
        if df.empty:
            return df
            
        result = df.copy()
        
        # Ensure we are working with a time-series
        if "timestamp" in result.columns:
            result["timestamp"] = pd.to_datetime(result["timestamp"])
            result = result.sort_values("timestamp")

        for param in PARAMETERS:
            if param not in result.columns:
                continue

            # --- STEP 1: MISSING DATA LOGIC (LOCF + DECAY) ---
            # Track when the actual reading happened
            is_measured = result[param].notna()
            last_measured_time = result["timestamp"].where(is_measured).ffill()
            
            # Calculate how 'stale' the data is in hours
            hours_since = (result["timestamp"] - last_measured_time).dt.total_seconds() / 3600
            
            # Fill forward the last known value
            result[param] = result[param].ffill()
            
            # MASKING: If data is older than our limit (7 days), we force it to NaN
            # This prevents the AI from trusting 'ghost' data.
            result.loc[hours_since > self.max_staleness, param] = np.nan

            # --- STEP 2: CALCULATE VELOCITY ---
            # Velocity = (Change in Value) / (Change in Time in Hours)
            time_diff_hours = result["timestamp"].diff().dt.total_seconds() / 3600
            result[f"{param}_velocity"] = result[param].diff() / time_diff_hours
            
        return result

# Helper for the ML model to label states
def create_labels(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    labels = np.zeros(len(df), dtype=int) # 0 = Stable
    
    for param, (i_min, i_max) in IDEAL_RANGES.items():
        if param in df.columns:
            val = df[param]
            # 1 = Warning (Out of ideal range)
            labels[(val < i_min) | (val > i_max)] = 1
            
    result["tank_state"] = labels
    return result