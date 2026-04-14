"""
Random Forest forecasting model for reef tank chemistry.

Model A (Regression): Predicts 24-hour chemistry trends.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
import joblib
import os

PARAMETERS = ["Alkalinity", "Calcium", "Magnesium", "pH", "Temperature"]


class ChemistryForecastModel:
    """
    Random Forest model for forecasting chemistry parameters.
    """
    
    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 10,
        min_samples_split: int = 5,
        min_samples_leaf: int = 2,
        random_state: int = 42,
    ):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.random_state = random_state
        
        self.models: Dict[str, RandomForestRegressor] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.imputer = SimpleImputer(strategy="median")
        self.feature_columns: List[str] = []
        
        self.is_fitted = False
    
    def _get_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract feature columns for training/prediction."""
        feature_cols = []
        
        base_params = ["Alkalinity", "Calcium", "Magnesium", "pH", "Temperature"]
        derived = [
            "_velocity", "_acceleration", "_rolling_mean", "_rolling_std", "_cv",
            "_lag_", "_staleness", "_deviation",
        ]
        
        for col in df.columns:
            for param in base_params:
                if param in col or any(d in col for d in derived):
                    if col not in ["timestamp", "tank_state", "Alkalinity_forecast_target"]:
                        feature_cols.append(col)
        
        return df[[c for c in feature_cols if c in df.columns]]
    
    def _prepare_data(
        self,
        df: pd.DataFrame,
        target_param: str,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare features and targets."""
        features_df = self._get_features(df)
        
        target_col = f"{target_param}_forecast_target"
        if target_col not in df.columns:
            return None, None
        
        valid_mask = ~df[target_col].isna()
        
        X = features_df[valid_mask].values
        y = df.loc[valid_mask, target_col].values
        
        return X, y
    
    def fit(
        self,
        df: pd.DataFrame,
        target_param: str,
    ) -> "ChemistryForecastModel":
        """
        Fit the forecasting model.
        
        Math: For each tree in the ensemble:
        - Bootstrap sample training data
        - Find best split using MSE reduction
        - Average predictions across all trees
        """
        X, y = self._prepare_data(df, target_param)
        
        if X is None or len(X) < 10:
            print(f"Insufficient data to fit model for {target_param}")
            return self
        
        self.feature_columns = self._get_features(df).columns.tolist()
        
        X_imputed = self.imputer.fit_transform(X)
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_imputed)
        
        model = RandomForestRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            min_samples_split=self.min_samples_split,
            min_samples_leaf=self.min_samples_leaf,
            random_state=self.random_state,
            n_jobs=-1,
        )
        
        model.fit(X_scaled, y)
        
        self.models[target_param] = model
        self.scalers[target_param] = scaler
        
        self.is_fitted = True
        
        return self
    
    def predict(
        self,
        df: pd.DataFrame,
        target_param: str,
    ) -> np.ndarray:
        """
        Predict future values.
        
        Returns predicted value at horizon (default 24h).
        """
        if target_param not in self.models:
            raise ValueError(f"Model not fitted for {target_param}")
        
        features_df = self._get_features(df)
        
        X = features_df.values
        X_imputed = self.imputer.transform(X)
        X_scaled = self.scalers[target_param].transform(X_imputed)
        
        predictions = self.models[target_param].predict(X_scaled)
        
        return predictions
    
    def predict_with_confidence(
        self,
        df: pd.DataFrame,
        target_param: str,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Predict with confidence intervals.
        
        Math: Use prediction standard deviation across trees
        as measure of uncertainty.
        """
        if target_param not in self.models:
            raise ValueError(f"Model not fitted for {target_param}")
        
        features_df = self._get_features(df)
        
        X = features_df.values
        X_imputed = self.imputer.transform(X)
        X_scaled = self.scalers[target_param].transform(X_imputed)
        
        model = self.models[target_param]
        
        predictions = np.array([
            estimator.predict(X_scaled) 
            for estimator in model.estimators_
        ])
        
        mean_pred = np.mean(predictions, axis=0)
        std_pred = np.std(predictions, axis=0)
        
        lower = mean_pred - 1.96 * std_pred
        upper = mean_pred + 1.96 * std_pred
        
        return mean_pred, lower, upper
    
    def get_feature_importance(
        self,
        target_param: str,
    ) -> pd.DataFrame:
        """Get feature importance for interpretability."""
        if target_param not in self.models:
            return pd.DataFrame()
        
        importances = self.models[target_param].feature_importances_
        
        return pd.DataFrame({
            "feature": self.feature_columns,
            "importance": importances,
        }).sort_values("importance", ascending=False)
    
    def save(self, filepath: str):
        """Save model to disk."""
        model_data = {
            "models": self.models,
            "scalers": self.scalers,
            "feature_columns": self.feature_columns,
            "n_estimators": self.n_estimators,
            "max_depth": self.max_depth,
            "min_samples_split": self.min_samples_split,
            "min_samples_leaf": self.min_samples_leaf,
            "random_state": self.random_state,
        }
        joblib.dump(model_data, filepath)
    
    def load(self, filepath: str):
        """Load model from disk."""
        model_data = joblib.load(filepath)
        
        self.models = model_data["models"]
        self.scalers = model_data["scalers"]
        self.feature_columns = model_data["feature_columns"]
        self.n_estimators = model_data["n_estimators"]
        self.max_depth = model_data["max_depth"]
        self.min_samples_split = model_data["min_samples_split"]
        self.min_samples_leaf = model_data["min_samples_leaf"]
        self.random_state = model_data["random_state"]
        
        self.is_fitted = len(self.models) > 0


def train_forecasting_model(
    df: pd.DataFrame,
    target_param: str = "Alkalinity",
    horizon_hours: int = 24,
    **model_kwargs,
) -> ChemistryForecastModel:
    """
    Train a forecasting model for a specific parameter.
    """
    from features import create_forecast_labels
    
    df_labeled = create_forecast_labels(df, target_param, horizon_hours)
    
    model = ChemistryForecastModel(**model_kwargs)
    model.fit(df_labeled, target_param)
    
    return model


if __name__ == "__main__":
    from data_loader import generate_synthetic_data
    from features import create_labels
    
    print("Testing forecasting model...")
    
    df = generate_synthetic_data(n_days=30)
    from features import FeatureEngineer
    
    engineer = FeatureEngineer()
    df_features = engineer.create_all_features(df)
    df_labeled = create_labels(df_features)
    
    from features import create_forecast_labels
    df_forecast = create_forecast_labels(df_labeled, "Alkalinity", horizon_hours=24)
    
    df_forecast = df_forecast.dropna(subset=["Alkalinity_forecast_target"])
    
    model = ChemistryForecastModel(n_estimators=50, max_depth=5)
    model.fit(df_forecast, "Alkalinity")
    
    if model.is_fitted:
        preds = model.predict(df_forecast, "Alkalinity")
        print(f"Predictions: {preds[:5]}")
        
        importance = model.get_feature_importance("Alkalinity")
        print(f"Top features: {importance.head()}")