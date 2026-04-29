#!/usr/bin/env python3
"""
ReefGPT Full Benchmark - Comprehensive ML Model Evaluation
============================================================
 Trains on synthetic data, evaluates on NEW generated test data with noise.
"""
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, f1_score, r2_score, precision_score, recall_score

np.random.seed(42)

def generate_train_data(n_per_class=500):
    """Generate clean training data - NO noise for clear class separation"""
    X, y = [], []
    
    # STABLE class (0): All parameters optimal
    for _ in range(n_per_class):
        X.append([
            np.random.uniform(8.0, 8.4),      # pH
            np.random.uniform(400, 450),        # Calcium
            np.random.uniform(1250, 1450),    # Magnesium
            np.random.uniform(8.0, 9.5),     # Alkalinity
            78.0                            # Temp
        ])
        y.append(0)
    
    # WARNING class (1): Parameters slightly off
    for _ in range(n_per_class):
        X.append([
            np.random.uniform(7.5, 8.0),      # pH
            np.random.uniform(350, 400),        # Calcium
            np.random.uniform(1100, 1250),    # Magnesium
            np.random.uniform(7.0, 8.0),     # Alkalinity
            78.0
        ])
        y.append(1)
    
    # CRITICAL class (2): Parameters out of range
    for _ in range(n_per_class):
        X.append([
            np.random.uniform(6.5, 7.5),      # pH
            np.random.uniform(280, 350),        # Calcium
            np.random.uniform(850, 1100),       # Magnesium
            np.random.uniform(5.5, 7.0),     # Alkalinity
            78.0
        ])
        y.append(2)
    
    return np.array(X), np.array(y)

def generate_test_data(n_per_class=100, add_noise=True):
    """Generate NEW test data with realistic sensor noise"""
    X, y = [], []
    
    # STABLE: Realistic base values + noise
    for _ in range(n_per_class):
        base = [8.2, 420, 1300, 8.5, 78.0]
        if add_noise:
            noisy = [
                base[0] + np.random.normal(0, 0.15),   # pH noise
                base[1] + np.random.normal(0, 10),      # Calcium noise
                base[2] + np.random.normal(0, 30),      # Magnesium noise
                base[3] + np.random.normal(0, 0.2),      # Alkalinity noise
                base[4] + np.random.normal(0, 0.5)       # Temp noise
            ]
        else:
            noisy = base
        X.append(noisy)
        y.append(0)
    
    # WARNING: Realistic values + noise
    for _ in range(n_per_class):
        base = [7.7, 375, 1180, 7.5, 78.0]
        if add_noise:
            noisy = [
                base[0] + np.random.normal(0, 0.15),
                base[1] + np.random.normal(0, 10),
                base[2] + np.random.normal(0, 30),
                base[3] + np.random.normal(0, 0.2),
                base[4] + np.random.normal(0, 0.5)
            ]
        else:
            noisy = base
        X.append(noisy)
        y.append(1)
    
    # CRITICAL: Realistic values + noise
    for _ in range(n_per_class):
        base = [7.0, 320, 950, 6.5, 78.0]
        if add_noise:
            noisy = [
                base[0] + np.random.normal(0, 0.15),
                base[1] + np.random.normal(0, 10),
                base[2] + np.random.normal(0, 30),
                base[3] + np.random.normal(0, 0.2),
                base[4] + np.random.normal(0, 0.5)
            ]
        else:
            noisy = base
        X.append(noisy)
        y.append(2)
    
    return np.array(X), np.array(y)

