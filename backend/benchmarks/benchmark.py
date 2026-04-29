#!/usr/bin/env python3
"""
Loads trained models and new CSV evaluation data, evaluates with metrics.
"""
import numpy as np
import os
import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, r2_score, precision_score, recall_score
import warnings
warnings.filterwarnings('ignore')

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
EVAL_CSV = os.path.join(os.path.dirname(__file__), '..', 'models', 'benchmark_eval_data.csv')

def main():
    print("=" * 70)
    print("ReefGPT ML BENCHMARK - MODEL EVALUATION")
    print("=" * 70)
    print()
    
    # Load new evaluation data from CSV
    df = pd.read_csv(EVAL_CSV)
    df = df.dropna(subset=['tank_state'])
    X_eval = df[['pH', 'Calcium', 'Magnesium', 'Alkalinity', 'Salinity']].values
    y_eval = df['tank_state'].values.astype(int)
    
    print(f"Evaluation samples: {len(X_eval)}")
    unique, counts = np.unique(y_eval, return_counts=True)
    print(f"Class distribution: {dict(zip(unique.tolist(), counts.tolist()))}")
    print()
    
    # Load models
    print("=" * 70)
    print("LOADING MODELS")
    print("=" * 70)
    
    results = {}
    
    # Load XGBoost
    xgb_data = joblib.load(os.path.join(MODEL_DIR, 'xgb_model.pkl'))
    xgb = xgb_data['model']
    scaler = xgb_data['scaler']
    X_eval_s = scaler.transform(X_eval)
    xgb_pred = xgb.predict(X_eval_s)
    results['XGBoost'] = {
        'eval_acc': accuracy_score(y_eval, xgb_pred),
        'r2': r2_score(y_eval, xgb_pred),
        'f1': f1_score(y_eval, xgb_pred, average='weighted', zero_division='warn'),
        'prec': precision_score(y_eval, xgb_pred, average='weighted', zero_division='warn'),
        'rec': recall_score(y_eval, xgb_pred, average='weighted', zero_division='warn'),
    }
    print(f"Loaded XGBoost model")
    print(f"  Eval Accuracy: {results['XGBoost']['eval_acc']*100:.1f}%")
    
    # Load MLP
    mlp_data = joblib.load(os.path.join(MODEL_DIR, 'mlp_model.pkl'))
    mlp = mlp_data['model']
    scaler = mlp_data['scaler']
    X_eval_s = scaler.transform(X_eval)
    mlp_pred = mlp.predict(X_eval_s)
    results['MLP'] = {
        'eval_acc': accuracy_score(y_eval, mlp_pred),
        'r2': r2_score(y_eval, mlp_pred),
        'f1': f1_score(y_eval, mlp_pred, average='weighted', zero_division='warn'),
        'prec': precision_score(y_eval, mlp_pred, average='weighted', zero_division='warn'),
        'rec': recall_score(y_eval, mlp_pred, average='weighted', zero_division='warn'),
    }
    print(f"Loaded MLP model")
    print(f"  Eval Accuracy: {results['MLP']['eval_acc']*100:.1f}%")
    
    print("\n" + "=" * 70)
    print("EVALUATION RESULTS")
    print("=" * 70)
    print(f"\n{'Model':<18} {'Eval':>8} {'R2':>8} {'F1':>8} {'Prec':>8} {'Rec':>8}")
    print("-" * 70)
    
    for name, r in results.items():
        print(f"{name:<18} {r['eval_acc']*100:>7.1f}% {r['r2']:>8.3f} {r['f1']*100:>7.1f}% {r['prec']*100:>7.1f}% {r['rec']*100:>7.1f}%")
    
    print("\n" + "=" * 70)
    print("BEST MODEL")
    print("=" * 70)
    best = max(results.items(), key=lambda x: x[1]['eval_acc'])
    print(f"\nBest: {best[0]}")
    print(f"  Eval Accuracy: {best[1]['eval_acc']*100:.1f}%")
    print(f"  R2:             {best[1]['r2']:.3f}")
    print(f"  F1 Score:       {best[1]['f1']*100:.1f}%")

if __name__ == '__main__':
    main()