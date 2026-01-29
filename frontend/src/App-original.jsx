import React, { useState } from 'react';
import { CheckCircle, XCircle, AlertCircle, TrendingUp, TrendingDown, DollarSign, User, Briefcase, GraduationCap, Wallet, Calendar, CreditCard, Loader2 } from 'lucide-react';
import { scoreApplication } from './api';
import './index.css';

const EXAMPLE_APPLICANT = {
  fullName: 'Nithik Roshan',
  age: '24',
  annualIncome: '375000',
  savingsBalance: '500000',
  creditScore: '720',
  loanAmount: '250000',
  loanTermMonths: '24',
  employmentStatus: 'Employed',
  existingDebt: '5000',
  educationLevel: 'Higher education'
};

function App() {
  const [formData, setFormData] = useState({
    fullName: '',
    age: '',
    annualIncome: '',
    savingsBalance: '',
    creditScore: '',
    loanAmount: '',
    loanTermMonths: '',
    employmentStatus: 'Employed',
    existingDebt: '',
    educationLevel: 'Higher education'
  });

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    setError(null);
  };

  const loadExample = () => {
    setFormData(EXAMPLE_APPLICANT);
    setResult(null);
    setError(null);
  };

  const validateForm = () => {
    const required = ['fullName', 'age', 'annualIncome', 'savingsBalance', 'creditScore', 'loanAmount', 'loanTermMonths', 'existingDebt'];
    for (const field of required) {
      if (!formData[field]) {
        return `${field.replace(/([A-Z])/g, ' $1').trim()} is required`;
      }
    }

    const age = parseInt(formData.age);
    if (age < 18 || age > 100) return 'Age must be between 18 and 100';

    const creditScore = parseInt(formData.creditScore);
    if (creditScore < 300 || creditScore > 850) return 'Credit score must be between 300 and 850';

    const income = parseFloat(formData.annualIncome);
    if (income < 0) return 'Annual income must be positive';

    const loan = parseFloat(formData.loanAmount);
    if (loan <= 0) return 'Loan amount must be greater than 0';

    const term = parseInt(formData.loanTermMonths);
    if (term < 1 || term > 360) return 'Loan term must be between 1 and 360 months';

    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    const response = await scoreApplication(formData);
    
    setLoading(false);

    if (response.success) {
      setResult(response.data);
    } else {
      setError(response.error);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const getDecisionColor = (decision) => {
    if (decision === 'APPROVED' || decision === 'APPROVE') return 'success';
    if (decision === 'REJECTED' || decision === 'DECLINE') return 'danger';
    return 'warning';
  };

  const getTierBadgeColor = (tier) => {
    if (tier === 'A') return 'bg-green-100 text-green-800';
    if (tier === 'B') return 'bg-blue-100 text-blue-800';
    if (tier === 'C') return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const getImprovementTips = (result) => {
    const tips = [];
    const income = parseFloat(formData.annualIncome);
    const loan = parseFloat(formData.loanAmount);
    const credit = parseInt(formData.creditScore);
    const savings = parseFloat(formData.savingsBalance);

    if (loan / income > 1) {
      tips.push('Reduce loan amount - currently exceeds annual income');
    }
    if (credit < 650) {
      tips.push('Improve credit score (current: ' + credit + ') - pay bills on time');
    }
    if (savings < loan * 0.2) {
      tips.push('Increase savings - aim for at least 20% of loan amount');
    }
    const monthlyPayment = loan / parseInt(formData.loanTermMonths);
    const monthlyIncome = income / 12;
    if (monthlyPayment / monthlyIncome > 0.4) {
      tips.push('Extend loan term to reduce monthly payment burden');
    }
    if (tips.length === 0) {
      tips.push('Consider increasing down payment for better terms');
      tips.push('Maintain good payment history for future applications');
    }

    return tips;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="bg-primary-600 p-2 rounded-lg">
                <DollarSign className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Credit Risk Engine</h1>
                <p className="text-sm text-gray-500">AI-Powered Loan Eligibility Checker</p>
              </div>
            </div>
            <button
              onClick={loadExample}
              className="px-4 py-2 bg-primary-100 text-primary-700 rounded-lg hover:bg-primary-200 transition-colors text-sm font-medium"
            >
              Load Example
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Left Side - Input Form */}
          <div className="bg-white rounded-xl shadow-lg p-6 lg:p-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center">
              <User className="w-5 h-5 mr-2 text-primary-600" />
              Applicant Information
            </h2>

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Personal Information */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Personal Details</h3>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Full Name *
                  </label>
                  <input
                    type="text"
                    name="fullName"
                    value={formData.fullName}
                    onChange={handleChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition"
                    placeholder="John Doe"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Age *
                    </label>
                    <input
                      type="number"
                      name="age"
                      value={formData.age}
                      onChange={handleChange}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition"
                      placeholder="30"
                      min="18"
                      max="100"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Credit Score *
                    </label>
                    <input
                      type="number"
                      name="creditScore"
                      value={formData.creditScore}
                      onChange={handleChange}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition"
                      placeholder="700"
                      min="300"
                      max="850"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center">
                    <Briefcase className="w-4 h-4 mr-1" />
                    Employment Status *
                  </label>
                  <select
                    name="employmentStatus"
                    value={formData.employmentStatus}
                    onChange={handleChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition"
                  >
                    <option value="Employed">Employed</option>
                    <option value="Self-employed">Self-employed</option>
                    <option value="Student">Student</option>
                    <option value="Unemployed">Unemployed</option>
                    <option value="Retired">Retired</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center">
                    <GraduationCap className="w-4 h-4 mr-1" />
                    Education Level
                  </label>
                  <select
                    name="educationLevel"
                    value={formData.educationLevel}
                    onChange={handleChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition"
                  >
                    <option value="Higher education">Higher Education</option>
                    <option value="Secondary / secondary special">Secondary Education</option>
                    <option value="Incomplete higher">Incomplete Higher</option>
                    <option value="Lower secondary">Lower Secondary</option>
                  </select>
                </div>
              </div>

              {/* Financial Information */}
              <div className="space-y-4 pt-4 border-t">
                <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Financial Details</h3>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Annual Income ($) *
                    </label>
                    <input
                      type="number"
                      name="annualIncome"
                      value={formData.annualIncome}
                      onChange={handleChange}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition"
                      placeholder="80000"
                      min="0"
                      step="1000"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center">
                      <Wallet className="w-4 h-4 mr-1" />
                      Savings Balance ($) *
                    </label>
                    <input
                      type="number"
                      name="savingsBalance"
                      value={formData.savingsBalance}
                      onChange={handleChange}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition"
                      placeholder="50000"
                      min="0"
                      step="1000"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Existing Monthly Debt Payment ($) *
                  </label>
                  <input
                    type="number"
                    name="existingDebt"
                    value={formData.existingDebt}
                    onChange={handleChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition"
                    placeholder="500"
                    min="0"
                    step="100"
                  />
                </div>
              </div>

              {/* Loan Information */}
              <div className="space-y-4 pt-4 border-t">
                <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Loan Request</h3>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center">
                      <CreditCard className="w-4 h-4 mr-1" />
                      Loan Amount ($) *
                    </label>
                    <input
                      type="number"
                      name="loanAmount"
                      value={formData.loanAmount}
                      onChange={handleChange}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition"
                      placeholder="25000"
                      min="1"
                      step="1000"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center">
                      <Calendar className="w-4 h-4 mr-1" />
                      Loan Term (Months) *
                    </label>
                    <input
                      type="number"
                      name="loanTermMonths"
                      value={formData.loanTermMonths}
                      onChange={handleChange}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition"
                      placeholder="24"
                      min="1"
                      max="360"
                    />
                  </div>
                </div>
              </div>

              {/* Error Message */}
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-start">
                  <AlertCircle className="w-5 h-5 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-sm">{error}</span>
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-primary-600 text-white py-3 px-6 rounded-lg hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-semibold text-lg flex items-center justify-center"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  'Check Eligibility'
                )}
              </button>
            </form>
          </div>

          {/* Right Side - Results Panel */}
          <div className="bg-white rounded-xl shadow-lg p-6 lg:p-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">Decision Result</h2>

            {!result && !loading && (
              <div className="flex flex-col items-center justify-center h-full text-center py-12">
                <div className="bg-gray-100 p-6 rounded-full mb-4">
                  <TrendingUp className="w-12 h-12 text-gray-400" />
                </div>
                <p className="text-gray-500 text-lg">Submit the form to see results</p>
                <p className="text-gray-400 text-sm mt-2">Fill in the applicant details and click "Check Eligibility"</p>
              </div>
            )}

            {loading && (
              <div className="flex flex-col items-center justify-center h-full py-12">
                <Loader2 className="w-16 h-16 text-primary-600 animate-spin mb-4" />
                <p className="text-gray-600 text-lg">Analyzing application...</p>
              </div>
            )}

            {result && (
              <div className="space-y-6">
                {/* Decision Badge */}
                <div className={`p-6 rounded-xl ${
                  getDecisionColor(result.decision) === 'success' 
                    ? 'bg-success-50 border-2 border-success-500' 
                    : 'bg-danger-50 border-2 border-danger-500'
                }`}>
                  <div className="flex items-center justify-between mb-4">
                    {getDecisionColor(result.decision) === 'success' ? (
                      <CheckCircle className="w-12 h-12 text-success-700" />
                    ) : (
                      <XCircle className="w-12 h-12 text-danger-700" />
                    )}
                    <span className={`text-3xl font-bold ${
                      getDecisionColor(result.decision) === 'success' 
                        ? 'text-success-700' 
                        : 'text-danger-700'
                    }`}>
                      {result.decision}
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-white bg-opacity-50 p-3 rounded-lg">
                      <p className="text-sm text-gray-600 mb-1">Default Risk</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {(result.pd * 100).toFixed(2)}%
                      </p>
                    </div>
                    
                    <div className="bg-white bg-opacity-50 p-3 rounded-lg">
                      <p className="text-sm text-gray-600 mb-1">Risk Tier</p>
                      <span className={`inline-block px-4 py-2 rounded-full text-xl font-bold ${getTierBadgeColor(result.tier)}`}>
                        Tier {result.tier}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Top Reasons */}
                {result.top_reasons && result.top_reasons.length > 0 && (
                  <div className="border border-gray-200 rounded-lg p-5">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                      <TrendingDown className="w-5 h-5 mr-2 text-primary-600" />
                      Top Influencing Factors
                    </h3>
                    <div className="space-y-3">
                      {result.top_reasons.slice(0, 5).map((reason, idx) => (
                        <div key={idx} className="flex items-center justify-between">
                          <span className="text-sm text-gray-700 font-medium">
                            {reason.feature.replace(/_/g, ' ')}
                          </span>
                          <div className="flex items-center">
                            <div className="w-32 bg-gray-200 rounded-full h-2 mr-3">
                              <div
                                className="bg-primary-600 h-2 rounded-full"
                                style={{ width: `${Math.abs(reason.contribution) * 100}%` }}
                              />
                            </div>
                            <span className="text-sm font-semibold text-gray-900 w-12 text-right">
                              {(reason.contribution * 100).toFixed(1)}%
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Improvement Tips */}
                {getDecisionColor(result.decision) === 'danger' && (
                  <div className="border border-yellow-300 bg-yellow-50 rounded-lg p-5">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                      <AlertCircle className="w-5 h-5 mr-2 text-yellow-600" />
                      How to Improve
                    </h3>
                    <ul className="space-y-2">
                      {getImprovementTips(result).map((tip, idx) => (
                        <li key={idx} className="flex items-start text-sm text-gray-700">
                          <span className="text-yellow-600 mr-2">•</span>
                          {tip}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Additional Details */}
                {result.credit_limit && (
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-xs text-gray-500 mb-1">Credit Limit</p>
                      <p className="text-lg font-bold text-gray-900">
                        {formatCurrency(result.credit_limit)}
                      </p>
                    </div>
                    
                    {result.interest_rate && (
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <p className="text-xs text-gray-500 mb-1">Interest Rate</p>
                        <p className="text-lg font-bold text-gray-900">
                          {result.interest_rate.toFixed(2)}%
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>🤖 Powered by AI • Built with React + FastAPI • Production-Ready FinTech Demo</p>
        </div>
      </main>
    </div>
  );
}

export default App;
