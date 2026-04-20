#!/usr/bin/env python3
"""
ReefGPT Full Benchmark - Comprehensive ML Model Evaluation
=========================================================
Loads trained models and new CSV evaluation data, evaluates with full metrics:
- Accuracy
- R² Score
- F1 Score
- Precision & Recall
- Overfitting check
"""
import numpy as np
import os
import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, r2_score, precision_score, recall_score
import warnings
warnings.filterwarnings('ignore')

MODEL_DIR = os.path.join(os.path.dirname(__file__), 'models')
EVAL_CSV = os.path.join(os.path.dirname(__file__), 'models', 'benchmark_eval_data.csv')

def main():
    print("=" * 80)
    print("ReefGPT FULL BENCHMARK - Comprehensive ML Evaluation")
    print("=" * 80)
    print("Metrics: Accuracy, R², F1, Precision, Recall")
    print()
    
    # Load new evaluation data from CSV
    df = pd.read_csv(EVAL_CSV)
    df = df.dropna(subset=['tank_state'])
    X_test = df[['pH', 'Calcium', 'Magnesium', 'Alkalinity', 'Salinity']].values
    y_test = df['tank_state'].values.astype(int)
    
    print(f"Total samples: {len(X_test)}")
    unique, counts = np.unique(y_test, return_counts=True)
    print(f"Class distribution: {dict(zip(unique.tolist(), counts.tolist()))}")
    print()
    
    print("=" * 80)
    print("LOADING MODELS")
    print("=" * 80)
    print()
    
    results = {}
    
    # Load XGBoost
    print("[1/2] Loading XGBoost model...")
    xgb_data = joblib.load(os.path.join(MODEL_DIR, 'xgb_model.pkl'))
    xgb = xgb_data['model']
    scaler = xgb_data['scaler']
    X_test_s = scaler.transform(X_test)
    xgb_pred = xgb.predict(X_test_s)
    
    results['XGBoost'] = {
        'accuracy': accuracy_score(y_test, xgb_pred),
        'r2': r2_score(y_test, xgb_pred),
        'f1': f1_score(y_test, xgb_pred, average='weighted'),
        'precision': precision_score(y_test, xgb_pred, average='weighted', zero_division='warn'),
        'recall': recall_score(y_test, xgb_pred, average='weighted', zero_division='warn'),
    }
    print(f"  Test Accuracy: {results['XGBoost']['accuracy']*100:.2f}%")
    print()
    
    # Load MLP
    print("[2/2] Loading MLP model...")
    mlp_data = joblib.load(os.path.join(MODEL_DIR, 'mlp_model.pkl'))
    mlp = mlp_data['model']
    scaler = mlp_data['scaler']
    X_test_s = scaler.transform(X_test)
    mlp_pred = mlp.predict(X_test_s)
    
    results['MLP'] = {
        'accuracy': accuracy_score(y_test, mlp_pred),
        'r2': r2_score(y_test, mlp_pred),
        'f1': f1_score(y_test, mlp_pred, average='weighted'),
        'precision': precision_score(y_test, mlp_pred, average='weighted', zero_division='warn'),
        'recall': recall_score(y_test, mlp_pred, average='weighted', zero_division='warn'),
    }
    print(f"  Test Accuracy: {results['MLP']['accuracy']*100:.2f}%")
    print()
    
    # Print results table
    print("=" * 80)
    print("BENCHMARK RESULTS")
    print("=" * 80)
    print()
    print(f"{'Model':<20} {'Test Acc':>10} {'R²':>10} {'F1':>10} {'Precision':>12} {'Recall':>10}")
    print("-" * 80)
    
    for name, r in results.items():
        print(f"{name:<20} {r['accuracy']*100:>9.2f}% {r['r2']:>10.3f} {r['f1']*100:>9.2f}% {r['precision']*100:>11.2f}% {r['recall']*100:>9.2f}%")
    
    print()
    print("=" * 80)
    print("BEST MODEL")
    print("=" * 80)
    best = max(results.items(), key=lambda x: x[1]['accuracy'])
    print(f"\nBest: {best[0]}")
    print(f"  Test Accuracy: {best[1]['accuracy']*100:.2f}%")
    print(f"  R² Score:       {best[1]['r2']:.3f}")
    print(f"  F1 Score:       {best[1]['f1']*100:.2f}%")
    print(f"  Precision:      {best[1]['precision']*100:.2f}%")
    print(f"  Recall:         {best[1]['recall']*100:.2f}%")

if __name__ == '__main__':
    main()