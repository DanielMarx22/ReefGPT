"""
ReefOS Model - Synthetic Data Generator
===================================
Generates synthetic reef tank data for training and testing ML models.

This creates realistic reef aquarium water chemistry data including:
- Normal operating conditions (stable parameters)
- Common failure modes (heater malfunction, dosing pump clog, etc.)
- Realistic correlations between parameters (e.g., calcium/alkalinity relationship)

Usage:
    from data_loader import generate_synthetic_data
    
    # Generate 30 days of normal data
    df = generate_synthetic_data(n_days=30)
    
    # Generate 30 days with a specific failure mode
    df = generate_synthetic_data(n_days=30, failure_mode='heater_malfunction')

Failure Modes:
    - None: Normal operation
    - heater_malfunction: Temperature drops or spikes
    - dosing_pump_clog: Alkalinity/Calcium dropping
    - calcifier_depletion: Calcium depleting while alk stable
    - magnesium_spike: Magnesium elevated
"""

from datetime import datetime, timedelta
import numpy as np
import pandas as pd

# The 5 core parameters for reef tank water chemistry
# These are what we measure and predict
PARAMETERS = ["Alkalinity", "Calcium", "Magnesium", "pH", "Temperature"]


def generate_synthetic_data(
    n_days: int = 30,
    sample_interval_hours: int = 6,
    failure_mode: str = None,
) -> pd.DataFrame:
    """
    Generate synthetic reef tank data for training.
    
    Creates realistic time-series data with:
    - Correlated parameters (alk/calcium, mg/calcium)
    - Random noise and drift
    - Optional failure mode injection
    
    Args:
        n_days: Number of days of data to generate
        sample_interval_hours: Hours between samples (6 = 4x/day)
        failure_mode: Optional failure mode to inject
        
    Returns:
        DataFrame with columns: timestamp, Alkalinity, Calcium, Magnesium, pH, Temperature
        
    Example:
        >>> df = generate_synthetic_data(n_days=7)
        >>> print(df.head())
           timestamp  Alkalinity  Calcium  Magnesium   pH  Temperature
        0 2024-...      8.2      420        1350  8.1         78.1
        1 2024-...      8.4      425        1345  8.2         78.3
    """
    # Use time-based seed for variety (different data each run)
    np.random.seed(None)
    
    # Calculate number of samples: n_days * 24h / interval
    n_samples = n_days * 24 // sample_interval_hours
    
    # Generate timestamps spanning n_days into the past
    timestamps = pd.date_range(
        start=datetime.now() - timedelta(days=n_days),
        periods=n_samples,
        freq=f"{sample_interval_hours}h",
    )
    
    # =========================================================================
    # GENERATE BASE DATA WITH NORMAL PARAMETERS
    # =========================================================================
    # Generate values with realistic distributions:
    # - Alkalinity: ~8.5 dKH (ideal is 8-9)
    # - Calcium: ~420 ppm (ideal is 400-450)
    # - Magnesium: ~1350 ppm (ideal is 1300-1400)
    # - pH: ~8.2 (ideal is 8.1-8.3)
    # - Temperature: ~78°F (ideal is 76-80)
    
    data = {
        "timestamp": timestamps,
        "Alkalinity": np.random.normal(8.5, 0.5, n_samples),
        "Calcium": np.random.normal(420, 20, n_samples),
        "Magnesium": np.random.normal(1350, 50, n_samples),
        "pH": np.random.normal(8.2, 0.1, n_samples),
        "Temperature": np.random.normal(78, 1, n_samples),
    }
    
    # =========================================================================
    # ADD CORRELATIONS (realistic chemistry relationships)
    # =========================================================================
    # In real tanks, parameters are correlated:
    # - Higher calcium → slightly lower pH (carbon chemistry)
    # - Sequential samples are correlated (not random)
    
    for i in range(1, n_samples):
        # Add drift from previous value ( tanks aren't random)
        data["Alkalinity"][i] += data["Alkalinity"][i-1] * 0.05
        data["Calcium"][i] += data["Calcium"][i-1] * 0.03
        data["Magnesium"][i] += data["Magnesium"][i-1] * 0.02
        data["pH"][i] += np.random.randn() * 0.02
        data["Temperature"][i] += np.random.randn() * 0.1
    
    # =========================================================================
    # CLAMP TO REALISTIC RANGES
    # =========================================================================
    # Ensure values are within reasonable bounds
    for param, min_val, max_val in [
        ("Alkalinity", 7.0, 12.0),
        ("Calcium", 380, 500),
        ("Magnesium", 1200, 1500),
        ("pH", 7.8, 8.5),
        ("Temperature", 74, 82),
    ]:
        data[param] = np.clip(data[param], min_val, max_val)
    
    # =========================================================================
    # INJECT FAILURE MODE (if specified)
    # =========================================================================
    if failure_mode:
        data = _inject_failure_mode(data, failure_mode)
    
    return pd.DataFrame(data)


def _inject_failure_mode(data: dict, mode: str) -> dict:
    """
    Inject a specific failure mode into the data.
    
    Common reef tank failures and their signatures:
    
    Args:
        data: Dictionary of parameter arrays
        mode: Failure mode name
        
    Returns:
        Modified data dictionary with failure injected
    """
    n = len(data["Alkalinity"])
    
    if mode == "heater_malfunction":
        # Temperature drops suddenly, stays low
        drop_point = n // 3
        for i in range(drop_point, n):
            data["Temperature"][i] -= np.random.uniform(2, 5)
    
    elif mode == "dosing_pump_clog":
        # Alkalinity drops while calcium stays
        drop_point = n // 2
        for i in range(drop_point, n):
            data["Alkalinity"][i] -= np.random.uniform(0.5, 1.5)
    
    elif mode == "calcifier_depletion":
        # Calcium drops (coral consuming), alk stable
        drop_point = n // 2
        for i in range(drop_point, n):
            data["Calcium"][i] -= np.random.uniform(1, 3)
    
    elif mode == "magnesium_spike":
        # Magnesium spikes (overdosing)
        spike_point = n // 2
        for i in range(spike_point, n):
            data["Magnesium"][i] += np.random.uniform(50, 150)
    
    # Re-clamp after failure injection
    for param in PARAMETERS:
        if param == "Alkalinity":
            data[param] = np.clip(data[param], 6.0, 12.0)
        elif param == "Calcium":
            data[param] = np.clip(data[param], 350, 550)
        elif param == "Magnesium":
            data[param] = np.clip(data[param], 1100, 1700)
        elif param == "pH":
            data[param] = np.clip(data[param], 7.6, 8.6)
        elif param == "Temperature":
            data[param] = np.clip(data[param], 70, 86)
    
    return data


if __name__ == "__main__":
    # Example usage
    print("Generating normal data...")
    df = generate_synthetic_data(n_days=7)
    print(df.describe())
    
    print("\nGenerating heater malfunction data...")
    df_fail = generate_synthetic_data(n_days=7, failure_mode="heater_malfunction")
    print(f"Temperature range: {df_fail['Temperature'].min():.1f} - {df_fail['Temperature'].max():.1f}")