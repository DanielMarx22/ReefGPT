"""
ReefOS Model - Feature Engineering
Calculates velocity, acceleration, inter-param ratios.
"""

import numpy as np
import pandas as pd

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

IDEAL_RANGES = {
    "Alkalinity": (7.5, 9.5),
    "Calcium": (400, 450),
    "Magnesium": (1250, 1450),
    "pH": (8.0, 8.4),
    "Temperature": (76, 80),
}

CRITICAL_RANGES = {
    "Alkalinity": (6.5, 11.0),
    "Calcium": (350, 500),
    "Magnesium": (1100, 1600),
    "pH": (7.6, 8.6),
    "Temperature": (72, 84),
}


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