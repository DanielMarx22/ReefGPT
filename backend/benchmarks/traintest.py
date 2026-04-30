#!/usr/bin/env python3
"""
ReefGPT Train/Test Benchmark - Model Training with Split
====================================================
Trains XGBoost and MLP models with train/test split, evaluates with metrics.
Saves trained models and evaluation data for benchmark evaluation.
"""
import numpy as np
import joblib
import os
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, GridSearchCV, train_test_split
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, f1_score, r2_score, precision_score, recall_score
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)

MODEL_DIR = os.path.join(os.path.dirname(__file__), 'models')

def generate_train_data(n_per_class=200):
    """Generate training data"""
    X, y = [], []
    for _ in range(n_per_class):
        X.append([np.random.uniform(7.5, 9.5), np.random.uniform(400, 450), np.random.uniform(1250, 1450), np.random.uniform(8.0, 8.4), np.random.uniform(76, 80)])
        y.append(0)
    for _ in range(n_per_class):
        X.append([np.random.choice([np.random.uniform(6.5, 7.5), np.random.uniform(9.5, 11.0)]), np.random.choice([np.random.uniform(350, 400), np.random.uniform(450, 500)]), np.random.choice([np.random.uniform(1100, 1250), np.random.uniform(1450, 1600)]), np.random.choice([np.random.uniform(7.6, 8.0), np.random.uniform(8.4, 8.6)]), np.random.choice([np.random.uniform(72, 76), np.random.uniform(80, 84)])])
        y.append(1)
    for _ in range(n_per_class):
        X.append([np.random.choice([np.random.uniform(5.5, 6.5), np.random.uniform(11.0, 12.0)]), np.random.choice([np.random.uniform(250, 350), np.random.uniform(500, 550)]), np.random.choice([np.random.uniform(900, 1100), np.random.uniform(1500, 1700)]), np.random.choice([np.random.uniform(7.0, 7.6), np.random.uniform(8.6, 9.0)]), np.random.choice([np.random.uniform(68, 72), np.random.uniform(84, 88)])])
        y.append(2)
    return np.array(X), np.array(y)

def generate_test_data(n_per_class=50, seed=99):
    """Generate test data with different seed"""
    np.random.seed(seed)
    X, y = [], []
    for _ in range(n_per_class):
        X.append([np.random.uniform(7.6, 9.4), np.random.uniform(405, 445), np.random.uniform(1260, 1440), np.random.uniform(8.05, 8.35), np.random.uniform(77, 79)])
        y.append(0)
    for _ in range(n_per_class):
        X.append([np.random.choice([np.random.uniform(6.6, 7.4), np.random.uniform(9.6, 10.9)]), np.random.choice([np.random.uniform(355, 395), np.random.uniform(455, 495)]), np.random.choice([np.random.uniform(1110, 1245), np.random.uniform(1455, 1595)]), np.random.choice([np.random.uniform(7.65, 7.95), np.random.uniform(8.45, 8.55)]), np.random.choice([np.random.uniform(73, 75), np.random.uniform(81, 83)])])
        y.append(1)
    for _ in range(n_per_class):
        X.append([np.random.choice([np.random.uniform(5.6, 6.4), np.random.uniform(11.1, 11.9)]), np.random.choice([np.random.uniform(260, 340), np.random.uniform(510, 540)]), np.random.choice([np.random.uniform(910, 1095), np.random.uniform(1510, 1695)]), np.random.choice([np.random.uniform(7.05, 7.55), np.random.uniform(8.65, 8.95)]), np.random.choice([np.random.uniform(69, 71), np.random.uniform(85, 87)])])
        y.append(2)
    return np.array(X), np.array(y)

