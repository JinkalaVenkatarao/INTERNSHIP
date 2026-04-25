#!/usr/bin/env python3
"""
LOAN APPROVAL ML SYSTEM
Complete machine learning pipeline for loan approval prediction
"""

import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import pickle
import json

print("\n" + "="*80)
print("LOAN APPROVAL ML SYSTEM")
print("="*80)

# Step 1: Generate Data
print("\n[STEP 1] Generating synthetic data...")
np.random.seed(42)
n = 1000
df = pd.DataFrame({
    'age': np.random.normal(35, 12, n).astype(int).clip(18, 80),
    'gender': np.random.choice([0, 1], n),
    'marital_status': np.random.choice([0, 1, 2], n),
    'dependents': np.random.poisson(1, n),
    'years_employed': np.random.exponential(5, n).astype(int),
    'employment_type': np.random.choice([0, 1, 2], n),
    'monthly_income': np.random.lognormal(10.5, 0.8, n).astype(int),
    'monthly_expenses': np.random.lognormal(9.8, 0.7, n).astype(int),
    'credit_score': np.random.normal(650, 80, n).astype(int).clip(300, 850),
    'existing_loans': np.random.poisson(1.5, n),
    'loan_amount': np.random.lognormal(11.5, 1.2, n).astype(int),
    'loan_term_months': np.random.choice([12, 24, 36, 48, 60], n),
    'loan_purpose': np.random.choice([0, 1, 2], n),
    'property_value': np.random.lognormal(12, 1.3, n).astype(int),
    'property_type': np.random.choice([0, 1, 2], n),
    'total_assets': np.random.lognormal(11.8, 1.1, n).astype(int),
    'total_liabilities': np.random.lognormal(10.5, 1.2, n).astype(int),
})

# Create approval label
df['approval'] = (((df['credit_score']-300)/550)*0.3 + (1-df['monthly_expenses']/df['monthly_income']).clip(0,1)*0.3 + (df['years_employed']/20).clip(0,1)*0.4 + np.random.normal(0, 0.1, n) > 0.5).astype(int)

print(f"✓ Generated {len(df)} samples")

# Step 2: Preprocess
print("\n[STEP 2] Preprocessing data...")
X = df.drop('approval', axis=1)
y = df['approval']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Feature engineering
for data in [X_train, X_test]:
    data['debt_to_income'] = data['monthly_expenses'] / (data['monthly_income'] + 1)
    data['loan_to_income'] = (data['loan_amount']/12) / (data['monthly_income'] + 1)
    data['savings_rate'] = (data['monthly_income'] - data['monthly_expenses']) / (data['monthly_income'] + 1)
    data['net_worth'] = data['total_assets'] - data['total_liabilities']

print(f"✓ Train: {len(X_train)}, Test: {len(X_test)}, Features: {X_train.shape[1]}")

# Step 3: Train Models
print("\n[STEP 3] Training models...")
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

results = {}

# Logistic Regression
print("  • Training Logistic Regression...")
lr = LogisticRegression(max_iter=1000, random_state=42)
lr.fit(X_train_scaled, y_train)
pred = lr.predict(X_test_scaled)
results['logistic_regression'] = {
    'accuracy': accuracy_score(y_test, pred),
    'precision': precision_score(y_test, pred),
    'recall': recall_score(y_test, pred),
    'f1': f1_score(y_test, pred),
    'roc_auc': roc_auc_score(y_test, lr.predict_proba(X_test_scaled)[:,1])
}

# Random Forest
print("  • Training Random Forest...")
rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
rf.fit(X_train, y_train)
pred = rf.predict(X_test)
results['random_forest'] = {
    'accuracy': accuracy_score(y_test, pred),
    'precision': precision_score(y_test, pred),
    'recall': recall_score(y_test, pred),
    'f1': f1_score(y_test, pred),
    'roc_auc': roc_auc_score(y_test, rf.predict_proba(X_test)[:,1])
}

# Gradient Boosting
print("  • Training Gradient Boosting...")
gb = GradientBoostingClassifier(n_estimators=100, random_state=42)
gb.fit(X_train, y_train)
pred = gb.predict(X_test)
results['gradient_boosting'] = {
    'accuracy': accuracy_score(y_test, pred),
    'precision': precision_score(y_test, pred),
    'recall': recall_score(y_test, pred),
    'f1': f1_score(y_test, pred),
    'roc_auc': roc_auc_score(y_test, gb.predict_proba(X_test)[:,1])
}

print("✓ Models trained")

# Step 4: Save Models
print("\n[STEP 4] Saving models...")
os.makedirs('models', exist_ok=True)
pickle.dump(lr, open('models/logistic_regression.pkl', 'wb'))
pickle.dump(rf, open('models/random_forest.pkl', 'wb'))
pickle.dump(gb, open('models/gradient_boosting.pkl', 'wb'))
pickle.dump(scaler, open('models/scaler.pkl', 'wb'))
json.dump(results, open('models/results.json', 'w'), indent=2)
print("✓ Models saved to models/")

# Step 5: Display Results
print("\n" + "="*80)
print("RESULTS")
print("="*80)
for model, metrics in results.items():
    print(f"\n{model}:")
    print(f"  Accuracy:  {metrics['accuracy']:.4f}")
    print(f"  Precision: {metrics['precision']:.4f}")
    print(f"  Recall:    {metrics['recall']:.4f}")
    print(f"  F1-Score:  {metrics['f1']:.4f}")
    print(f"  ROC-AUC:   {metrics['roc_auc']:.4f}")

best = max(results, key=lambda x: results[x]['accuracy'])
print(f"\nBEST MODEL: {best.upper()} ({results[best]['accuracy']:.4f})")
print("="*80)

print("\n✅ COMPLETE! Check models/ folder for trained models.")
print("\nTo view results:")
print("  Windows: type models\\results.json")
print("  Mac/Linux: cat models/results.json")

# cd month4
# python loan_approval_system.py