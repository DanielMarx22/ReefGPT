"""
ReefOS Model - Synthetic Data Generator
Generates training data for failure modes.
"""

from datetime import datetime, timedelta
import numpy as np
import pandas as pd

PARAMETERS = ["Alkalinity", "Calcium", "Magnesium", "pH", "Temperature"]


def generate_synthetic_data(
    n_days: int = 30,
    sample_interval_hours: int = 6,
    failure_mode: str = None,
) -> pd.DataFrame:
    """
    Generate synthetic reef tank data for training.
    """
    # Use time-based seed for variety
    np.random.seed(None)
    
    n_samples = n_days * 24 // sample_interval_hours
    timestamps = pd.date_range(
        start=datetime.now() - timedelta(days=n_days),
        periods=n_samples,
        freq=f"{sample_interval_hours}h",
    )
    
    data = {
        "timestamp": timestamps,
        "Alkalinity": np.random.normal(8.5, 0.5, n_samples),
        "Calcium": np.random.normal(420, 20, n_samples),
        "Magnesium": np.random.normal(1350, 50, n_samples),
        "pH": np.random.normal(8.2, 0.1, n_samples),
        "Temperature": np.random.normal(78, 1, n_samples),
    }
    
    for i in range(1, n_samples):
        data["Alkalinity"][i] += data["Alkalinity"][i-1] * 0.05
        data["Calcium"][i] += data["Calcium"][i-1] * 0.03
        data["Magnesium"][i] += data["Magnesium"][i-1] * 0.02
        data["pH"][i] += np.random.randn() * 0.02
        data["Temperature"][i] += np.random.randn() * 0.1
    
    for param, min_val, max_val in [
        ("Alkalinity", 7.0, 12.0),
        ("Calcium", 380, 500),
        ("Magnesium", 1200, 1500),
        ("pH", 7.8, 8.5),
        ("Temperature", 74, 82),
    ]:
        data[param] = np.clip(data[param], min_val, max_val)
    
    if failure_mode == "heater_malfunction":
        fail_idx = n_samples // 2
        for i in range(fail_idx, n_samples):
            data["Temperature"][i] += np.random.normal(-3, 0.5)
    
    elif failure_mode == "dosing_pump_clog":
        fail_idx = n_samples // 2
        for i in range(fail_idx, n_samples):
            data["Alkalinity"][i] -= np.random.uniform(0.2, 0.5)
    
    elif failure_mode == "calcifier_depletion":
        fail_idx = n_samples // 2
        for i in range(fail_idx, n_samples):
            data["Calcium"][i] -= np.random.uniform(1, 3)
            data["pH"][i] -= np.random.uniform(0.05, 0.1)
    
    elif failure_mode == "magnesium_spike":
        fail_idx = n_samples // 2
        for i in range(fail_idx, n_samples):
            data["Magnesium"][i] += np.random.uniform(20, 50)
    
    return pd.DataFrame(data)


if __name__ == "__main__":
    df = generate_synthetic_data(n_days=7)
    print(f"Generated {len(df)} samples")
    print(df.tail())