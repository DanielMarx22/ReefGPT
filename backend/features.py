"""
ReefOS Model - Feature Engineering
Calculates velocity, acceleration, inter-param ratios.
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional

PARAMETERS = ["Alkalinity", "Calcium", "Magnesium", "pH", "Temperature"]

PARAMETER_ALIASES = {
    "alk": "Alkalinity",
    "alkalinity": "Alkalinity",
    "calcium": "Calcium",
    "ca": "Calcium",
    "magnesium": "Magnesium",
    "mg": "Magnesium",
    "ph": "pH",
    "temperature": "Temperature",
    "temp": "Temperature",
    "tds": "Temperature",
}

# ============================================================================
# PHYSICAL/CHEMICAL LIMITS
# ============================================================================
# These are the hard physical limits that CANNOT be exceeded.
# Values outside these ranges are physically impossible.
#
# Hard physical/chemical limits for reef parameters:
# - pH: 0-14 (power of hydrogen scale, 0=acid, 14=base)
# - Temperature: 32-120°F (water freezes at 32°F, boils at 212°F)
# - Calcium: 0-5000 ppm (physically soluble in seawater)
# - Magnesium: 0-5000 ppm (physically soluble)
# - Alkalinity: 0-20 dKH (maximum for stability)

PHYSICAL_LIMITS = {
    "pH": (0.0, 14.0),                  # Power of hydrogen scale (0=acid, 14=base)
    "Temperature": (32.0, 120.0),         # Water freezes at 32°F, boils at 212°F
    "Calcium": (0, 5000),                 # ppm - max ~5000 for seawater solubility
    "Magnesium": (0, 5000),               # ppm - max ~5000 for seawater solubility  
    "Alkalinity": (0, 20.0),              # dKH - above ~20 unstable
    "Salinity": (0, 50),                 # ppt - seawater is ~35 ppt
    "Nitrate": (0, 500),                # ppm - toxic at high levels
    "Phosphate": (0, 10),                # ppm - toxic at high levels
}

# Ideal ranges for healthy reef tanks (target values)
IDEAL_RANGES = {
    "Alkalinity": (7.5, 9.5),
    "Calcium": (400, 450),
    "Magnesium": (1250, 1450),
    "pH": (8.0, 8.4),
    "Temperature": (76, 80),
}

# Critical ranges that indicate potential problems (warning limits)
CRITICAL_RANGES = {
    "Alkalinity": (6.5, 11.0),
    "Calcium": (350, 500),
    "Magnesium": (1100, 1600),
    "pH": (7.6, 8.6),
    "Temperature": (72, 84),
}


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_parameter(param: str, value: float) -> Tuple[bool, Optional[str]]:
    """
    Validate a parameter value against physical limits.
    
    Args:
        param: Parameter name (e.g., "pH", "Calcium")
        value: Value to validate
        
    Returns:
        Tuple of (is_valid, error_message)
        - If valid: (True, None)
        - If invalid: (False, "Error description")
        
    Usage:
        is_valid, error = validate_parameter("pH", 7.8)
        if not is_valid:
            print(error)  # "pH 7.8 is valid"
    """
    physical_min, physical_max = PHYSICAL_LIMITS.get(param, (0, float('inf')))
    
    if value < physical_min:
        return False, f"{param} {value} is below physical minimum ({physical_min}). {param} cannot be less than {physical_min}."
    
    if value > physical_max:
        return False, f"{param} {value} exceeds physical maximum ({physical_max}). {param} cannot be greater than {physical_max}."
    
    return True, None


def validate_all_parameters(values: dict) -> dict:
    """
    Validate a dictionary of parameter values.
    
    Args:
        values: Dict of {parameter: value}
        
    Returns:
        Dict of {parameter: error_message} for invalid params,
        or empty dict if all valid.
        
    Usage:
        errors = validate_all_parameters({"pH": 7.8, "Calcium": 420})
        if errors:
            print(errors)  # {"pH": "..."}
    """
    errors = {}
    for param, value in values.items():
        is_valid, error = validate_parameter(param, value)
        if not is_valid:
            errors[param] = error
    return errors


def normalize_param_name(name: str) -> str:
    """Normalize parameter name to canonical form (case-insensitive)."""
    if not name:
        return None
    normalized = name.strip().lower()
    return PARAMETER_ALIASES.get(normalized, None)


def calculate_velocity(df: pd.DataFrame, param: str) -> pd.Series:
    """Rate of change: dX/dt"""
    if param not in df.columns:
        return pd.Series([np.nan] * len(df))
    values = df[param]
    return values.diff() / 6


def calculate_acceleration(df: pd.DataFrame, param: str) -> pd.Series:
    """Rate of change of velocity"""
    vel = calculate_velocity(df, param)
    return vel.diff() / 6


def calculate_inter_param_ratios(df: pd.DataFrame) -> dict:
    """Key ratios: Alk/Ca, Mg/Ca"""
    ratios = {}
    if "Alkalinity" in df.columns and "Calcium" in df.columns:
        ratios["Alk_Ca_ratio"] = df["Alkalinity"] / (df["Calcium"] / 100)
    if "Magnesium" in df.columns and "Calcium" in df.columns:
        ratios["Mg_Ca_ratio"] = df["Magnesium"] / df["Calcium"]
    return ratios


def calculate_deviation(df: pd.DataFrame) -> dict:
    """Deviation from ideal range"""
    dev = {}
    for param, (ideal_min, ideal_max) in IDEAL_RANGES.items():
        if param not in df.columns:
            continue
        crit_min, crit_max = CRITICAL_RANGES[param]
        norm = (df[param] - (ideal_min + ideal_max) / 2) / (crit_max - crit_min)
        dev[f"{param}_deviation"] = np.clip(norm * 2, -2, 2)
    return dev


def create_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Classify tank state: Stable(0), Warning(1), Critical(2)"""
    result = df.copy()
    warning = np.zeros(len(df), dtype=bool)
    critical = np.zeros(len(df), dtype=bool)
    
    for param in PARAMETERS:
        if param not in df.columns:
            continue
        val = df[param]
        i_min, i_max = IDEAL_RANGES[param]
        c_min, c_max = CRITICAL_RANGES[param]
        warning |= (val < i_min) | (val > i_max)
        critical |= (val < c_min) | (val > c_max)
    
    labels = np.zeros(len(df), dtype=int)
    labels[warning] = 1
    labels[critical] = 2
    result["tank_state"] = labels
    return result


