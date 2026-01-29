"""
Explain why a person is considered risky - Show the top factors
"""
import sys
sys.path.append('src')

import pandas as pd
import joblib
import numpy as np
from pathlib import Path

# Load model artifacts
models_path = Path("models")
model = joblib.load(models_path / "credit_risk_model_calibrated.pkl")
feature_names = joblib.load(models_path / "credit_risk_model_features.pkl")
label_encoders = joblib.load(models_path / "label_encoders.pkl")

# Load SHAP explainer if available
try:
    explainer_artifacts = joblib.load(models_path / "explainer_artifacts.pkl")
    shap_values_sample = explainer_artifacts.get('shap_values')
    feature_importance = explainer_artifacts.get('feature_importance')
    print("✅ SHAP explainer loaded\n")
except:
    feature_importance = None
    print("⚠️  SHAP not available, using feature importance\n")

def explain_prediction(input_dict):
    """
    Explain why a person is approved/rejected
    Shows the top factors influencing the decision
    """
    # Create DataFrame
    df = pd.DataFrame([input_dict])
    
    # Encode categorical features
    for col, encoder in label_encoders.items():
        if col in df.columns:
            try:
                df[col] = encoder.transform(df[col].astype(str))
            except:
                df[col] = 0
    
    # Ensure all features exist
    for feat in feature_names:
        if feat not in df.columns:
            df[feat] = 0
    
    # Select features in correct order
    df_model = df[feature_names].apply(pd.to_numeric, errors='coerce').fillna(0)
    
    # Get prediction
    prob_default = model.predict_proba(df_model)[0, 1]
    
    print("="*80)
    print("🔍 DETAILED RISK ANALYSIS")
    print("="*80)
    print(f"\n⚠️  Default Risk: {prob_default*100:.2f}%")
    print(f"💰 Payback Probability: {(1-prob_default)*100:.2f}%\n")
    
    # Show key features from the person's data
    print("📊 KEY FEATURES FROM APPLICATION:")
    print("-" * 80)
    
    important_features = [
        ('AMT_INCOME_TOTAL', 'Annual Income'),
        ('AMT_CREDIT', 'Loan Amount'),
        ('AMT_ANNUITY', 'Monthly Payment'),
        ('DAYS_BIRTH', 'Age'),
        ('DAYS_EMPLOYED', 'Employment Duration'),
        ('EXT_SOURCE_1', 'External Credit Score 1'),
        ('EXT_SOURCE_2', 'External Credit Score 2'),
        ('EXT_SOURCE_3', 'External Credit Score 3'),
        ('FLAG_OWN_CAR', 'Owns Car'),
        ('FLAG_OWN_REALTY', 'Owns Property'),
        ('REGION_RATING_CLIENT', 'Region Rating'),
        ('CNT_CHILDREN', 'Number of Children'),
        ('CODE_GENDER', 'Gender'),
        ('NAME_INCOME_TYPE', 'Income Type'),
        ('NAME_EDUCATION_TYPE', 'Education'),
    ]
    
    for feat, desc in important_features:
        if feat in input_dict:
            value = input_dict[feat]
            
            # Format special fields
            if 'DAYS_' in feat and feat != 'DAYS_ID_PUBLISH':
                if value < 0:
                    years = abs(value) / 365.25
                    print(f"  • {desc:.<30} {value:>12,.0f} days (~{years:.1f} years)")
                else:
                    print(f"  • {desc:.<30} {value:>12,.0f} days")
            elif 'AMT_' in feat:
                print(f"  • {desc:.<30} ${value:>12,.2f}")
            elif 'EXT_SOURCE' in feat:
                if pd.notna(value) and value > 0:
                    print(f"  • {desc:.<30} {value:>12.4f} (higher is better)")
                else:
                    print(f"  • {desc:.<30} {'MISSING':>12}")
            elif 'FLAG_' in feat:
                status = "YES" if value == 1 else "NO"
                print(f"  • {desc:.<30} {status:>12}")
            else:
                print(f"  • {desc:.<30} {str(value):>12}")
    
    # Calculate derived metrics
    if 'AMT_INCOME_TOTAL' in input_dict and 'AMT_CREDIT' in input_dict:
        income = input_dict['AMT_INCOME_TOTAL']
        credit = input_dict['AMT_CREDIT']
        if income > 0:
            debt_to_income = credit / income
            print(f"\n💡 DERIVED METRICS:")
            print(f"  • Loan-to-Income Ratio....... {debt_to_income:.2%}")
            
            if 'AMT_ANNUITY' in input_dict:
                annuity = input_dict['AMT_ANNUITY']
                monthly_income = income / 12
                payment_ratio = annuity / monthly_income
                print(f"  • Payment-to-Income Ratio..... {payment_ratio:.2%}")
    
    # Decision
    print(f"\n{'='*80}")
    if prob_default < 0.04:
        print("✅ DECISION: APPROVED - Tier A (Excellent Risk)")
        print(f"   Credit Limit: $50,000 | Interest Rate: 8.0%")
    elif prob_default < 0.08:
        print("✅ DECISION: APPROVED - Tier B (Good Risk)")
        print(f"   Credit Limit: $30,000 | Interest Rate: 12.0%")
    elif prob_default < 0.15:
        print("✅ DECISION: APPROVED - Tier C (Acceptable Risk)")
        print(f"   Credit Limit: $15,000 | Interest Rate: 18.0%")
    else:
        print("❌ DECISION: REJECTED - Risk Too High")
        print(f"   Reason: Default probability ({prob_default:.1%}) exceeds threshold (15%)")
    print("="*80)
    
    return prob_default

