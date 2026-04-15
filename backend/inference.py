"""
ReefOS Model - Unified Inference
Predicts tank state and generates recommendations.
"""

import numpy as np
import pandas as pd
from typing import Dict
from datetime import datetime

from data_loader import generate_synthetic_data, PARAMETERS
from features import FeatureEngineer, create_labels, calculate_velocity, IDEAL_RANGES, CRITICAL_RANGES, normalize_param_name
import numpy as np


class ReefTankPredictor:
    def __init__(self, user_id: str = None):
        self.user_id = user_id or "00000000-0000-0000-0000-000000000000"
        self.feature_engineer = FeatureEngineer()
        self.is_trained = False
        self.data_source = None
    
    def load_data(self, source: str = "auto") -> pd.DataFrame:
        """Load tank data from various sources."""
        self.data_source = source
        
        df = pd.DataFrame()
        
        if source == "csv":
            try:
                df = pd.read_csv("test_data.csv")
                self.data_source = "csv"
            except FileNotFoundError:
                df = pd.DataFrame(columns=["timestamp", "Alkalinity", "Calcium", "Magnesium", "pH", "Temperature"])
        
        elif source == "supabase":
            try:
                from main import supabase
                response = supabase.table("metrics_log").select("*").order("timestamp", desc=False).execute()
                if response.data and len(response.data) > 0:
                    df = pd.DataFrame(response.data)
                    df["timestamp"] = pd.to_datetime(df["timestamp"])
                    
                    if "parameter" in df.columns and "value" in df.columns:
                        # Normalize parameter names
                        df["parameter"] = df["parameter"].apply(
                            lambda x: normalize_param_name(str(x)) if pd.notna(x) else x
                        )
                        df = df[df["parameter"].notna()]
                        
                        if len(df) > 0:
                            # Pivot and forward-fill to get all params in each row
                            df = df.pivot(index="timestamp", columns="parameter", values="value").reset_index()
                            df = df.ffill()  # Forward fill gaps
                            df = df.bfill()  # Backward fill any leading NaNs
                            self.data_source = "supabase"
                        else:
                            df = pd.DataFrame(columns=["timestamp", "Alkalinity", "Calcium", "Magnesium", "pH", "Temperature"])
                    else:
                        df = pd.DataFrame(columns=["timestamp", "Alkalinity", "Calcium", "Magnesium", "pH", "Temperature"])
                else:
                    df = pd.DataFrame(columns=["timestamp", "Alkalinity", "Calcium", "Magnesium", "pH", "Temperature"])
            except Exception as e:
                print(f"Supabase error: {e}")
                df = pd.DataFrame(columns=["timestamp", "Alkalinity", "Calcium", "Magnesium", "pH", "Temperature"])
        
        else:  # synthetic or default
            df = generate_synthetic_data(n_days=30)
            self.data_source = "synthetic"
        
        self._cached_data = df
        return df
    
    def get_cached_data(self) -> pd.DataFrame:
        """Get previously loaded data without reloading."""
        if hasattr(self, '_cached_data') and len(self._cached_data) > 0:
            return self._cached_data
        return self.load_data(self.data_source or "synthetic")
    
    def train(self, n_days: int = 30) -> Dict:
        """Train on synthetic data with various failure modes."""
        dfs = []
        for mode in [None, "heater_malfunction", "dosing_pump_clog", 
                    "calcifier_depletion", "magnesium_spike"]:
            df = generate_synthetic_data(n_days=n_days//5, failure_mode=mode)
            dfs.append(df)
        
        self.training_data = pd.concat(dfs, ignore_index=True)
        self.is_trained = True
        return {"status": "trained", "n_samples": len(self.training_data), "source": self.data_source}
    
    def predict_current_state(self) -> Dict:
        """Predict tank state from rule-based system."""
        if not self.is_trained:
            self.train()
        
        df = self.get_cached_data()
        fe = FeatureEngineer()
        df_feat = fe.create_all_features(df)
        
        latest = df_feat.iloc[-1]
        warnings = []
        
        for param in PARAMETERS:
            if param not in latest.index:
                continue
            val = latest.get(param)
            if pd.isna(val):
                continue
            
            i_min, i_max = IDEAL_RANGES.get(param, (7, 9))
            c_min, c_max = CRITICAL_RANGES.get(param, (6, 11))
            
            if val < c_min or val > c_max:
                warnings.append(param)
            elif val < i_min or val > i_max:
                warnings.append(param)
        
        if not warnings:
            return {"state_id": 0, "state_name": "Stable", "confidence": 0.9, "warning_parameters": []}
        elif len(warnings) <= 2:
            return {"state_id": 1, "state_name": "Warning", "confidence": 0.7, "warning_parameters": warnings}
        else:
            return {"state_id": 2, "state_name": "Critical", "confidence": 0.8, "warning_parameters": warnings}
    
    def get_full_analysis(self) -> Dict:
        """Complete analysis with recommendations."""
        state = self.predict_current_state()
        forecast = self._get_forecast()
        
        recommendations = []
        param_recs = []
        
        for param, fc in forecast.items():
            if fc["trend"] == "critical":
                if param == "Alkalinity":
                    param_recs.append("Dosing pump may be clogged - check alkalinity additive")
                elif param == "Calcium":
                    param_recs.append("Calcium reactor needs attention")
                elif param == "Magnesium":
                    param_recs.append("Check magnesium dosage")
                elif param == "Temperature":
                    param_recs.append("Heater/chiller malfunction - check equipment")
                elif param == "pH":
                    param_recs.append("Check CO2 regulator - pH swing detected")
            elif fc["trend"] == "warning":
                if param == "Temperature":
                    param_recs.append("Monitor temperature closely")
                elif param == "pH":
                    param_recs.append("Check water flow - possible pH drift")
        
        if param_recs:
            recommendations.extend(param_recs)
        elif state["state_id"] == 1:
            recommendations.extend([
                "Test water parameters manually",
                "Check dosing pump operation",
            ])
        elif state["state_id"] == 2:
            recommendations.extend([
                "IMMEDIATE water change (25%)",
                "Test all parameters",
                "Check all equipment",
            ])
        
        return {
            "timestamp": datetime.now().isoformat(),
            "source": self.data_source,
            "source_info": self._get_source_info(),
            "current_state": state,
            "current_values": self._get_latest_values(),
            "forecast_24h": self._get_forecast(),
            "data_points": len(self.load_data()) if self.data_source != "supabase" else "from_db",
            "recommendations": recommendations,
            "model_version": "1.0.0",
        }
    
    def _get_source_info(self) -> Dict:
        """Get info about the data source"""
        if self.data_source == "csv":
            return {"type": "csv", "file": "test_data.csv", "description": "Load from test_data.csv file"}
        elif self.data_source == "supabase":
            return {"type": "supabase", "description": "Load from Supabase database"}
        else:
            return {"type": "synthetic", "description": "Generated random data"}
    
    def _get_latest_values(self) -> Dict:
        """Get current parameter readings."""
        df = self.get_cached_data()
        latest = df.iloc[-1]
        return {p: round(float(latest[p]), 2) for p in PARAMETERS if p in latest.index and pd.notna(latest.get(p))}
    
    def _get_forecast(self) -> Dict:
        """Predict values in 24 hours using velocity extrapolation."""
        df = self.get_cached_data()
        
        if df.empty or len(df) < 2:
            return {}
        
        latest = df.iloc[-1]
        
        forecasts = {}
        for param in PARAMETERS:
            if param not in df.columns:
                continue
            
            current = float(latest[param])
            velocity = calculate_velocity(df, param).iloc[-1]
            
            if pd.isna(velocity):
                velocity = 0
            if pd.isna(current):
                continue
            
            predicted_24h = float(current + (velocity * 4))
            
            deviation = abs(predicted_24h - ((IDEAL_RANGES[param][0] + IDEAL_RANGES[param][1]) / 2))
            ideal_width = (IDEAL_RANGES[param][1] - IDEAL_RANGES[param][0]) / 2
            
            trend = "stable"
            if deviation > ideal_width * 0.5:
                trend = "warning" if deviation <= ideal_width else "critical"
            
            forecasts[param] = {
                "current": round(current, 2),
                "predicted_24h": round(predicted_24h, 2),
                "velocity": round(float(velocity), 4),
                "trend": trend,
            }
        
        return forecasts


def create_predictor(user_id: str = None) -> ReefTankPredictor:
    predictor = ReefTankPredictor(user_id)
    predictor.train()
    return predictor


if __name__ == "__main__":
    p = create_predictor()
    print(p.get_full_analysis())