# ============================================================================
# STALENESS TRACKING (Forward-Fill with Decay)
# ============================================================================

class StalenessTracker:
    """
    Tracks data freshness with exponential decay.
    
    This implements "trust but verify":
    - Recent readings are highly trusted (weight = 1.0)
    - Older readings decay in confidence (exponentially)
    - After max_staleness hours, readings are ignored
    
    USAGE:
        tracker = StalenessTracker(max_staleness=72)  # 72 hours = 3 days
        stale_df = tracker.apply_decay(df, timestamps)
        
    The decay formula:
        weight = decay_rate ^ (hours_since_reading)
        
    Example with decay_rate=0.9:
        0 hours ago: weight = 0.9^0 = 1.0
        6 hours ago: weight = 0.9^1 = 0.9
        24 hours ago: weight = 0.9^4 = 0.656
        72 hours ago: weight = 0.9^12 = 0.282
    """
    
    def __init__(
        self, 
        max_staleness: int = 72,  # hours until completely stale
        decay_rate: float = 0.9,   # confidence decay per 6-hour interval
    ):
        self.max_staleness = max_staleness
        self.decay_rate = decay_rate
    
    def calculate_staleness_weights(
        self, 
        df: pd.DataFrame, 
        time_col: str = "timestamp"
    ) -> np.ndarray:
        """
        Calculate weight for each row based on staleness.
        
        Returns array of weights between 0 and 1.
        """
        if time_col not in df.columns:
            # No timestamps - assume recent data
            return np.ones(len(df))
        
        timestamps = pd.to_datetime(df[time_col])
        
        # Calculate hours since each reading
        latest_time = timestamps.max()
        hours_since = (latest_time - timestamps).dt.total_seconds() / 3600
        
        # Calculate decay: rate ^ (hours / interval)
        # decay_rate is for 6-hour intervals
        weights = self.decay_rate ** (hours_since / 6)
        
        # Cap at max staleness
        weights = np.where(hours_since > self.max_staleness, 0, weights)
        
        return weights
    
    def apply_decay(
        self, 
        df: pd.DataFrame, 
        time_col: str = "timestamp"
    ) -> pd.DataFrame:
        """
        Apply forward-fill with decay to handle missing values.
        
        Old values are decayed before being used to fill gaps.
        """
        result = df.copy()
        weights = self.calculate_staleness_weights(df, time_col)
        
        # Forward fill with decay
        for col in df.columns:
            if col == time_col or col not in df.columns:
                continue
                
            # Get values and decay weights
            values = df[col].values
            filled = np.zeros_like(values)
            filled[:] = np.nan
            
            last_valid = np.nan
            last_weight = 1.0
            
            for i in range(len(values)):
                if pd.notna(values[i]):
                    last_valid = values[i]
                    last_weight = weights[i]
                    filled[i] = values[i]
                elif weights[i] > 0.3:  # If not too stale
                    # Decay the old value
                    decayed = last_valid * (weights[i] / last_weight) if last_weight > 0 else last_valid
                    filled[i] = decayed
                # Else leave as NaN (too stale)
            
            result[col] = filled
        
        result['_staleness_weight'] = weights
        return result


