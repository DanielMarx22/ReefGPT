import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

PARAMETERS = ["Alkalinity", "Calcium", "Magnesium", "pH", "Temperature"]

IDEAL_RANGES = {
    "Alkalinity": (7.5, 9.5),
    "Calcium": (400, 450),
    "Magnesium": (1250, 1450),
    "pH": (8.0, 8.4),
    "Temperature": (76, 80),
}

ACTION_CONFIG = {
    "Stable": {
        "alert_level": "info",
        "actions": [
            "Continue regular monitoring schedule",
            "Check dosing reservoir levels",
        ],
        "frequency": "daily",
    },
    "Warning": {
        "alert_level": "warning",
        "actions": [
            "Test water parameters manually",
            "Check dosing pump operation",
            "Inspect heater/cooling",
        ],
        "frequency": "every 12 hours",
    },
    "Critical": {
        "alert_level": "critical",
        "actions": [
            "IMMEDIATE water change (25%)",
            "Test all parameters",
            "Check all equipment",
            "Do not add chemicals until parameters verified",
        ],
        "frequency": "immediate",
    },
}


class BacktestSimulator:
    """
    Simulate model performance over historical data.
    
    Tracks:
    - True positive, false positive, false negative rates
    - Alert frequency and urgency distribution
    - Actionable insights generated
    """
    
    def __init__(self):
        self.results: List[Dict] = []
        self.alerts: List[Dict] = []
    
    def simulate_predictions(
        self,
        df: pd.DataFrame,
        predictions: List[Dict],
    ) -> pd.DataFrame:
        """
        Simulate predictions over data.
        
        For each prediction, determine:
        - If alert should have fired (ground truth)
        - If alert actually fired (model prediction)
        - Time since previous alert
        """
        results = []
        
        for i, pred in enumerate(predictions):
            if i >= len(df):
                break
            
            row = df.iloc[i]
            actual_state = int(row.get("tank_state", 0))
            predicted_state = pred["state_id"]
            
            is_tp = (actual_state > 0 and predicted_state > 0)
            is_fp = (actual_state == 0 and predicted_state > 0)
            is_fn = (actual_state > 0 and predicted_state == 0)
            is_tn = (actual_state == 0 and predicted_state == 0)
            
            results.append({
                "timestamp": row.get("timestamp", i),
                "actual_state": actual_state,
                "predicted_state": predicted_state,
                "prediction_proba": pred["confidence"],
                "true_positive": is_tp,
                "false_positive": is_fp,
                "false_negative": is_fn,
                "true_negative": is_tn,
                "warning_params": pred.get("warning_params", []),
            })
        
        return pd.DataFrame(results)
    
    def calculate_metrics(
        self,
        results_df: pd.DataFrame,
    ) -> Dict:
        """
        Calculate backtest metrics.
        
        Metrics:
        - Accuracy, Precision, Recall, F1
        - Alert frequency by level
        - Mean time between alerts
        - Parameter-specific performance
        """
        tp = results_df["true_positive"].sum()
        fp = results_df["false_positive"].sum()
        fn = results_df["false_negative"].sum()
        tn = results_df["true_negative"].sum()
        
        accuracy = (tp + tn) / len(results_df) if len(results_df) > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        alert_counts = results_df["predicted_state"].value_counts().to_dict()
        
        return {
            "accuracy": float(accuracy),
            "precision": float(precision),
            "recall": float(recall),
            "f1_score": float(f1),
            "true_positives": int(tp),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_negatives": int(tn),
            "alert_counts": alert_counts,
            "total_predictions": len(results_df),
        }
    
    def generate_alerts(
        self,
        predictions: List[Dict],
        timestamps: List[datetime],
    ) -> List[Dict]:
        """
        Generate alerts from predictions.
        
        Filters alerts based on:
        - Confidence threshold
        - Cooldown period (avoid alert fatigue)
        """
        alerts = []
        last_alert_time = None
        cooldown_hours = 6
        
        for pred, ts in zip(predictions, timestamps):
            if pred["state_id"] == 0:
                continue
            
            if last_alert_time is not None:
                hours_since = (ts - last_alert_time).total_seconds() / 3600
                if hours_since < cooldown_hours:
                    continue
            
            config = ACTION_CONFIG.get(pred["state_name"], ACTION_CONFIG["Warning"])
            
            alerts.append({
                "timestamp": ts.isoformat(),
                "alert_level": config["alert_level"],
                "state": pred["state_name"],
                "confidence": pred["confidence"],
                "probability": pred["probability"],
                "actions": config["actions"],
                "warning_params": pred["warning_params"],
            })
            
            last_alert_time = ts
        
        return alerts
    
    def run_simulation(
        self,
        df: pd.DataFrame,
        classifier: "TankStateClassifier",
        forecast_model: "ChemistryForecastModel" = None,
    ) -> Dict:
        """
        Run complete backtest simulation.
        
        Returns metrics, alerts, and detailed results.
        """
        from features import FeatureEngineer, create_labels
        
        engineer = FeatureEngineer()
        df_features = engineer.create_all_features(df)
        df_labeled = create_labels(df_features)
        
        predictions = classifier.predict_with_confidence(df_labeled)
        
        results_df = self.simulate_predictions(df_labeled, predictions)
        metrics = self.calculate_metrics(results_df)
        
        if "timestamp" in df.columns:
            timestamps = pd.to_datetime(df["timestamp"]).tolist()
        else:
            timestamps = [datetime.now()] * len(df)
        
        alerts = self.generate_alerts(predictions, timestamps)
        
        return {
            "metrics": metrics,
            "alerts": alerts,
            "predictions": predictions[:10],
            "n_predictions": len(predictions),
        }


