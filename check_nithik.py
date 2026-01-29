"""
Check loan application for: Nithik Roshan
"""
import sys
sys.path.append('src')

import pandas as pd
import joblib
from pathlib import Path

# Load model
models_path = Path("models")
model = joblib.load(models_path / "credit_risk_model_calibrated.pkl")
feature_names = joblib.load(models_path / "credit_risk_model_features.pkl")
label_encoders = joblib.load(models_path / "label_encoders.pkl")

def check_loan(app_data):
    """Check if loan will be approved"""
    df = pd.DataFrame([app_data])
    
    # Encode categorical
    for col, encoder in label_encoders.items():
        if col in df.columns:
            try:
                df[col] = encoder.transform(df[col].astype(str))
            except:
                df[col] = 0
    
    # Add missing features
    for feat in feature_names:
        if feat not in df.columns:
            df[feat] = 0
    
    df_model = df[feature_names].apply(pd.to_numeric, errors='coerce').fillna(0)
    prob_default = model.predict_proba(df_model)[0, 1]
    
    return prob_default

# ============================================================================
# NITHIK ROSHAN'S APPLICATION
# ============================================================================

nithik_application = {
    # Basic Info
    'AMT_INCOME_TOTAL': 375000,       # Annual income: ₹375,000 (~$4,500/year)
    'AMT_CREDIT': 250000,             # Loan requested: ₹250,000 (REDUCED - using savings!)
    'AMT_ANNUITY': 21000,             # Monthly payment (250k over 12 months)
    'AMT_GOODS_PRICE': 500000,        # Total purchase: ₹500,000
    'DAYS_BIRTH': -(24 * 365),        # Age: 24 years = -8,760 days
    'DAYS_EMPLOYED': -(2 * 365),      # Assumed 2 years employment
    'CODE_GENDER': 'M',               # Male
    'FLAG_OWN_CAR': 'N',              # Assumed no car mentioned
    'FLAG_OWN_REALTY': 'N',           # Assumed no property mentioned
    
    # Credit scores - "good credit" = high scores
    'EXT_SOURCE_1': 0.80,             # Good credit score + HIGH SAVINGS = better score
    'EXT_SOURCE_2': 0.78,             # Good credit score + financial discipline
    'EXT_SOURCE_3': 0.75,             # Good credit score + proven savings ability
    
    # Additional info (estimated)
    'CNT_CHILDREN': 0,
    'CNT_FAM_MEMBERS': 1,
    'NAME_EDUCATION_TYPE': 'Higher education',
    'NAME_INCOME_TYPE': 'Working',
    'NAME_FAMILY_STATUS': 'Single',
    'FLAG_WORK_PHONE': 1,
    'FLAG_CONT_MOBILE': 1,
    'FLAG_EMAIL': 1,
}

print("\n" + "="*80)
print("💳 LOAN APPLICATION REVIEW")
print("="*80)

print("\n👤 APPLICANT DETAILS:")
print(f"   Name: Nithik Roshan")
print(f"   Age: 24 years")
print(f"   Annual Income: ₹{nithik_application['AMT_INCOME_TOTAL']:,} ($~{nithik_application['AMT_INCOME_TOTAL']/83:,.0f})")
print(f"   💰 Savings Available: ₹500,000 (Down Payment)")
print(f"   Total Purchase: ₹500,000")
print(f"   Down Payment: ₹250,000 (50%)")
print(f"   Loan Requested: ₹{nithik_application['AMT_CREDIT']:,} ($~{nithik_application['AMT_CREDIT']/83:,.0f})")
print(f"   Credit Score: Excellent (0.80/1.0 - boosted by savings)")

# Calculate ratios
income = nithik_application['AMT_INCOME_TOTAL']
credit = nithik_application['AMT_CREDIT']
annuity = nithik_application['AMT_ANNUITY']

loan_to_income = credit / income * 100
monthly_income = income / 12
payment_to_income = annuity / monthly_income * 100

print(f"\n📊 KEY METRICS:")
print(f"   • Monthly Income: ₹{monthly_income:,.0f}")
print(f"   • Proposed Monthly Payment: ₹{annuity:,.0f}")
print(f"   • Loan-to-Income Ratio: {loan_to_income:.1f}%")
print(f"   • Payment-to-Income Ratio: {payment_to_income:.1f}%")

