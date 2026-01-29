"""
Interactive Loan Application Form - Submit Your Own Data
Shows what inputs are needed and tests the prediction
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

print("\n" + "="*80)
print("💳 LOAN APPLICATION - REQUIRED INFORMATION")
print("="*80)

print("""
To check if you can get a loan, you need to provide these details:

┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. PERSONAL INFORMATION                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│   • Age (in years)                                                          │
│   • Gender (M/F)                                                            │
│   • Number of children                                                      │
│   • Number of family members                                                │
│   • Education level                                                         │
│   • Marital status                                                          │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. EMPLOYMENT & INCOME                                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│   • Annual income (in dollars)                                              │
│   • Income type (Working/Commercial/Pensioner/State servant)                │
│   • Years employed (how long at current job)                                │
│   • Occupation type                                                         │
│   • Organization type                                                       │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 3. LOAN DETAILS                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│   • Loan amount requested (in dollars)                                      │
│   • Monthly payment you can afford (in dollars)                             │
│   • Purpose of loan (Cash loan or Revolving loan)                           │
│   • Price of goods you're buying (if applicable)                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 4. ASSETS & PROPERTY                                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│   • Do you own a car? (Yes/No)                                              │
│   • Age of car (if you own one)                                             │
│   • Do you own a house/apartment? (Yes/No)                                  │
│   • Type of housing (House/Apartment/Rented/With parents/etc.)              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 5. CONTACT & DOCUMENTS                                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│   • Do you have a work phone? (Yes/No)                                      │
│   • Do you have a mobile phone? (Yes/No)                                    │
│   • Do you have email? (Yes/No)                                             │
│   • Years since ID was issued                                               │
│   • Years since current address registration                                │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 6. CREDIT HISTORY (if available)                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│   • External credit score 1 (0-1, from credit bureau)                       │
│   • External credit score 2 (0-1, from credit bureau)                       │
│   • External credit score 3 (0-1, from credit bureau)                       │
│   • Previous loan applications (number)                                     │
└─────────────────────────────────────────────────────────────────────────────┘
""")

print("\n" + "="*80)
print("📝 EXAMPLE: HOW TO SUBMIT YOUR DATA")
print("="*80)

print("""
Here's an example of how to create your application:

my_application = {
    # 1. PERSONAL INFO
    'CODE_GENDER': 'M',                          # M or F
    'DAYS_BIRTH': -12000,                        # Age: 12000 days / 365 = ~33 years
    'CNT_CHILDREN': 1,                           # Number of children
    'CNT_FAM_MEMBERS': 3,                        # Family size
    'NAME_EDUCATION_TYPE': 'Higher education',   # Education level
    'NAME_FAMILY_STATUS': 'Married',             # Marital status
    
    # 2. EMPLOYMENT & INCOME
    'AMT_INCOME_TOTAL': 120000,                  # Annual income: $120,000
    'NAME_INCOME_TYPE': 'Working',               # Income type
    'DAYS_EMPLOYED': -2000,                      # 2000 days employed = ~5.5 years
    'OCCUPATION_TYPE': 'Managers',               # Your job type
    'ORGANIZATION_TYPE': 'Business Entity Type 3',
    
    # 3. LOAN DETAILS
    'AMT_CREDIT': 50000,                         # Want to borrow: $50,000
    'AMT_ANNUITY': 4000,                         # Can pay monthly: $4,000
    'NAME_CONTRACT_TYPE': 'Cash loans',          # Loan type
    'AMT_GOODS_PRICE': 45000,                    # Item costs: $45,000
    
    # 4. ASSETS & PROPERTY
    'FLAG_OWN_CAR': 'Y',                         # Owns car
    'OWN_CAR_AGE': 5,                            # Car is 5 years old
    'FLAG_OWN_REALTY': 'Y',                      # Owns property
    'NAME_HOUSING_TYPE': 'House / apartment',    # Housing type
    
    # 5. CONTACT & DOCUMENTS
    'FLAG_WORK_PHONE': 1,                        # Has work phone
    'FLAG_CONT_MOBILE': 1,                       # Has mobile
    'FLAG_EMAIL': 1,                             # Has email
    'DAYS_ID_PUBLISH': -2000,                    # ID issued 2000 days ago
    'DAYS_REGISTRATION': -3000,                  # Registered 3000 days ago
    
    # 6. CREDIT HISTORY (if you have credit scores from bureaus)
    'EXT_SOURCE_1': 0.7,                         # External score 1 (0-1)
    'EXT_SOURCE_2': 0.65,                        # External score 2 (0-1)
    'EXT_SOURCE_3': 0.6,                         # External score 3 (0-1)
    
    # 7. LOCATION
    'REGION_RATING_CLIENT': 2,                   # Region rating (1-3)
    'REGION_POPULATION_RELATIVE': 0.02,          # Regional population
}
""")

print("\n" + "="*80)
print("✅ LET'S TEST THIS EXAMPLE APPLICATION")
print("="*80)

# Example application
my_application = {
    'CODE_GENDER': 'M',
    'DAYS_BIRTH': -12000,
    'CNT_CHILDREN': 1,
    'CNT_FAM_MEMBERS': 3,
    'NAME_EDUCATION_TYPE': 'Higher education',
    'NAME_FAMILY_STATUS': 'Married',
    'AMT_INCOME_TOTAL': 120000,
    'NAME_INCOME_TYPE': 'Working',
    'DAYS_EMPLOYED': -2000,
    'OCCUPATION_TYPE': 'Managers',
    'ORGANIZATION_TYPE': 'Business Entity Type 3',
    'AMT_CREDIT': 50000,
    'AMT_ANNUITY': 4000,
    'NAME_CONTRACT_TYPE': 'Cash loans',
    'AMT_GOODS_PRICE': 45000,
    'FLAG_OWN_CAR': 'Y',
    'OWN_CAR_AGE': 5,
    'FLAG_OWN_REALTY': 'Y',
    'NAME_HOUSING_TYPE': 'House / apartment',
    'FLAG_WORK_PHONE': 1,
    'FLAG_CONT_MOBILE': 1,
    'FLAG_EMAIL': 1,
    'DAYS_ID_PUBLISH': -2000,
    'DAYS_REGISTRATION': -3000,
    'EXT_SOURCE_1': 0.7,
    'EXT_SOURCE_2': 0.65,
    'EXT_SOURCE_3': 0.6,
    'REGION_RATING_CLIENT': 2,
    'REGION_POPULATION_RELATIVE': 0.02,
}

# Predict
df = pd.DataFrame([my_application])

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

print(f"\n📊 RESULT FOR EXAMPLE APPLICATION:")
print(f"   Income: $120,000/year")
print(f"   Loan Request: $50,000")
print(f"   Monthly Payment: $4,000")
print(f"   Age: ~33 years")
print(f"   Employment: ~5.5 years")
print(f"\n   ⚠️  Default Risk: {prob_default*100:.2f}%")
print(f"   💰 Payback Probability: {(1-prob_default)*100:.2f}%")

if prob_default < 0.04:
    print(f"\n   ✅ APPROVED - Tier A (Excellent)")
    print(f"   Credit Limit: $50,000")
    print(f"   Interest Rate: 8.0%")
elif prob_default < 0.08:
    print(f"\n   ✅ APPROVED - Tier B (Good)")
    print(f"   Credit Limit: $30,000")
    print(f"   Interest Rate: 12.0%")
elif prob_default < 0.15:
    print(f"\n   ✅ APPROVED - Tier C (Fair)")
    print(f"   Credit Limit: $15,000")
    print(f"   Interest Rate: 18.0%")
else:
    print(f"\n   ❌ REJECTED - Too Risky")

print("\n" + "="*80)
print("💡 MINIMUM REQUIRED FIELDS (if you don't have all data)")
print("="*80)

print("""
If you don't have all information, at MINIMUM provide:

