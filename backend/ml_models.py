"""
ReefGPT ML Models
================
Random Forest (Regression) and XGBoost (Classification) 
with staleness tracking and feature engineering.

Usage:
    from ml_models import ChemistryForecastModel, TankStateClassifier, create_ml_pipeline
    
    # Create and train models
    models = create_ml_pipeline(df)
    
    # Predict 24-hour forecast
    forecast = models.predict_forecast(df, target_param='Alkalinity')
    
    # Classify tank state
    state = models.classify_state(df)
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# ML Libraries
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_squared_error, accuracy_score
from xgboost import XGBClassifier
import joblib
import os

from features import (
    PARAMETERS,
    IDEAL_RANGES,
    CRITICAL_RANGES,
    calculate_velocity,
    calculate_acceleration,
    calculate_inter_param_ratios,
    calculate_deviation,
    create_labels,
    StalenessTracker,
)


class ChemistryForecastModel:
    """
    Random Forest Regression for 24-hour chemistry forecasting.
    
    Uses:
    - Forward-fill with decay (staleness tracking)
    - Velocity and acceleration features
    - Inter-parameter ratios
    
    Usage:
        model = ChemistryForecastModel()
        model.fit(df, target_param='Alkalinity')
        prediction = model.predict_24h(current_features)
    """
    
    def __init__(
        self, 
        n_estimators: int = 100,
        max_depth: int = 10,
        min_samples_split: int = 5,
        decay_rate: float = 0.9,
        max_staleness: int = 72,
    ):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.decay_rate = decay_rate
        self.max_staleness = max_staleness
        
        # Model components
        self.model: Optional[RandomForestRegressor] = None
        self.scaler = StandardScaler()
        self.imputer = SimpleImputer(strategy='median')
        self.feature_cols: List[str] = []
        self.target_param: str = ""
        self.is_fitted: bool = False
    
    def _prepare_data(
        self, 
        df: pd.DataFrame, 
        target_param: str
    ) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Prepare features and target for training/inference.
        
        Applies:
        1. Staleness tracking (forward-fill with decay)
        2. Feature engineering (velocity, acceleration, ratios)
        3. Forecasting target (value in 24h = current + velocity*4)
        """
        # Exclude timestamp column
        df = df.drop(columns=['timestamp'], errors='ignore')
        
        # Apply staleness tracking
        tracker = StalenessTracker(
            max_staleness=self.max_staleness,
            decay_rate=self.decay_rate
        )
        df_processed = tracker.apply_decay(df.copy())
        
        # Calculate features
        feature_df = self._extract_features(df_processed)
        
        # Create target: current_value + velocity*4 (24h prediction)
        target_col = f"{target_param}_velocity"
        if target_col in feature_df.columns:
            # Target = current + velocity * 4
            feature_df[f"{target_param}_target_24h"] = (
                feature_df[target_param] + 
                feature_df[target_col] * 4
            )
        
        # Remove rows without targets
        target_col = f"{target_param}_target_24h"
        if target_col not in feature_df.columns:
            return feature_df[[target_param]], np.array([np.nan] * len(df))
        
        valid_mask = ~feature_df[target_col].isna()
        feature_df = feature_df[valid_mask]
        
        # Drop target column from features
        y = feature_df[target_col].values
        X = feature_df.drop(columns=[target_col], errors='ignore')
        
        return X, y
    
    def _extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract all features from dataframe."""
        result = df.copy()
        
        # Convert timestamp to hours since first reading (numeric)
        if 'timestamp' in result.columns:
            timestamps = pd.to_datetime(result['timestamp'])
            if len(timestamps) > 1:
                hours_elapsed = (timestamps - timestamps.min()).dt.total_seconds() / 3600
                result['hours_elapsed'] = hours_elapsed
            result = result.drop(columns=['timestamp'])
        
        # Velocity features
        for param in PARAMETERS:
            if param in result.columns:
                result[f"{param}_velocity"] = calculate_velocity(result, param)
                result[f"{param}_acceleration"] = calculate_acceleration(result, param)
        
        # Inter-parameter ratios
        ratios = calculate_inter_param_ratios(result)
        for ratio_name, ratio_values in ratios.items():
            result[ratio_name] = ratio_values
        
        # Deviation from ideal
        deviations = calculate_deviation(result)
        for col, dev_values in deviations.items():
            result[col] = dev_values
        
        # Staleness weight
        if '_staleness_weight' in result.columns:
            result['_staleness_weight'] = result['_staleness_weight']
        
        # Select numeric columns only
        result = result.select_dtypes(include=[np.number])
        
        return result
    
    def _prepare_predict_features(self, df: pd.DataFrame) -> np.ndarray:
        """Prepare features for prediction (single row or batch)."""
        tracker = StalenessTracker(
            max_staleness=self.max_staleness,
            decay_rate=self.decay_rate
        )
        df_processed = tracker.apply_decay(df.copy())
        feature_df = self._extract_features(df_processed)
        
        # Align columns to training
        X = pd.DataFrame(columns=self.feature_cols)
        for col in self.feature_cols:
            if col in feature_df.columns:
                X[col] = feature_df[col].values[-len(X):] if len(X) > 0 else [feature_df[col].iloc[-1]]
            else:
                X[col] = 0
        
        return X.values[-1:] if len(X) > 0 else np.array([])
    
    def fit(
        self, 
        df: pd.DataFrame, 
        target_param: str = "Alkalinity"
    ) -> "ChemistryForecastModel":
        """Train the Random Forest model."""
        X, y = self._prepare_data(df, target_param)
        
        if len(X) < 10:
            print(f"Not enough data to train model for {target_param}")
            return self
        
        # Store feature columns
        self.feature_cols = [c for c in X.columns if c != f"{target_param}_target_24h"]
        
        # Impute missing values
        X_imputed = self.imputer.fit_transform(X[self.feature_cols])
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X_imputed)
        
        # Train Random Forest
        self.model = RandomForestRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            min_samples_split=self.min_samples_split,
            random_state=42,
            n_jobs=-1,
        )
        self.model.fit(X_scaled, y)
        
        self.target_param = target_param
        self.is_fitted = True
        
        # Calculate training error
        y_pred = self.model.predict(X_scaled)
        rmse = np.sqrt(mean_squared_error(y, y_pred))
        print(f"Trained {target_param} model. RMSE: {rmse:.3f}")
        
        return self
    
    def predict_24h(self, df: pd.DataFrame) -> Dict:
        """
        Predict parameter value in 24 hours.
        
        Returns:
            {
                "current": float,
                "predicted_24h": float,
                "confidence": float,
            }
        """
        if not self.is_fitted:
            return {"error": "Model not trained"}
        
        try:
            # Get latest row for prediction
            latest = df.iloc[-1:]
            current_val = latest[self.target_param].iloc[-1]
            
            # Prepare features
            X = self._prepare_predict_features(latest)
            X_imputed = self.imputer.transform(X)
            X_scaled = self.scaler.transform(X_imputed)
            
            # Predict
            pred_24h = self.model.predict(X_scaled)[0]
            
            return {
                "current": float(current_val),
                "predicted_24h": round(float(pred_24h), 2),
                "param": self.target_param,
            }
        except Exception as e:
            return {"error": str(e)}
    
    def save(self, path: str):
        """Save model to disk."""
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'imputer': self.imputer,
            'feature_cols': self.feature_cols,
            'target_param': self.target_param,
            'decay_rate': self.decay_rate,
            'max_staleness': self.max_staleness,
        }, path)
    
    @classmethod
    def load(cls, path: str) -> "ChemistryForecastModel":
        """Load model from disk."""
        data = joblib.load(path)
        model = cls(
            decay_rate=data.get('decay_rate', 0.9),
            max_staleness=data.get('max_staleness', 72),
        )
        model.model = data['model']
        model.scaler = data['scaler']
        model.imputer = data['imputer']
        model.feature_cols = data['feature_cols']
        model.target_param = data['target_param']
        model.is_fitted = True
        return model


class TankStateClassifier:
    """
    XGBoost Classifier for tank state (Stable/Warning/Critical).
    
    Uses:
    - All parameters with staleness tracking
    - Velocity and acceleration
    - Inter-parameter ratios
    - Deviation from ideal
    
    Usage:
        classifier = TankStateClassifier()
        classifier.fit(df)
        state = classifier.predict(df)
    """
    
    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 6,
        learning_rate: float = 0.1,
        decay_rate: float = 0.9,
        max_staleness: int = 72,
    ):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.decay_rate = decay_rate
        self.max_staleness = max_staleness
        
        self.model: Optional[XGBClassifier] = None
        self.scaler = StandardScaler()
        self.imputer = SimpleImputer(strategy='median')
        self.feature_cols: List[str] = []
        self.is_fitted: bool = False
        
        # State mapping
        self.state_names = {0: "Stable", 1: "Warning", 2: "Critical"}
        self.state_colors = {0: "#22c55e", 1: "#f59e0b", 2: "#ef4444"}
    
    def _prepare_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, np.ndarray]:
        """Prepare features and labels."""
        # Exclude timestamp column
        df = df.drop(columns=['timestamp'], errors='ignore')
        
        # Apply staleness tracking
        tracker = StalenessTracker(
            max_staleness=self.max_staleness,
            decay_rate=self.decay_rate
        )
        df_processed = tracker.apply_decay(df.copy())
        
        # Calculate features
        feature_df = self._extract_features(df_processed)
        
        # Create labels
        labeled_df = create_labels(feature_df)
        
        # Remove rows without labels
        if 'tank_state' not in labeled_df.columns:
            return feature_df, np.array([0] * len(feature_df))
        
        valid_mask = ~labeled_df['tank_state'].isna()
        labeled_df = labeled_df[valid_mask]
        
        X = labeled_df.drop(columns=['tank_state'], errors='ignore')
        y = labeled_df['tank_state'].values.astype(int)
        
        return X, y
    
    def _extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract all features."""
        result = df.copy()
        
        # Convert timestamp to hours since first reading (numeric)
        if 'timestamp' in result.columns:
            timestamps = pd.to_datetime(result['timestamp'])
            if len(timestamps) > 1:
                hours_elapsed = (timestamps - timestamps.min()).dt.total_seconds() / 3600
                result['hours_elapsed'] = hours_elapsed
            result = result.drop(columns=['timestamp'])
        
        # Velocity and acceleration
        for param in PARAMETERS:
            if param in result.columns:
                result[f"{param}_velocity"] = calculate_velocity(result, param)
                result[f"{param}_acceleration"] = calculate_acceleration(result, param)
        
        # Inter-parameter ratios
        ratios = calculate_inter_param_ratios(result)
        for ratio_name, ratio_values in ratios.items():
            result[ratio_name] = ratio_values
        
        # Deviation
        deviations = calculate_deviation(result)
        for col, dev_values in deviations.items():
            result[col] = dev_values
        
        # Staleness
        if '_staleness_weight' in result.columns:
            result['_staleness_weight'] = result['_staleness_weight']
        
        return result
    
    def fit(self, df: pd.DataFrame) -> "TankStateClassifier":
        """Train XGBoost classifier."""
        X, y = self._prepare_data(df)
        
        if len(X) < 10:
            print("Not enough data to train classifier")
            return self
        
        # Get feature columns
        self.feature_cols = [c for c in X.columns if c != 'tank_state']
        
        # Impute and scale
        X_imputed = self.imputer.fit_transform(X[self.feature_cols])
        X_scaled = self.scaler.fit_transform(X_imputed)
        
        # Train XGBoost
        self.model = XGBClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            random_state=42,
            use_label_encoder=False,
            eval_metric='mlogloss',
        )
        self.model.fit(X_scaled, y)
        
        # Training accuracy
        y_pred = self.model.predict(X_scaled)
        acc = accuracy_score(y, y_pred)
        print(f"Trained classifier. Accuracy: {acc:.1%}")
        
        self.is_fitted = True
        return self
    
    def predict(self, df: pd.DataFrame) -> Dict:
        """
        Predict tank state.
        
        Returns:
            {
                "state_id": 0/1/2,
                "state_name": "Stable"/"Warning"/"Critical",
                "confidence": float,
                "warning_params": List[str],
            }
        """
        if not self.is_fitted:
            return {"error": "Model not trained"}
        
        try:
            # Prepare features
            X = self._extract_features(df)
            
            # Align columns
            X_aligned = pd.DataFrame(columns=self.feature_cols)
            for col in self.feature_cols:
                if col in X.columns:
                    X_aligned[col] = X[col].values[-len(X_aligned):]
                else:
                    X_aligned[col] = 0
            
            # Get latest row
            X_latest = X_aligned.iloc[-1:].values
            
            X_imputed = self.imputer.transform(X_latest)
            X_scaled = self.scaler.transform(X_imputed)
            
            # Predict
            state_id = int(self.model.predict(X_scaled)[0])
            probabilities = self.model.predict_proba(X_scaled)[0]
            confidence = float(max(probabilities))
            
            # Find warning parameters
            warning_params = []
            for param in PARAMETERS:
                if param in df.columns:
                    val = df[param].iloc[-1]
                    i_min, i_max = IDEAL_RANGES.get(param, (0, 100))
                    if val < i_min or val > i_max:
                        warning_params.append(param)
            
            return {
                "state_id": state_id,
                "state_name": self.state_names[state_id],
                "confidence": confidence,
                "warning_params": warning_params,
            }
        except Exception as e:
            return {"error": str(e)}
    
    def save(self, path: str):
        """Save model to disk."""
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'imputer': self.imputer,
            'feature_cols': self.feature_cols,
            'decay_rate': self.decay_rate,
            'max_staleness': self.max_staleness,
        }, path)
    
    @classmethod
    def load(cls, path: str) -> "TankStateClassifier":
        """Load model from disk."""
        data = joblib.load(path)
        model = cls(
            decay_rate=data.get('decay_rate', 0.9),
            max_staleness=data.get('max_staleness', 72),
        )
        model.model = data['model']
        model.scaler = data['scaler']
        model.imputer = data['imputer']
        model.feature_cols = data['feature_cols']
        model.is_fitted = True
        return model


