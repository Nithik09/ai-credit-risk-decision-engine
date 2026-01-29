"""
Test if a single person can pay back their loan.
Simple script to make predictions for one applicant.
"""

import sys
sys.path.append('src')

import pandas as pd
import joblib
from pathlib import Path
from model.decision_engine import DecisionEngine
from loguru import logger

def test_person(person_data):
    """
    Test if a person can pay back their loan.
    
    Args:
        person_data: Dictionary with person's information
    
    Returns:
        Decision result with approval, risk score, credit limit, etc.
    """
    
    # Load the trained model
    models_path = Path("models")
    model_file = models_path / "credit_risk_model_calibrated.pkl"
    
    if not model_file.exists():
        logger.error("No trained model found! Please run: python scripts/train_model.py")
        return None
    
    logger.info(f"Loading model: {model_file}")
    
    model = joblib.load(model_file)
    
    # Load feature names and encoders
    feature_names = joblib.load(models_path / "feature_names.pkl")
    
    # Initialize decision engine
    decision_engine = DecisionEngine()
    
    # Create DataFrame from person data
    df = pd.DataFrame([person_data])
    
    # Make sure all required features exist (fill missing with 0)
    for feature in feature_names:
        if feature not in df.columns:
            df[feature] = 0
    
    # Select only the features used in training
    df = df[feature_names]
    
    # Get prediction
    risk_score = model.predict_proba(df)[0, 1]  # Probability of default
    
    # Make decision
    decision = decision_engine.make_decision(
        pd_score=risk_score,
        application_data=person_data
    )
    
    # Print results
    print("\n" + "="*70)
    print("🎯 LOAN APPLICATION RESULT")
    print("="*70)
    print(f"\n📊 Risk Score: {risk_score:.4f} ({risk_score*100:.2f}% chance of default)")
    print(f"\n✅ Decision: {decision['decision']}")
    print(f"🏷️  Risk Tier: {decision['risk_tier']}")
    
    if decision['decision'] == 'APPROVED':
        print(f"\n💰 Credit Limit: ${decision['credit_limit']:,.0f}")
        print(f"💵 Interest Rate: {decision['interest_rate']:.2f}%")
        print(f"📅 Max Term: {decision['max_term_months']} months")
        
        print(f"\n📝 Top Reasons:")
        for i, reason in enumerate(decision['reasons'][:5], 1):
            print(f"   {i}. {reason}")
    
    elif decision['decision'] == 'REJECTED':
        print(f"\n❌ Rejection Reasons:")
        for i, reason in enumerate(decision['reasons'][:5], 1):
            print(f"   {i}. {reason}")
    
    else:  # MANUAL_REVIEW
        print(f"\n⚠️  Requires Manual Review")
        print(f"📋 Review Reasons:")
        for i, reason in enumerate(decision['reasons'][:5], 1):
            print(f"   {i}. {reason}")
    
    print("\n" + "="*70 + "\n")
    
    return decision


if __name__ == "__main__":
    
    print("\n" + "="*70)
    print("💳 CREDIT RISK TESTER - Check if a Person Can Pay Back")
    print("="*70)
    
    # Example 1: Low Risk Person (should be APPROVED)
    print("\n\n🟢 TEST 1: Low Risk Applicant")
    print("-" * 70)
    
    low_risk_person = {
        'AMT_INCOME_TOTAL': 200000,        # Good income: $200k/year
        'AMT_CREDIT': 50000,               # Wants: $50k loan
        'AMT_ANNUITY': 5000,               # Monthly payment: $5k
        'AMT_GOODS_PRICE': 45000,          # Item price: $45k
        'DAYS_BIRTH': -15000,              # Age: ~41 years old
        'DAYS_EMPLOYED': -3000,            # Employed: ~8 years
        'EXT_SOURCE_1': 0.75,              # External score 1: Good
        'EXT_SOURCE_2': 0.70,              # External score 2: Good
        'EXT_SOURCE_3': 0.65,              # External score 3: Good
        'REGION_RATING_CLIENT': 1,         # Best region rating
        'FLAG_OWN_CAR': 1,                 # Owns a car
        'FLAG_OWN_REALTY': 1,              # Owns property
    }
    
    result1 = test_person(low_risk_person)
    
    
    # Example 2: High Risk Person (should be REJECTED or MANUAL_REVIEW)
    print("\n\n🔴 TEST 2: High Risk Applicant")
    print("-" * 70)
    
    high_risk_person = {
        'AMT_INCOME_TOTAL': 50000,         # Low income: $50k/year
        'AMT_CREDIT': 100000,              # Wants: $100k loan (too much!)
        'AMT_ANNUITY': 8000,               # Monthly payment: $8k (can't afford!)
        'AMT_GOODS_PRICE': 95000,          # Item price: $95k
        'DAYS_BIRTH': -8000,               # Age: ~22 years old (young)
        'DAYS_EMPLOYED': -365,             # Employed: ~1 year only
        'EXT_SOURCE_1': 0.20,              # External score 1: Poor
        'EXT_SOURCE_2': 0.15,              # External score 2: Poor
        'EXT_SOURCE_3': 0.25,              # External score 3: Poor
        'REGION_RATING_CLIENT': 3,         # Worst region rating
        'FLAG_OWN_CAR': 0,                 # No car
        'FLAG_OWN_REALTY': 0,              # No property
    }
    
    result2 = test_person(high_risk_person)
    
    
    # Example 3: Medium Risk Person (borderline)
    print("\n\n🟡 TEST 3: Medium Risk Applicant")
    print("-" * 70)
    
    medium_risk_person = {
        'AMT_INCOME_TOTAL': 100000,        # Average income: $100k/year
        'AMT_CREDIT': 60000,               # Wants: $60k loan
        'AMT_ANNUITY': 6000,               # Monthly payment: $6k
        'AMT_GOODS_PRICE': 55000,          # Item price: $55k
        'DAYS_BIRTH': -12000,              # Age: ~33 years old
        'DAYS_EMPLOYED': -1500,            # Employed: ~4 years
        'EXT_SOURCE_1': 0.50,              # External score 1: Average
        'EXT_SOURCE_2': 0.45,              # External score 2: Average
        'EXT_SOURCE_3': 0.48,              # External score 3: Average
        'REGION_RATING_CLIENT': 2,         # Medium region rating
        'FLAG_OWN_CAR': 1,                 # Owns a car
        'FLAG_OWN_REALTY': 0,              # No property
    }
    
    result3 = test_person(medium_risk_person)
    
    
    print("\n✅ Testing complete! Try your own values by editing this file.\n")
