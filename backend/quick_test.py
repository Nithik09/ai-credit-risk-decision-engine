"""
Simple test script - Check if a person can pay back their loan
"""
import sys
sys.path.append('src')

import pandas as pd
import joblib
from pathlib import Path
from loguru import logger

# Load model and feature information
models_path = Path("models")
model = joblib.load(models_path / "credit_risk_model_calibrated.pkl")
feature_names = joblib.load(models_path / "credit_risk_model_features.pkl")  # This has the 80 actual features!
scaler = joblib.load(models_path / "scaler.pkl")
label_encoders = joblib.load(models_path / "label_encoders.pkl")

print(f"\n✅ Model loaded successfully!")
print(f"📊 Model expects {len(feature_names)} features")

def predict_payback(input_dict):
    """
    Predict if a person will pay back.
    
    Args:
        input_dict: Dictionary with person's data
        
    Returns:
        Probability of default and decision
    """
    # Create DataFrame
    df = pd.DataFrame([input_dict])
    
    # Encode categorical features
    for col, encoder in label_encoders.items():
        if col in df.columns:
            try:
                df[col] = encoder.transform(df[col].astype(str))
            except:
                df[col] = 0  # Unknown category
    
    # Ensure all features exist
    for feat in feature_names:
        if feat not in df.columns:
            df[feat] = 0  # Fill missing with 0
    
    # Select only needed features in correct order
    df = df[feature_names]
    
    # Convert to numeric
    df = df.apply(pd.to_numeric, errors='coerce').fillna(0)
    
    # Predict
    prob_default = model.predict_proba(df)[0, 1]
    prob_payback = 1 - prob_default
    
    # Decision logic
    if prob_default < 0.04:
        decision = "✅ APPROVED - Tier A (Excellent)"
        limit = 50000
        rate = 8.0
    elif prob_default < 0.08:
        decision = "✅ APPROVED - Tier B (Good)"
        limit = 30000
        rate = 12.0
    elif prob_default < 0.15:
        decision = "✅ APPROVED - Tier C (Fair)"
        limit = 15000
        rate = 18.0
    else:
        decision = "❌ REJECTED - Too Risky"
        limit = 0
        rate = 0
    
    return {
        'prob_default': prob_default,
        'prob_payback': prob_payback,
        'decision': decision,
        'credit_limit': limit,
        'interest_rate': rate
    }

# Load a real example from training data to test
print("Loading a real sample from training data...\n")
train_df = pd.read_csv("data/raw/application_train.csv")

# Test with a person who DID pay back (TARGET=0)
good_person = train_df[train_df['TARGET'] == 0].iloc[0].to_dict()
print("="*70)
print("🟢 TEST 1: Person who PAID BACK in real data")
print("="*70)
result = predict_payback(good_person)
print(f"💰 Probability will PAY BACK: {result['prob_payback']*100:.2f}%")
print(f"⚠️  Probability will DEFAULT: {result['prob_default']*100:.2f}%")
print(f"📋 Decision: {result['decision']}")
if result['credit_limit'] > 0:
    print(f"💵 Credit Limit: ${result['credit_limit']:,}")
    print(f"📊 Interest Rate: {result['interest_rate']}%")
print()

# Test with a person who DIDN'T pay back (TARGET=1)
bad_person = train_df[train_df['TARGET'] == 1].iloc[0].to_dict()
print("="*70)
print("🔴 TEST 2: Person who DEFAULTED in real data")
print("="*70)
result = predict_payback(bad_person)
print(f"💰 Probability will PAY BACK: {result['prob_payback']*100:.2f}%")
print(f"⚠️  Probability will DEFAULT: {result['prob_default']*100:.2f}%")
print(f"📋 Decision: {result['decision']}")
if result['credit_limit'] > 0:
    print(f"💵 Credit Limit: ${result['credit_limit']:,}")
    print(f"📊 Interest Rate: {result['interest_rate']}%")
print()

#  Test with average person
avg_person = train_df.iloc[1000].to_dict()
print("="*70)
print("🟡 TEST 3: Random Person from Dataset")
print("="*70)
result = predict_payback(avg_person)
print(f"💰 Probability will PAY BACK: {result['prob_payback']*100:.2f}%")
print(f"⚠️  Probability will DEFAULT: {result['prob_default']*100:.2f}%")
print(f"📋 Decision: {result['decision']}")
if result['credit_limit'] > 0:
    print(f"💵 Credit Limit: ${result['credit_limit']:,}")
    print(f"📊 Interest Rate: {result['interest_rate']}%")
print()

print("="*70)
print("✅ Demo Complete!")
print("="*70)
print("\n💡 To test YOUR OWN person, modify the dictionary and call:")
print("   result = predict_payback(your_data_dict)")
print()