# ============================================================================
# INTER-PARAMETER RATIOS (Enhanced)
# ============================================================================

def calculate_inter_param_ratios(df: pd.DataFrame) -> dict:
    """
    Calculate key inter-parameter ratios.
    
    These ratios help identify:
    - Consumption patterns (natural vs failure)
    - Chemical imbalances
    - System stability
    
    Key ratios:
    - Alk/Ca ratio: ~100 ideal (buffer capacity)
    - Mg/Ca ratio: ~3.0 ideal (ion balance)
    
    Returns dict of ratio_name -> value
    """
    ratios = {}
    
    # Alk/Ca ratio: Alkalinity / (Calcium / 100)
    # Normalized to ~100 for ideal tanks
    if "Alkalinity" in df.columns and "Calcium" in df.columns:
        ratios["Alk_Ca_ratio"] = df["Alkalinity"] / (df["Calcium"] / 100)
    
    # Mg/Ca ratio: Magnesium / Calcium
    # ~3.0 for balanced tanks
    if "Magnesium" in df.columns and "Calcium" in df.columns:
        ratios["Mg_Ca_ratio"] = df["Magnesium"] / df["Calcium"]
    
    # pH/Alk relationship: pH stability indicator
    # Low pH + high alk = CO2 issue
    if "pH" in df.columns and "Alkalinity" in df.columns:
        ratios["pH_alk_product"] = df["pH"] * df["Alkalinity"]
    
    return ratios


def calculate_all_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate ALL features for ML model training/inference.
    
    Features include:
    1. Raw parameters (after staleness tracking)
    2. Velocity (dX/dt)
    3. Acceleration (d²X/dt²)
    4. Inter-parameter ratios
    5. Deviation from ideal
    6. Staleness weights
    
    Returns DataFrame with all feature columns.
    """
    result = df.copy()
    
    # Calculate velocity for each parameter
    for param in PARAMETERS:
        if param in df.columns:
            result[f"{param}_velocity"] = calculate_velocity(df, param)
            result[f"{param}_acceleration"] = calculate_acceleration(df, param)
    
    # Calculate inter-parameter ratios
    ratios = calculate_inter_param_ratios(df)
    for ratio_name, ratio_values in ratios.items():
        result[ratio_name] = ratio_values
    
    # Calculate deviation from ideal
    deviations = calculate_deviation(df)
    for col, dev_values in deviations.items():
        result[col] = dev_values
    
    # Add staleness tracking
    tracker = StalenessTracker()
    result = tracker.apply_decay(result)
    
    return result


def create_forecast_labels(df: pd.DataFrame, param: str, horizon: int = 24) -> pd.DataFrame:
    """Target: param value at t+horizon"""
    result = df.copy()
    if param in df.columns:
        result[f"{param}_forecast_target"] = result[param].shift(-horizon)
    return result


class FeatureEngineer:
    def create_all_features(self, df: pd.DataFrame) -> pd.DataFrame:
        result = df.copy()
        for param in PARAMETERS:
            if param in df.columns:
                result[f"{param}_velocity"] = calculate_velocity(df, param)
                result[f"{param}_acceleration"] = calculate_acceleration(df, param)
        
        ratios = calculate_inter_param_ratios(df)
        for k, v in ratios.items():
            result[k] = v
        
        devs = calculate_deviation(df)
        for k, v in devs.items():
            result[k] = v
        
        return result


if __name__ == "__main__":
    from data_loader import generate_synthetic_data
    
    df = generate_synthetic_data(n_days=7)
    fe = FeatureEngineer()
    df_feat = fe.create_all_features(df)
    df_labeled = create_labels(df_feat)
    
    print(f"Generated {len(df)} samples")
    print(f"Features: {len(df_feat.columns)} cols")
    print(f"States: {dict(df_labeled.tank_state.value_counts())}")