# Get prediction
prob_default = check_loan(nithik_application)
prob_payback = 1 - prob_default

print(f"\n🎯 RISK ASSESSMENT:")
print(f"   • Default Risk: {prob_default*100:.2f}%")
print(f"   • Payback Probability: {prob_payback*100:.2f}%")

# Decision
print("\n" + "="*80)
if prob_default < 0.04:
    print("✅ LOAN APPROVED - Tier A (Excellent Credit)")
    print("="*80)
    print(f"   Credit Limit: ₹1,000,000 (~$12,000)")
    print(f"   Interest Rate: 8.0% per annum")
    print(f"   Max Loan Term: 120 months (10 years)")
    print(f"\n   🎉 Congratulations Nithik! You qualify for our best rates!")
    
elif prob_default < 0.08:
    print("✅ LOAN APPROVED - Tier B (Good Credit)")
    print("="*80)
    print(f"   Credit Limit: ₹750,000 (~$9,000)")
    print(f"   Interest Rate: 12.0% per annum")
    print(f"   Max Loan Term: 84 months (7 years)")
    print(f"\n   👍 Good news Nithik! Your loan is approved with standard terms.")
    
elif prob_default < 0.15:
    print("✅ LOAN APPROVED - Tier C (Fair Credit)")
    print("="*80)
    print(f"   Credit Limit: ₹400,000 (~$4,800)")
    print(f"   Interest Rate: 18.0% per annum")
    print(f"   Max Loan Term: 60 months (5 years)")
    print(f"\n   ⚠️  Nithik, your loan is approved but at higher interest due to risk factors:")
    print(f"      • Loan amount (₹500k) exceeds income (₹375k)")
    print(f"      • Monthly payment (₹42k) exceeds monthly income (₹31k)")
    print(f"\n   💡 RECOMMENDATION: Consider reducing loan to ₹300,000 for better approval")
    
else:
    print("❌ LOAN APPLICATION REJECTED")
    print("="*80)
    print(f"   Reason: Default risk ({prob_default:.1%}) exceeds acceptable threshold (15%)")
    print(f"\n   ⚠️  Sorry Nithik, we cannot approve this loan due to:")
    if loan_to_income > 100:
        print(f"      ✗ Loan-to-Income Ratio too high: {loan_to_income:.0f}%")
        print(f"        (You're requesting {loan_to_income:.0f}% of your annual income)")
    if payment_to_income > 40:
        print(f"      ✗ Payment-to-Income Ratio too high: {payment_to_income:.0f}%")
        print(f"        (Monthly payment is {payment_to_income:.0f}% of monthly income)")
    if nithik_application['DAYS_BIRTH'] > -9125:  # Less than 25 years
        print(f"      ✗ Young age (24 years) - limited credit history")
    
    print(f"\n   💡 HOW TO GET APPROVED:")
    print(f"      1. Request smaller loan: ₹200,000 - ₹300,000")
    print(f"      2. Increase down payment to reduce loan amount")
    print(f"      3. Add a co-signer with stable income")
    print(f"      4. Wait 1-2 years to build more credit history")
    print(f"      5. Increase your income before reapplying")

print("="*80)

# Analysis
print(f"\n📋 DETAILED ANALYSIS:")
print(f"   STRENGTHS:")
print(f"      ✓✓✓ EXCELLENT: ₹500,000 savings shows financial discipline!")
print(f"      ✓✓✓ 50% down payment significantly reduces risk")
print(f"      ✓ Good credit scores (0.75-0.80)")
print(f"      ✓ Decent income for age 24")
print(f"      ✓ Loan-to-income ratio now manageable at {loan_to_income:.0f}%")

print(f"\n   MINIMAL CONCERNS:")
if nithik_application['DAYS_BIRTH'] > -9125:
    print(f"      ⚠ Young age (24) - but savings prove maturity")
if nithik_application['FLAG_OWN_CAR'] == 'N' and nithik_application['FLAG_OWN_REALTY'] == 'N':
    print(f"      ⚠ No assets yet - but ₹500k savings is equivalent collateral")

print("\n" + "="*80 + "\n")