class AlertManager:
    """
    Manage alerts to balance urgency vs user experience.
    
    Key challenge from proposal:
    "Balancing the need for critical alerts with the user's 
    desire for not being too annoying or intrusive"
    """
    
    def __init__(
        self,
        critical_cooldown_hours: int = 1,
        warning_cooldown_hours: int = 6,
        min_confidence: float = 0.5,
    ):
        self.critical_cooldown = timedelta(hours=critical_cooldown_hours)
        self.warning_cooldown = timedelta(hours=warning_cooldown_hours)
        self.min_confidence = min_confidence
        
        self.last_alert_time: Dict[str, datetime] = {}
        self.alert_history: List[Dict] = []
    
    def should_alert(
        self,
        state: str,
        confidence: float,
        timestamp: datetime,
    ) -> bool:
        """
        Determine if alert should be sent.
        
        Rules:
        1. Confidence must exceed threshold
        2. Must be in cooldown period
        3. Critical alerts have shorter cooldown
        """
        if confidence < self.min_confidence:
            return False
        
        last_time = self.last_alert_time.get(state)
        
        if state == "Critical":
            cooldown = self.critical_cooldown
        else:
            cooldown = self.warning_cooldown
        
        if last_time is None:
            return True
        
        return (timestamp - last_time) >= cooldown
    
    def record_alert(
        self,
        state: str,
        timestamp: datetime,
    ):
        """Record alert sent for cooldown tracking."""
        self.last_alert_time[state] = timestamp
        
        self.alert_history.append({
            "state": state,
            "timestamp": timestamp.isoformat(),
        })
    
    def get_alert_frequency(self, hours: int = 24) -> Dict:
        """Get alert frequency over time window."""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        recent = [
            a for a in self.alert_history
            if pd.to_datetime(a["timestamp"]) > cutoff
        ]
        
        state_counts = {}
        for alert in recent:
            state = alert["state"]
            state_counts[state] = state_counts.get(state, 0) + 1
        
        return state_counts
    
    def adjust_sensitivity(
        self,
        target_alerts_per_day: int = 3,
    ):
        """
        Adjust sensitivity based on alert frequency.
        
        If alerts exceed target, increase confidence threshold.
        If alerts are too few, decrease threshold.
        """
        current_freq = self.get_alert_frequency(hours=24)
        total_alerts = sum(current_freq.values())
        
        if total_alerts > target_alerts_per_day:
            self.min_confidence = min(0.95, self.min_confidence + 0.05)
        elif total_alerts < target_alerts_per_day - 1:
            self.min_confidence = max(0.3, self.min_confidence - 0.05)
        
        return {
            "new_min_confidence": self.min_confidence,
            "current_alerts_per_day": total_alerts,
            "target_alerts_per_day": target_alerts_per_day,
        }


def generate_recommendations(
    predictions: List[Dict],
    forecasts: Optional[Dict[str, np.ndarray]] = None,
) -> List[Dict]:
    """
    Generate actionable recommendations based on model output.
    
    Combines:
    - Current tank state
    - Predicted trends
    - Parameter velocities
    
    Returns prioritized action list.
    """
    recommendations = []
    
    for pred in predictions:
        if pred["state_id"] == 0:
            recommendations.append({
                "priority": "low",
                "message": "Tank is stable. Continue regular monitoring.",
                "actions": [
                    "Test parameters on regular schedule",
                ],
            })
            continue
        
        state = pred["state_name"]
        params = pred.get("warning_params", [])
        
        if state == "Critical":
            recommendations.append({
                "priority": "critical",
                "message": f"CRITICAL: {', '.join(params)} out of range",
                "actions": ACTION_CONFIG["Critical"]["actions"],
            })
        else:
            recommendations.append({
                "priority": "medium",
                "message": f"Warning: {', '.join(params)} need attention",
                "actions": ACTION_CONFIG["Warning"]["actions"],
            })
    
    return recommendations[:5]


if __name__ == "__main__":
    from data_loader import generate_synthetic_data
    from features import FeatureEngineer, create_labels
    from classifier import TankStateClassifier
    
    print("Testing backtest simulation...")
    
    dfs = []
    for mode in [None, "heater_malfunction", "dosing_pump_clog"]:
        df = generate_synthetic_data(n_days=7, failure_mode=mode)
        dfs.append(df)
    
    df = pd.concat(dfs, ignore_index=True)
    
    engineer = FeatureEngineer()
    df_features = engineer.create_all_features(df)
    df_labeled = create_labels(df_features)
    
    model = TankStateClassifier(n_estimators=30, max_depth=3)
    model.fit(df_labeled)
    
    sim = BacktestSimulator()
    results = sim.run_simulation(df, model)
    
    print(f"Accuracy: {results['metrics']['accuracy']:.2%}")
    print(f"F1 Score: {results['metrics']['f1_score']:.2%}")
    print(f"Alerts generated: {len(results['alerts'])}")