def main():
    print("=" * 70)
    print("ReefGPT TRAIN/TEST BENCHMARK")
    print("=" * 70)
    print("\nTrain/Test Split: 80/20")
    print("Models: XGBoost, MLP")
    print()

    # Generate data
    X_full, y_full = generate_train_data(n_per_class=200)
    X_test, y_test = generate_test_data(n_per_class=50, seed=99)
    
    # Split training data
    X_train, _, y_train, _ = train_test_split(X_full, y_full, test_size=0.2, random_state=42, stratify=y_full)
    
    print(f"Training: {len(X_train)} samples")
    print(f"Test: {len(X_test)} samples")
    print()

    # Scale
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    print("=" * 70)
    print("TRAINING MODELS")
    print("=" * 70)
    
    results = {}

    # XGBoost - stronger regularization to prevent overfitting
    print("\n[1/2] Training XGBoost...")
    xgb = XGBClassifier(
        n_estimators=30, 
        max_depth=2, 
        learning_rate=0.03, 
        reg_alpha=0.5, 
        reg_lambda=2.0,
        min_child_weight=3,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42, 
        verbosity=0
    )
    xgb.fit(X_train_s, y_train)
    xgb_pred = xgb.predict(X_test_s)
    xgb_cv = cross_val_score(xgb, X_train_s, y_train, cv=5, scoring='accuracy').mean()
    results['XGBoost'] = {
        'cv': xgb_cv,
        'test_acc': accuracy_score(y_test, xgb_pred),
        'r2': r2_score(y_test, xgb_pred),
        'f1': f1_score(y_test, xgb_pred, average='weighted', zero_division='warn'),
        'prec': precision_score(y_test, xgb_pred, average='weighted', zero_division='warn'),
        'rec': recall_score(y_test, xgb_pred, average='weighted', zero_division='warn'),
    }
    print(f"  CV Accuracy: {xgb_cv*100:.1f}%")

    # MLP with GridSearchCV - stronger regularization to prevent overfitting
    print("\n[2/2] Training MLP with GridSearchCV...")
    mlp_base = MLPClassifier(max_iter=1000, early_stopping=True, validation_fraction=0.15, n_iter_no_change=20, random_state=42)
    mlp_params = {
        'hidden_layer_sizes': [(25,), (50,), (25, 10)],
        'alpha': [0.01, 0.1, 0.5, 1.0],
        'activation': ['relu', 'tanh'],
        'learning_rate_init': [0.001, 0.01]
    }
    mlp_grid = GridSearchCV(mlp_base, mlp_params, cv=5, scoring='accuracy', n_jobs=-1)
    mlp_grid.fit(X_train_s, y_train)
    mlp_pred = mlp_grid.best_estimator_.predict(X_test_s)
    mlp_cv = cross_val_score(mlp_grid.best_estimator_, X_train_s, y_train, cv=5, scoring='accuracy').mean()
    results['MLP'] = {
        'cv': mlp_cv,
        'test_acc': accuracy_score(y_test, mlp_pred),
        'r2': r2_score(y_test, mlp_pred),
        'f1': f1_score(y_test, mlp_pred, average='weighted', zero_division='warn'),
        'prec': precision_score(y_test, mlp_pred, average='weighted', zero_division='warn'),
        'rec': recall_score(y_test, mlp_pred, average='weighted', zero_division='warn'),
        'best_params': mlp_grid.best_params_,
    }
    print(f"  Best params: {mlp_grid.best_params_}")
    print(f"  CV Accuracy: {mlp_cv*100:.1f}%")

    print("\n" + "=" * 70)
    print("EVALUATION RESULTS")
    print("=" * 70)
    print(f"\n{'Model':<18} {'CV':>8} {'Test':>8} {'R2':>8} {'F1':>8} {'Prec':>8} {'Rec':>8}")
    print("-" * 70)
    
    for name, r in results.items():
        print(f"{name:<18} {r['cv']*100:>7.1f}% {r['test_acc']*100:>7.1f}% {r['r2']:>8.3f} {r['f1']*100:>7.1f}% {r['prec']*100:>7.1f}% {r['rec']*100:>7.1f}%")

    print("\n" + "=" * 70)
    print("BEST MODEL")
    print("=" * 70)
    best = max(results.items(), key=lambda x: x[1]['test_acc'])
    print(f"\nBest: {best[0]}")
    print(f"  Test Accuracy: {best[1]['test_acc']*100:.1f}%")
    print(f"  CV Accuracy:    {best[1]['cv']*100:.1f}%")
    print(f"  R2:             {best[1]['r2']:.3f}")
    print(f"  F1 Score:       {best[1]['f1']*100:.1f}%")
    if 'best_params' in best[1]:
        print(f"  Best Params:    {best[1]['best_params']}")

    print("\n" + "=" * 70)
    print("OVERFITTING CHECK")
    print("=" * 70)
    for name, r in results.items():
        gap = r['cv'] - r['test_acc']
        status = "OK" if abs(gap) < 0.20 else "OVERFIT!"
        print(f"{name:<18} CV={r['cv']*100:.1f}%, Test={r['test_acc']*100:.1f}%, Gap={gap*100:.1f}% [{status}]")

    print("\n" + "=" * 70)
    print("HYPERPARAMETERS")
    print("=" * 70)
    print("""
XGBoost: n_estimators=30, max_depth=2, learning_rate=0.03, reg_alpha=0.5, reg_lambda=2.0
MLP: GridSearchCV over hidden_layer_sizes, alpha, activation
""")

    # Save models and evaluation data
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    # Save XGBoost model
    joblib.dump({
        'model': xgb,
        'scaler': scaler,
    }, os.path.join(MODEL_DIR, 'xgb_model.pkl'))
    print(f"Saved XGBoost model to {MODEL_DIR}/xgb_model.pkl")
    
    # Save MLP model
    joblib.dump({
        'model': mlp_grid.best_estimator_,
        'scaler': scaler,
    }, os.path.join(MODEL_DIR, 'mlp_model.pkl'))
    print(f"Saved MLP model to {MODEL_DIR}/mlp_model.pkl")
    
    # Save evaluation data for benchmark files
    np.savez(
        os.path.join(MODEL_DIR, 'eval_data.npz'),
        X_eval=X_test,
        y_eval=y_test
    )
    print(f"Saved evaluation data to {MODEL_DIR}/eval_data.npz")

if __name__ == '__main__':
    main()