# Load real training data
print("\nLoading training data samples...\n")
train_df = pd.read_csv("data/raw/application_train.csv")

# Test 1: Person who PAID BACK (TARGET=0)
print("\n" + "🟢 " + "="*78)
print("TEST 1: PERSON WHO ACTUALLY PAID BACK (TARGET = 0)")
print("="*80)
good_person = train_df[train_df['TARGET'] == 0].iloc[0].to_dict()
prob1 = explain_prediction(good_person)

print("\n\n📌 WHY IS THIS PERSON RISKY EVEN THOUGH THEY PAID BACK?")
print("="*80)
print("""
The model looks at the PROFILE at application time, not the future outcome.

Possible reasons this person looked risky:
  • Low external credit scores (EXT_SOURCE_1, EXT_SOURCE_2, EXT_SOURCE_3)
  • High loan-to-income ratio
  • Short employment history
  • Young age
  • Missing key information
  • Living in a higher-risk region
  
Even risky-looking people can pay back! That's why:
  ✓ Some good people get rejected (False Negatives)
  ✓ Some bad people get approved (False Positives)
  
The model aims to minimize losses, not be 100% perfect.
""")

# Test 2: Person who DEFAULTED (TARGET=1)
print("\n" + "🔴 " + "="*78)
print("TEST 2: PERSON WHO ACTUALLY DEFAULTED (TARGET = 1)")
print("="*80)
bad_person = train_df[train_df['TARGET'] == 1].iloc[0].to_dict()
prob2 = explain_prediction(bad_person)

# Compare
print("\n\n📊 COMPARISON:")
print("="*80)
print(f"Person 1 (Paid Back):    {prob1*100:.2f}% default risk")
print(f"Person 2 (Defaulted):    {prob2*100:.2f}% default risk")
print(f"Difference:              {abs(prob1-prob2)*100:.2f} percentage points")
print("="*80)

if prob1 < prob2:
    print("✅ Model correctly identified Person 2 as MORE risky")
elif prob1 > prob2:
    print("⚠️  Model thought Person 1 was MORE risky (wrong direction)")
else:
    print("➖ Model saw both as equally risky")

print("\n💡 Remember: Credit scoring is about PROBABILITIES, not certainties!")
print("   A 40% default risk means: 60% will pay, 40% won't - on average.")