def create_ml_pipeline(df: pd.DataFrame) -> Dict:
    """
    Create full ML pipeline with all models.
    
    Returns:
        {
            "forecast_models": {param: ChemistryForecastModel},
            "classifier": TankStateClassifier,
        }
    """
    # Train classifier
    classifier = TankStateClassifier()
    classifier.fit(df)
    
    # Train forecast models for each parameter
    forecast_models = {}
    for param in PARAMETERS:
        if param in df.columns:
            model = ChemistryForecastModel()
            model.fit(df, param)
            forecast_models[param] = model
    
    return {
        "classifier": classifier,
        "forecast_models": forecast_models,
    }


# For backward compatibility (imports from inference)
def create_predictor(user_id: str = None):
    """Legacy function - now uses ML pipeline."""
    from inference import create_predictor as old_create
    return old_create(user_id)


if __name__ == "__main__":
    # Test with synthetic data
    from data_loader import generate_synthetic_data
    
    print("Generating test data...")
    df = generate_synthetic_data(n_days=30)
    
    print("\nTraining ML pipeline...")
    pipeline = create_ml_pipeline(df)
    
    print("\n=== Testing Classifier ===")
    state = pipeline["classifier"].predict(df)
    print(f"State: {state}")
    
    print("\n=== Testing Forecast ===")
    for param in PARAMETERS:
        if param in df.columns:
            forecast = pipeline["forecast_models"][param].predict_24h(df)
            print(f"{param}: {forecast}")