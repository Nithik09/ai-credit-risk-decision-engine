import axios from 'axios';
import API_BASE_URL from './config';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Convert user form inputs to backend API format
 */
export const convertFormToFeatures = (formData) => {
  const age = parseInt(formData.age, 10);
  const income = parseFloat(formData.annualIncome);
  const loanAmount = parseFloat(formData.loanAmount);
  const creditScore = parseInt(formData.creditScore, 10);
  const loanTermMonths = parseInt(formData.loanTermMonths, 10);
  const savingsAmount = parseFloat(formData.savingsAmount);
  const existingMonthlyEmi = parseFloat(formData.existingMonthlyEmi);

  const monthlyPayment = loanAmount / loanTermMonths;

  // Map credit score to external source score (lower is better)
  const normalizedCredit = (creditScore - 300) / (850 - 300);
  const extSource = 0.40 - (normalizedCredit * 0.20);

  const employmentType = (formData.employmentType || '').toLowerCase();
  const daysEmployed = employmentType === 'salaried' || employmentType === 'self-employed'
    ? -(4 * 365)
    : employmentType === 'contract'
      ? -(2 * 365)
      : -30;

  const isExcellent = (creditScore >= 720 && (income / loanAmount) >= 1.5) ? 1 : 0;

  const additionalFeatures = {
    DAYS_BIRTH: -(age * 365),
    DAYS_ID_PUBLISH: -(3 * 365),
    DAYS_REGISTRATION: -(5 * 365),
    EXT_SOURCE_MEAN: extSource,
    EXT_SOURCE_WEIGHTED: extSource * 0.95,
    INCOME_PER_PERSON: income / 2,
    CREDIT_INCOME_PERCENT: loanAmount / income,
    ANNUITY_INCOME_PERC: (monthlyPayment * 12) / income,
    AMT_GOODS_PRICE: loanAmount * 0.95,
    CNT_FAM_MEMBERS: 2,
    FLAG_OWN_CAR: 1,
    FLAG_OWN_REALTY: 1,
    REGION_RATING_CLIENT: 2,
    BURO_DAYS_CREDIT_MEAN: -1000,
    PREV_APP_CREDIT_PERC: 0.75,
    IS_EXCELLENT_APPLICANT: isExcellent,
    SAVINGS_AMOUNT: savingsAmount,
    EXISTING_MONTHLY_EMI: existingMonthlyEmi,
    EMPLOYMENT_TYPE: formData.employmentType,
    CREDIT_SCORE: creditScore
  };

  return {
    application_id: formData.fullName,
    age: age,
    income_total: income,
    credit_amount: loanAmount,
    annuity_amount: monthlyPayment,
    days_employed: daysEmployed,
    ext_source_1: extSource,
    ext_source_2: extSource * 1.05,
    ext_source_3: extSource * 0.95,
    gender: 'M',
    additional_features: additionalFeatures
  };
};
/**
 * Call the credit scoring API
 */
export const scoreApplication = async (formData) => {
  try {
    if (!API_BASE_URL) {
      return {
        success: false,
        error: 'API base URL is not configured. Set NEXT_PUBLIC_API_BASE_URL.'
      };
    }
    const features = convertFormToFeatures(formData);
    const response = await api.post('/score', features);
    return {
      success: true,
      data: response.data
    };
  } catch (error) {
    console.error('API Error:', error.response?.data || error.message);
    return {
      success: false,
      error: error.response?.data?.detail || error.message || 'Failed to connect to API'
    };
  }
};

export default api;