ESSENTIAL FIELDS:
  1. AMT_INCOME_TOTAL      - Your annual income
  2. AMT_CREDIT            - Loan amount you want
  3. AMT_ANNUITY           - Monthly payment you can afford
  4. DAYS_BIRTH            - Your age (in negative days)
  5. DAYS_EMPLOYED         - Employment duration (in negative days)
  6. CODE_GENDER           - M or F
  7. FLAG_OWN_CAR          - Y or N
  8. FLAG_OWN_REALTY       - Y or N

IMPORTANT FIELDS (helps improve accuracy):
  9. EXT_SOURCE_1, 2, 3    - Credit scores if you have them
 10. NAME_EDUCATION_TYPE   - Your education level
 11. NAME_INCOME_TYPE      - Type of income
 12. CNT_CHILDREN          - Number of children

NOTE: Missing fields will be filled with default values (0 or "Unknown")
""")

print("\n" + "="*80)
print("🎯 TO TEST YOUR OWN APPLICATION:")
print("="*80)

print("""
1. Copy the example above
2. Change the values to match YOUR information
3. Save it in a Python file or paste in Python console
4. Run: result = predict_payback(my_application)

OR use the API (after starting the API server):

curl -X POST "http://localhost:8000/score" \\
  -H "Content-Type: application/json" \\
  -d '{
    "AMT_INCOME_TOTAL": 120000,
    "AMT_CREDIT": 50000,
    "AMT_ANNUITY": 4000,
    "DAYS_BIRTH": -12000,
    "DAYS_EMPLOYED": -2000,
    "CODE_GENDER": "M",
    "FLAG_OWN_CAR": "Y",
    "FLAG_OWN_REALTY": "Y",
    "EXT_SOURCE_1": 0.7,
    "EXT_SOURCE_2": 0.65,
    "EXT_SOURCE_3": 0.6
  }'
""")

print("\n" + "="*80)
print("📋 QUICK REFERENCE: AGE & EMPLOYMENT CONVERSION")
print("="*80)

print("""
The model uses NEGATIVE DAYS for dates:

AGE CONVERSION:
  • 25 years old  = -9,125 days  (25 × 365)
  • 30 years old  = -10,950 days (30 × 365)
  • 35 years old  = -12,775 days (35 × 365)
  • 40 years old  = -14,600 days (40 × 365)
  • 45 years old  = -16,425 days (45 × 365)
  • 50 years old  = -18,250 days (50 × 365)

EMPLOYMENT DURATION:
  • 1 year  = -365 days
  • 2 years = -730 days
  • 3 years = -1,095 days
  • 5 years = -1,825 days
  • 10 years = -3,650 days

Formula: DAYS = -(Years × 365)
""")

print("="*80)
print("✅ You're ready to submit your application!")
print("="*80 + "\n")
