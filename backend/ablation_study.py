import numpy as np
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# 1. Generate data with Base + Velocity features (10 columns total)
def generate_ablation_data(n_per_class=250):
    np.random.seed(42)
    X, y = [], []
    
    # Class 0: Stable (Good raw numbers, near-zero velocity)
    for _ in range(n_per_class):
        base = [np.random.uniform(7.5, 9.5), np.random.uniform(400, 450), 
                np.random.uniform(1250, 1450), np.random.uniform(8.0, 8.4), np.random.uniform(76, 80)]
        vel = [np.random.uniform(-0.1, 0.1) for _ in range(5)]
        X.append(base + vel)
        y.append(0)
        
    # Class 1: Warning (Slightly off numbers, moderate velocity)
    for _ in range(n_per_class):
        base = [np.random.uniform(6.5, 10.5), np.random.uniform(350, 500), 
                np.random.uniform(1100, 1500), np.random.uniform(7.6, 8.6), np.random.uniform(72, 84)]
        vel = [np.random.uniform(-0.5, 0.5) for _ in range(5)]
        X.append(base + vel)
        y.append(1)
        
    # Class 2: Critical (Bad numbers, high velocity)
    for _ in range(n_per_class):
        base = [np.random.uniform(5.0, 12.0), np.random.uniform(250, 550), 
                np.random.uniform(900, 1700), np.random.uniform(7.0, 9.0), np.random.uniform(68, 88)]
        vel = [np.random.choice([np.random.uniform(-1.5, -0.5), np.random.uniform(0.5, 1.5)]) for _ in range(5)]
        X.append(base + vel)
        y.append(2)
        
    return np.array(X), np.array(y)

X, y = generate_ablation_data()
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# 2. Define Ablation Scenarios (Column Indices)
# Cols 0-4: Alk, Ca, Mg, pH, Temp | Cols 5-9: Alk_Vel, Ca_Vel, Mg_Vel, pH_Vel, Temp_Vel
scenarios = {
    "Baseline (All Features)": list(range(10)),
    "Ablation 1: No Velocity/Variance": [0, 1, 2, 3, 4],
    "Ablation 2: No Calcium or Magnesium": [0, 3, 4, 5, 8, 9], # Alk, pH, Temp + their velocities
    "Ablation 3: Core Only (Alk & pH Static)": [0, 3] # Only static Alk and pH
}

results = []

# 3. Run Training Loop
for name, features in scenarios.items():
    X_train_sub = StandardScaler().fit_transform(X_train[:, features])
    X_test_sub = StandardScaler().fit_transform(X_test[:, features])
    
    xgb = XGBClassifier(n_estimators=30, max_depth=2, random_state=42, verbosity=0)
    xgb.fit(X_train_sub, y_train)
    preds = xgb.predict(X_test_sub)
    
    acc = accuracy_score(y_test, preds)
    f1 = f1_score(y_test, preds, average='weighted')
    results.append((name, len(features), acc, f1))

# 4. Generate LaTeX Output
print("\n--- COPY AND PASTE INTO YOUR IEEE REPORT ---")
print("\\begin{table}[htbp]")
print("\\caption{Ablation Study: XGBoost Feature Importance}")
print("\\begin{center}")
print("\\begin{tabular}{|l|c|c|c|}")
print("\\hline")
print("\\textbf{Model Setup} & \\textbf{Feature Count} & \\textbf{Accuracy} & \\textbf{F1-Score} \\\\")
print("\\hline")

baseline_acc = results[0][2]
for name, count, acc, f1 in results:
    drop = "" if name == "Baseline (All Features)" else f" (-{(baseline_acc - acc)*100:.1f}\\%)"
    print(f"{name} & {count} & {acc*100:.1f}\\%{drop} & {f1:.3f} \\\\")

print("\\hline")
print("\\end{tabular}")
print("\\label{tab:ablation}")
print("\\end{center}")
print("\\end{table}")