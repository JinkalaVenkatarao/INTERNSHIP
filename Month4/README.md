# LOAN APPROVAL ML SYSTEM

## Quick Start

### 1. Install Dependencies
```bash
pip install pandas numpy scikit-learn
```

### 2. Run the System
```bash
python loan_approval_system.py
```

### 3. Check Results
```bash
ls models/
cat models/results.json
```

## What It Does

1. **Generates** 1000 synthetic loan applications
2. **Splits** into 800 train, 200 test
3. **Engineers** 4 new features (debt ratio, savings, etc)
4. **Trains** 3 ML models:
   - Logistic Regression
   - Random Forest
   - Gradient Boosting
5. **Evaluates** on test set
6. **Saves** models to models/ folder

## Output

- models/logistic_regression.pkl
- models/random_forest.pkl
- models/gradient_boosting.pkl
- models/scaler.pkl
- models/results.json

## Features

Input: 17 features
- Age, gender, marital status
- Employment, income, expenses
- Credit score, loans
- Property details, assets

Engineered: 4 features
- Debt-to-income ratio
- Loan-to-income ratio
- Savings rate
- Net worth

## Models

| Model | Accuracy | F1 | ROC-AUC |
|-------|----------|-----|---------|
| Logistic | ~85% | ~0.67 | ~0.89 |
| Forest | ~83% | ~0.56 | ~0.88 |
| Gradient | ~85% | ~0.70 | ~0.87 |

Best: Gradient Boosting

## Performance

- Training time: ~30 seconds
- File size: 1-5 MB
- Memory: ~100 MB

## Requirements

- Python 3.7+
- pandas
- numpy
- scikit-learn

## Files Generated

After running, you'll have:
- models/ (folder with trained models)
- models/results.json (performance metrics)

That's it! Complete ML system in one file.
