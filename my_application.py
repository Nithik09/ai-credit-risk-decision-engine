"""
SUBMIT YOUR OWN APPLICATION - Simple Template
Just fill in your information below and run this script!
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

def check_loan_application(app_data):
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
# 👇 EDIT YOUR INFORMATION HERE 👇
# ============================================================================

YOUR_APPLICATION = {
    # ========== BASIC INFO (REQUIRED) ==========
    'AMT_INCOME_TOTAL': 80000,        # Your annual income ($)
    'AMT_CREDIT': 30000,              # Loan amount you want ($)
    'AMT_ANNUITY': 2500,              # Monthly payment you can afford ($)
    'DAYS_BIRTH': -11000,             # Your age in days (30 years = -10950)
    'DAYS_EMPLOYED': -1500,           # Employment duration in days (4 years = -1460)
    'CODE_GENDER': 'M',               # M or F
    'FLAG_OWN_CAR': 'Y',              # Y or N
    'FLAG_OWN_REALTY': 'Y',           # Y or N
    
    # ========== CREDIT SCORES (If you have them) ==========
    'EXT_SOURCE_1': 0.65,             # Credit score 1 (0-1, higher is better)
    'EXT_SOURCE_2': 0.60,             # Credit score 2 (0-1, higher is better)
    'EXT_SOURCE_3': 0.55,             # Credit score 3 (0-1, higher is better)
    
    # ========== ADDITIONAL INFO (Optional but helps) ==========
    'CNT_CHILDREN': 0,                # Number of children
    'CNT_FAM_MEMBERS': 2,             # Family size
    'NAME_EDUCATION_TYPE': 'Higher education',  # Education level
    'NAME_INCOME_TYPE': 'Working',    # Working/Pensioner/State servant/Commercial
    'NAME_FAMILY_STATUS': 'Married',  # Married/Single/etc
    'OWN_CAR_AGE': 3,                 # Age of car (if you own one)
    'FLAG_WORK_PHONE': 1,             # 1=Yes, 0=No
    'FLAG_CONT_MOBILE': 1,            # 1=Yes, 0=No
    'FLAG_EMAIL': 1,                  # 1=Yes, 0=No
}

# ============================================================================
# 🚀 RUN THE PREDICTION
# ============================================================================

print("\n" + "="*80)
print("💳 LOAN APPLICATION RESULT")
print("="*80)

# Show what you entered
print("\n📋 YOUR APPLICATION:")
print(f"   • Annual Income: ${YOUR_APPLICATION['AMT_INCOME_TOTAL']:,}")
print(f"   • Loan Requested: ${YOUR_APPLICATION['AMT_CREDIT']:,}")
print(f"   • Monthly Payment: ${YOUR_APPLICATION['AMT_ANNUITY']:,}")
print(f"   • Age: {abs(YOUR_APPLICATION['DAYS_BIRTH'])/365:.1f} years")
print(f"   • Employment: {abs(YOUR_APPLICATION['DAYS_EMPLOYED'])/365:.1f} years")
print(f"   • Gender: {YOUR_APPLICATION['CODE_GENDER']}")
print(f"   • Owns Car: {YOUR_APPLICATION['FLAG_OWN_CAR']}")
print(f"   • Owns Property: {YOUR_APPLICATION['FLAG_OWN_REALTY']}")

# Calculate key ratios
income = YOUR_APPLICATION['AMT_INCOME_TOTAL']
credit = YOUR_APPLICATION['AMT_CREDIT']
annuity = YOUR_APPLICATION['AMT_ANNUITY']

loan_to_income = credit / income * 100
monthly_income = income / 12
payment_to_income = annuity / monthly_income * 100

print(f"\n📊 KEY RATIOS:")
print(f"   • Loan-to-Income: {loan_to_income:.1f}%")
print(f"   • Payment-to-Income: {payment_to_income:.1f}%")

# Get prediction
prob_default = check_loan_application(YOUR_APPLICATION)
prob_payback = 1 - prob_default

print(f"\n🎯 CREDIT RISK ASSESSMENT:")
print(f"   • Default Risk: {prob_default*100:.2f}%")
print(f"   • Payback Probability: {prob_payback*100:.2f}%")

# Decision
print("\n" + "="*80)
if prob_default < 0.04:
    print("✅ APPROVED - Tier A (Excellent Credit)")
    print("   Credit Limit: $50,000")
    print("   Interest Rate: 8.0%")
    print("   Max Term: 120 months")
    print("\n   🎉 Congratulations! You qualify for our best rates!")
    
elif prob_default < 0.08:
    print("✅ APPROVED - Tier B (Good Credit)")
    print("   Credit Limit: $30,000")
    print("   Interest Rate: 12.0%")
    print("   Max Term: 84 months")
    print("\n   👍 Good credit profile! Approved with standard terms.")
    
elif prob_default < 0.15:
    print("✅ APPROVED - Tier C (Fair Credit)")
    print("   Credit Limit: $15,000")
    print("   Interest Rate: 18.0%")
    print("   Max Term: 60 months")
    print("\n   ⚠️  Approved but at higher interest rate due to risk factors.")
    print("   💡 Tip: Improve credit score or increase down payment for better rates.")
    
else:
    print("❌ REJECTED - Risk Too High")
    print(f"   Reason: Default probability ({prob_default:.1%}) exceeds threshold (15%)")
    print("\n   💡 SUGGESTIONS TO IMPROVE:")
    if loan_to_income > 100:
        print("      • Request a smaller loan amount")
    if payment_to_income > 40:
        print("      • Choose longer payment term to reduce monthly payment")
    if prob_default > 0.25:
        print("      • Improve credit score before reapplying")
        print("      • Add a co-signer with better credit")
        print("      • Increase down payment")
    if abs(YOUR_APPLICATION['DAYS_EMPLOYED']) < 730:  # Less than 2 years
        print("      • Wait until you have more employment history")

print("="*80)

# What affects your score
print("\n💡 FACTORS THAT AFFECT YOUR SCORE:")
print("   ✓ Higher income = Lower risk")
print("   ✓ Lower loan amount = Lower risk")  
print("   ✓ Longer employment = Lower risk")
print("   ✓ Higher credit scores = Lower risk")
print("   ✓ Owning property/car = Lower risk")
print("   ✓ Lower loan-to-income ratio = Lower risk")
print()

print("="*80)
print("📝 TO MODIFY YOUR APPLICATION:")
print("="*80)
print("""
Edit the YOUR_APPLICATION dictionary above with your actual information:

1. Change AMT_INCOME_TOTAL to your annual income
2. Change AMT_CREDIT to the loan amount you want
3. Change AMT_ANNUITY to your affordable monthly payment
4. Update your age (use formula: -(age × 365))
5. Update employment duration (use formula: -(years × 365))
6. Set your gender (M or F)
7. Update ownership flags (Y or N)

Then run this script again: python my_application.py
""")
print("="*80 + "\n")