def main():
    print("=" * 80)
    print("ReefGPT FULL BENCHMARK - Train on Data, Evaluate on NEW Noisey Data")
    print("=" * 80)
    print("Training: Clean synthetic data | Test: NEW data + realistic sensor noise")
    print("Metrics: Accuracy, CV, R², F1, Precision, Recall, Overfitting check")
    print()
    
    # Generate TRAINING data (clean, no noise)
    print("Generating TRAINING data (500 per class, clean)...")
    X_train, y_train = generate_train_data(500)
    print(f"  Train samples: {len(X_train)}")
    
    # Generate NEW TEST data (completely separate, with noise)
    print("Generating NEW TEST data (100 per class, with sensor noise)...")
    X_test, y_test = generate_test_data(100, add_noise=True)
    print(f"  Test samples: {len(X_test)}")
    
    # Scale data
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)
    
    print()
    print("=" * 80)
    print("TRAINING WITH HYPERPARAMETER TUNING (GridSearchCV)")
    print("=" * 80)
    print()
    
    results = {}
    
    # ========== MLP (Neural Network) ==========
    print("[1/2] Training NeuralNetwork (MLP) with GridSearchCV...")
    mlp = MLPClassifier(max_iter=2000, early_stopping=True, validation_fraction=0.1, random_state=42)
    mlp_params = {
        'hidden_layer_sizes': [(50,), (50, 25), (100, 50), (100, 50, 25)],
        'alpha': [0.0001, 0.001, 0.01, 0.1],
        'activation': ['relu', 'tanh']
    }
    mlp_grid = GridSearchCV(mlp, mlp_params, cv=5, scoring='accuracy', n_jobs=-1)
    mlp_grid.fit(X_train_s, y_train)
    
    mlp_pred = mlp_grid.best_estimator_.predict(X_test_s)
    mlp_cv = cross_val_score(mlp_grid.best_estimator_, X_train_s, y_train, cv=5, scoring='accuracy').mean()
    
    results['NeuralNetwork'] = {
        'model': mlp_grid.best_estimator_,
        'best_params': mlp_grid.best_params_,
        'cv_score': mlp_cv,
        'test_accuracy': accuracy_score(y_test, mlp_pred),
        'r2': r2_score(y_test, mlp_pred),
        'f1': f1_score(y_test, mlp_pred, average='weighted'),
        'precision': precision_score(y_test, mlp_pred, average='weighted', zero_division=0.0),
        'recall': recall_score(y_test, mlp_pred, average='weighted', zero_division=0.0),
    }
    print(f"  Best params: {mlp_grid.best_params_}")
    print(f"  CV Accuracy: {mlp_cv*100:.2f}%")
    print()
    
    # ========== XGBoost ==========
    print("[2/2] Training XGBoost with GridSearchCV...")
    xgb = XGBClassifier(random_state=42, eval_metric='mlogloss', verbosity=0)
    xgb_params = {
        'n_estimators': [50, 100, 150],
        'max_depth': [3, 5, 7],
        'learning_rate': [0.01, 0.05, 0.1],
        'min_child_weight': [1, 3, 5],
        'subsample': [0.8, 1.0]
    }
    xgb_grid = GridSearchCV(xgb, xgb_params, cv=5, scoring='accuracy', n_jobs=-1)
    xgb_grid.fit(X_train_s, y_train)
    
    xgb_pred = xgb_grid.best_estimator_.predict(X_test_s)
    xgb_cv = cross_val_score(xgb_grid.best_estimator_, X_train_s, y_train, cv=5, scoring='accuracy').mean()
    
    results['XGBoost'] = {
        'model': xgb_grid.best_estimator_,
        'best_params': xgb_grid.best_params_,
        'cv_score': xgb_cv,
        'test_accuracy': accuracy_score(y_test, xgb_pred),
        'r2': r2_score(y_test, xgb_pred),
        'f1': f1_score(y_test, xgb_pred, average='weighted'),
        'precision': precision_score(y_test, xgb_pred, average='weighted', zero_division=0.0),
        'recall': recall_score(y_test, xgb_pred, average='weighted', zero_division=0.0),
    }
    print(f"  Best params: {xgb_grid.best_params_}")
    print(f"  CV Accuracy: {xgb_cv*100:.2f}%")
    print()
    
    # ========== RESULTS TABLE ==========
    print("=" * 80)
    print("EVALUATION RESULTS (on NEW test data with sensor noise)")
    print("=" * 80)
    print()
    print(f"{'Model':<20} {'Test Acc':>10} {'CV Acc':>10} {'R²':>10} {'F1':>10} {'Precision':>12} {'Recall':>10}")
    print("-" * 100)
    
    for name, r in results.items():
        print(f"{name:<20} {r['test_accuracy']*100:>9.2f}% {r['cv_score']*100:>9.2f}% {r['r2']:>10.3f} {r['f1']*100:>9.2f}% {r['precision']*100:>11.2f}% {r['recall']*100:>9.2f}%")
    
    print()
    
    # ========== OVERFITTING CHECK ==========
    print("=" * 80)
    print("OVERFITTING ANALYSIS")
    print("=" * 80)
    for name, r in results.items():
        gap = r['cv_score'] - r['test_accuracy']
        status = "EXCELLENT" if abs(gap) < 0.05 else "GOOD" if abs(gap) < 0.10 else "ACCEPTABLE" if abs(gap) < 0.20 else "OVERFIT"
        print(f"{name:<20} CV={r['cv_score']*100:.2f}% Test={r['test_accuracy']*100:.2f}% Gap={gap*100:+.2f}% [{status}]")
    
    print()
    
    # ========== BEST MODEL ==========
    print("=" * 80)
    print("BEST MODEL (by Test Accuracy)")
    print("=" * 80)
    best = max(results.items(), key=lambda x: x[1]['test_accuracy'])
    print(f"\nBest: {best[0]}")
    print(f"  Hyperparameters: {best[1]['best_params']}")
    print(f"  Test Accuracy: {best[1]['test_accuracy']*100:.2f}%")
    print(f"  CV Accuracy: {best[1]['cv_score']*100:.2f}%")
    print(f"  R² Score: {best[1]['r2']:.3f}")
    print(f"  F1 Score: {best[1]['f1']*100:.2f}%")
    print(f"  Precision: {best[1]['precision']*100:.2f}%")
    print(f"  Recall: {best[1]['recall']*100:.2f}%")

if __name__ == '__main__':
    main()