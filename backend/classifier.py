"""
XGBoost classification model for reef tank state detection.

Model B (Classification): Identifies "Stable", "Warning", or "Critical" tank states.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from xgboost import XGBClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib

PARAMETERS = ["Alkalinity", "Calcium", "Magnesium", "pH", "Temperature"]

STATE_NAMES = {0: "Stable", 1: "Warning", 2: "Critical"}
STATE_COLORS = {0: "#22c55e", 1: "#f59e0b", 2: "#ef4444"}


class TankStateClassifier:
    """
    XGBoost classifier for tank state detection.
    
    States:
    - 0 (Stable): All parameters in ideal range
    - 1 (Warning): Any parameter outside ideal but in critical range
    - 2 (Critical): Any parameter outside critical range
    """
    
    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 6,
        learning_rate: float = 0.1,
        min_child_weight: int = 1,
        subsample: float = 0.8,
        colsample_bytree: float = 0.8,
        random_state: int = 42,
    ):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.min_child_weight = min_child_weight
        self.subsample = subsample
        self.colsample_bytree = colsample_bytree
        self.random_state = random_state
        
        self.model: Optional[XGBClassifier] = None
        self.scaler = StandardScaler()
        self.imputer = SimpleImputer(strategy="median")
        self.label_encoder = LabelEncoder()
        self.feature_columns: List[str] = []
        
        self.is_fitted = False
        
        self.feature_importance_df = None
    
    def _get_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract feature columns for training/prediction."""
        feature_cols = []
        
        base_params = ["Alkalinity", "Calcium", "Magnesium", "pH", "Temperature"]
        derived = [
            "_velocity", "_acceleration", "_rolling_mean", "_rolling_std", "_cv",
            "_lag_", "_staleness", "_deviation", "_in_ideal_range",
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
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare features and targets."""
        if "tank_state" not in df.columns:
            raise ValueError("DataFrame must contain 'tank_state' column")
        
        features_df = self._get_features(df)
        
        valid_mask = ~df["tank_state"].isna()
        
        X = features_df[valid_mask].values
        y = df.loc[valid_mask, "tank_state"].values
        
        return X, y
    
    def fit(
        self,
        df: pd.DataFrame,
        val_size: float = 0.2,
    ) -> "TankStateClassifier":
        """
        Fit the classification model.
        
        Math: XGBoost minimizes:
        L = sum_i[g_i * f(x_i) + h_i * f(x_i)²] + gamma * T
        
        Where:
        - g_i, h_i = gradients of loss function
        - f(x) = tree prediction
        - gamma = regularizer
        - T = number of leaves
        """
        X, y = self._prepare_data(df)
        
        if len(X) < 10:
            print("Insufficient data to fit classifier")
            return self
        
        self.feature_columns = self._get_features(df).columns.tolist()
        
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=val_size, random_state=self.random_state
        )
        
        X_train_imputed = self.imputer.fit_transform(X_train)
        X_train_scaled = self.scaler.fit_transform(X_train_imputed)
        
        X_val_imputed = self.imputer.transform(X_val)
        X_val_scaled = self.scaler.transform(X_val_imputed)
        
        self.label_encoder.fit([0, 1, 2])
        
        self.model = XGBClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            min_child_weight=self.min_child_weight,
            subsample=self.subsample,
            colsample_bytree=self.colsample_bytree,
            random_state=self.random_state,
            use_label_encoder=False,
            eval_metric="mlogloss",
            early_stopping_rounds=10,
        )
        
        self.model.fit(
            X_train_scaled, y_train,
            eval_set=[(X_val_scaled, y_val)],
            verbose=False,
        )
        
        self.is_fitted = True
        
        return self
    
    def predict(
        self,
        df: pd.DataFrame,
    ) -> np.ndarray:
        """
        Predict tank state.
        
        Returns class predictions (0=Stable, 1=Warning, 2=Critical).
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        features_df = self._get_features(df)
        
        X = features_df.values
        X_imputed = self.imputer.transform(X)
        X_scaled = self.scaler.transform(X_imputed)
        
        predictions = self.model.predict(X_scaled)
        
        return predictions
    
    def predict_proba(
        self,
        df: pd.DataFrame,
    ) -> np.ndarray:
        """
        Predict class probabilities.
        
        Returns array of shape (n_samples, 3) with probabilities
        for each class.
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        features_df = self._get_features(df)
        
        X = features_df.values
        X_imputed = self.imputer.transform(X)
        X_scaled = self.scaler.transform(X_imputed)
        
        probas = self.model.predict_proba(X_scaled)
        
        return probas
    
    def predict_with_confidence(
        self,
        df: pd.DataFrame,
    ) -> List[Dict]:
        """
        Predict with state name, probability, and confidence.
        
        Returns list of dicts with:
        - state_id: 0, 1, or 2
        - state_name: "Stable", "Warning", or "Critical"
        - probability: probability of predicted class
        - confidence: max probability across all classes
        - warning_params: parameters causing warning/critical
        """
        predictions = self.predict(df)
        probas = self.predict_proba(df)
        
        results = []
        
        for i, (pred, proba) in enumerate(zip(predictions, probas)):
            pred_proba = proba[pred]
            confidence = np.max(proba)
            
            warning_params = self._get_warning_parameters(df.iloc[i])
            
            results.append({
                "state_id": int(pred),
                "state_name": STATE_NAMES[pred],
                "probability": float(pred_proba),
                "confidence": float(confidence),
                "warning_params": warning_params,
            })
        
        return results
    
    def _get_warning_parameters(
        self,
        row: pd.Series,
    ) -> List[str]:
        """Get parameters causing warning/critical state."""
        warnings = []
        
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
        
        for param, (ideal_min, ideal_max) in IDEAL_RANGES.items():
            if param not in row.index:
                continue
            
            value = row[param]
            if pd.isna(value):
                continue
            
            crit_min, crit_max = CRITICAL_RANGES[param]
            
            if value < crit_min or value > crit_max:
                warnings.append(param)
        
        return warnings
    
    def get_feature_importance(self) -> pd.DataFrame:
        """Get feature importance for interpretability."""
        if not self.is_fitted:
            return pd.DataFrame()
        
        importances = self.model.feature_importances_
        
        self.feature_importance_df = pd.DataFrame({
            "feature": self.feature_columns,
            "importance": importances,
        }).sort_values("importance", ascending=False)
        
        return self.feature_importance_df
    
    def evaluate(self, df: pd.DataFrame) -> Dict:
        """Evaluate model performance."""
        if "tank_state" not in df.columns:
            raise ValueError("DataFrame must contain 'tank_state' column")
        
        X, y_true = self._prepare_data(df)
        
        X_imputed = self.imputer.transform(X)
        X_scaled = self.scaler.transform(X_imputed)
        
        y_pred = self.model.predict(X_scaled)
        
        report = classification_report(
            y_true, y_pred, 
            target_names=["Stable", "Warning", "Critical"],
            output_dict=True,
        )
        
        cm = confusion_matrix(y_true, y_pred)
        
        return {
            "classification_report": report,
            "confusion_matrix": cm.tolist(),
            "accuracy": float(report["accuracy"]),
        }
    
    def save(self, filepath: str):
        """Save model to disk."""
        model_data = {
            "model": self.model,
            "scaler": self.scaler,
            "imputer": self.imputer,
            "label_encoder": self.label_encoder,
            "feature_columns": self.feature_columns,
            "n_estimators": self.n_estimators,
            "max_depth": self.max_depth,
            "learning_rate": self.learning_rate,
            "random_state": self.random_state,
        }
        joblib.dump(model_data, filepath)
    
    def load(self, filepath: str):
        """Load model from disk."""
        model_data = joblib.load(filepath)
        
        self.model = model_data["model"]
        self.scaler = model_data["scaler"]
        self.imputer = model_data["imputer"]
        self.label_encoder = model_data["label_encoder"]
        self.feature_columns = model_data["feature_columns"]
        self.n_estimators = model_data["n_estimators"]
        self.max_depth = model_data["max_depth"]
        self.learning_rate = model_data["learning_rate"]
        self.random_state = model_data["random_state"]
        
        self.is_fitted = self.model is not None


def train_classifier(
    df: pd.DataFrame,
    **model_kwargs,
) -> TankStateClassifier:
    """Train a tank state classifier."""
    model = TankStateClassifier(**model_kwargs)
    model.fit(df)
    return model


if __name__ == "__main__":
    from data_loader import generate_synthetic_data
    from features import FeatureEngineer, create_labels
    
    print("Testing classifier...")
    
    dfs = []
    for mode in [None, "heater_malfunction", "dosing_pump_clog"]:
        df = generate_synthetic_data(n_days=14, failure_mode=mode)
        dfs.append(df)
    
    df = pd.concat(dfs, ignore_index=True)
    
    engineer = FeatureEngineer()
    df_features = engineer.create_all_features(df)
    df_labeled = create_labels(df_features)
    
    model = TankStateClassifier(n_estimators=50, max_depth=4)
    model.fit(df_labeled)
    
    if model.is_fitted:
        preds = model.predict_with_confidence(df_labeled)
        print(f"Sample predictions: {preds[:3]}")
        
        importance = model.get_feature_importance()
        print(f"Top features: {importance.head()}")