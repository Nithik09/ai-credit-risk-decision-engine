"use client";

import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  BadgeCheck,
  Banknote,
  Briefcase,
  CalendarClock,
  CreditCard,
  PiggyBank,
  Sparkles,
  UserRound,
  WalletCards
} from "lucide-react";

const INITIAL_FORM = {
  fullName: "",
  age: "",
  annualIncome: "",
  savingsAmount: "",
  creditScore: "",
  loanAmount: "",
  loanTermMonths: "",
  employmentType: "Salaried",
  existingMonthlyEmi: ""
};

const SAMPLE_DATA = {
  fullName: "Avery Morgan",
  age: "34",
  annualIncome: "98000",
  savingsAmount: "22000",
  creditScore: "735",
  loanAmount: "28000",
  loanTermMonths: "24",
  employmentType: "Salaried",
  existingMonthlyEmi: "420"
};

const EMPLOYMENT_OPTIONS = ["Salaried", "Self-Employed", "Contract", "Student", "Retired", "Unemployed"];

const cardMotion = {
  initial: { opacity: 0, y: 30 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.6, ease: "easeOut" }
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

export default function Home() {
  const [formData, setFormData] = useState(INITIAL_FORM);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setError("");
  };

  const validate = () => {
    const required = [
      "fullName",
      "age",
      "annualIncome",
      "savingsAmount",
      "creditScore",
      "loanAmount",
      "loanTermMonths",
      "existingMonthlyEmi"
    ];

    for (const field of required) {
      if (!formData[field]) {
        return `${field.replace(/([A-Z])/g, " $1").trim()} is required`;
      }
    }

    const age = Number(formData.age);
    if (age < 18 || age > 100) return "Age must be between 18 and 100";

    const creditScore = Number(formData.creditScore);
    if (creditScore < 300 || creditScore > 850) return "Credit score must be between 300 and 850";

    const income = Number(formData.annualIncome);
    if (income <= 0) return "Annual income must be greater than 0";

    const loan = Number(formData.loanAmount);
    if (loan <= 0) return "Loan amount must be greater than 0";

    const term = Number(formData.loanTermMonths);
    if (term < 6 || term > 360) return "Loan term must be between 6 and 360 months";

    return "";
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const age = Number(formData.age);
      const income = Number(formData.annualIncome);
      const loanAmount = Number(formData.loanAmount);
      const creditScore = Number(formData.creditScore);
      const loanTermMonths = Number(formData.loanTermMonths);
      const savingsAmount = Number(formData.savingsAmount);
      const existingMonthlyEmi = Number(formData.existingMonthlyEmi);
      const monthlyPayment = loanAmount / loanTermMonths;

      const normalizedCredit = (creditScore - 300) / (850 - 300);
      const extSource = 0.40 - (normalizedCredit * 0.20);

      const employmentType = (formData.employmentType || "").toLowerCase();
      const daysEmployed = employmentType === "salaried" || employmentType === "self-employed"
        ? -(4 * 365)
        : employmentType === "contract"
          ? -(2 * 365)
          : -30;

      const response = await fetch(`${API_BASE_URL}/score`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          application_id: formData.fullName,
          age: age,
          income_total: income,
          credit_amount: loanAmount,
          annuity_amount: monthlyPayment,
          days_employed: daysEmployed,
          ext_source_1: extSource,
          ext_source_2: extSource * 1.05,
          ext_source_3: extSource * 0.95,
          gender: "M",
          additional_features: {
            SAVINGS_AMOUNT: savingsAmount,
            EXISTING_MONTHLY_EMI: existingMonthlyEmi,
            EMPLOYMENT_TYPE: formData.employmentType,
            CREDIT_SCORE: creditScore
          }
        })
      });

      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || "Failed to score application.");
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err?.message || "Unable to score this application.");
    } finally {
      setLoading(false);
    }
  };

  const normalizedResult = useMemo(() => {
    if (!result) return null;

    const pd = result.pd ?? result.pd_score ?? 0;
    const decision = result.decision ?? "UNKNOWN";
    const tier = result.tier ?? result.risk_tier ?? "N/A";
    const reasons = result.top_reasons
      ?? result.top_factors?.map((item) => item.feature || item.reason || "Unknown reason")
      ?? [];

    return {
      pd,
      decision,
      tier,
      reasons
    };
  }, [result]);

  const decisionLabel = normalizedResult?.decision?.toUpperCase() || "";
  const isApproved = decisionLabel.includes("APPROVE");
  const isDeclined = decisionLabel.includes("DECLINE") || decisionLabel.includes("REJECT");
  const pdPercent = Math.min(Math.max(normalizedResult?.pd ?? 0, 0), 1) * 100;

  const tips = useMemo(() => {
    if (!normalizedResult || !isDeclined) return [];

    const income = Number(formData.annualIncome);
    const loan = Number(formData.loanAmount);
    const creditScore = Number(formData.creditScore);
    const savings = Number(formData.savingsAmount);
    const emi = Number(formData.existingMonthlyEmi);
    const term = Number(formData.loanTermMonths);
    const monthlyPayment = loan / term;

    const suggestions = [];
    if (loan / income > 1) suggestions.push("Reduce the loan amount to keep it below annual income.");
    if (creditScore < 650) suggestions.push("Improve credit score by paying bills on time and reducing utilization.");
    if (savings < loan * 0.2) suggestions.push("Increase savings to reach at least 20% of the loan amount.");
    if ((monthlyPayment + emi) / (income / 12) > 0.45) suggestions.push("Extend loan term or reduce EMI burden to improve affordability.");

    if (!suggestions.length) {
      suggestions.push("Consider adding a co-applicant to strengthen the profile.");
      suggestions.push("Re-apply after maintaining a consistent payment history for 3-6 months.");
    }

    return suggestions;
  }, [normalizedResult, isDeclined, formData]);

  return (
    <div className="relative min-h-screen overflow-hidden bg-slate-950 text-slate-100">
      <div className="animated-bg" />
      <div className="pointer-events-none absolute left-1/2 top-[-240px] h-[420px] w-[420px] -translate-x-1/2 rounded-full bg-indigo-500/30 blur-[160px]" />
      <div className="pointer-events-none absolute bottom-[-200px] right-[-120px] h-[360px] w-[360px] rounded-full bg-cyan-400/20 blur-[140px]" />

      <header className="relative z-10 border-b border-white/10 bg-black/40 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-6">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-cyan-200">FinTech AI</p>
            <h1 className="mt-2 text-3xl font-semibold text-white sm:text-4xl">AI Credit Risk Checker</h1>
            <p className="mt-2 text-sm text-slate-300">Instant loan eligibility with explainable AI</p>
          </div>
          <div className="flex items-center gap-3 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs font-semibold text-slate-200 shadow-[0_0_20px_rgba(99,102,241,0.3)]">
            <Sparkles className="h-4 w-4 text-cyan-300" />
            Live scoring connected to FastAPI
          </div>
        </div>
      </header>

      <main className="relative z-10 mx-auto grid max-w-6xl grid-cols-1 gap-8 px-6 py-10 lg:grid-cols-[1.15fr_0.85fr]">
        <motion.section {...cardMotion} className="glass-card rounded-3xl p-8">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold text-white">Applicant Details</h2>
              <p className="mt-1 text-sm text-slate-300">Complete the fields to get an instant decision.</p>
            </div>
            <button
              type="button"
              onClick={() => setFormData(SAMPLE_DATA)}
              className="rounded-full border border-cyan-400/30 bg-cyan-500/10 px-4 py-2 text-xs font-semibold text-cyan-200 transition hover:bg-cyan-500/20"
            >
              Fill Sample Data
            </button>
          </div>

          <form onSubmit={handleSubmit} className="mt-6 grid gap-5">
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="field-label">
                Full Name
                <div className="input-shell">
                  <UserRound className="h-4 w-4 text-cyan-200" />
                  <input
                    name="fullName"
                    value={formData.fullName}
                    onChange={handleChange}
                    placeholder="Jane Doe"
                    className="input-field"
                  />
                </div>
              </label>
              <label className="field-label">
                Age
                <div className="input-shell">
                  <CalendarClock className="h-4 w-4 text-cyan-200" />
                  <input
                    name="age"
                    type="number"
                    value={formData.age}
                    onChange={handleChange}
                    placeholder="32"
                    className="input-field"
                  />
                </div>
              </label>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <label className="field-label">
                Annual Income
                <div className="input-shell">
                  <Banknote className="h-4 w-4 text-cyan-200" />
                  <input
                    name="annualIncome"
                    type="number"
                    value={formData.annualIncome}
                    onChange={handleChange}
                    placeholder="85000"
                    className="input-field"
                  />
                </div>
              </label>
              <label className="field-label">
                Savings Amount
                <div className="input-shell">
                  <PiggyBank className="h-4 w-4 text-cyan-200" />
                  <input
                    name="savingsAmount"
                    type="number"
                    value={formData.savingsAmount}
                    onChange={handleChange}
                    placeholder="20000"
                    className="input-field"
                  />
                </div>
              </label>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <label className="field-label">
                Credit Score
                <div className="input-shell">
                  <BadgeCheck className="h-4 w-4 text-cyan-200" />
                  <input
                    name="creditScore"
                    type="number"
                    value={formData.creditScore}
                    onChange={handleChange}
                    placeholder="720"
                    className="input-field"
                  />
                </div>
              </label>
              <label className="field-label">
                Loan Amount
                <div className="input-shell">
                  <CreditCard className="h-4 w-4 text-cyan-200" />
                  <input
                    name="loanAmount"
                    type="number"
                    value={formData.loanAmount}
                    onChange={handleChange}
                    placeholder="25000"
                    className="input-field"
                  />
                </div>
              </label>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <label className="field-label">
                Loan Term (months)
                <div className="input-shell">
                  <CalendarClock className="h-4 w-4 text-cyan-200" />
                  <input
                    name="loanTermMonths"
                    type="number"
                    value={formData.loanTermMonths}
                    onChange={handleChange}
                    placeholder="24"
                    className="input-field"
                  />
                </div>
              </label>
              <label className="field-label">
                Employment Type
                <div className="input-shell">
                  <Briefcase className="h-4 w-4 text-cyan-200" />
                  <select
                    name="employmentType"
                    value={formData.employmentType}
                    onChange={handleChange}
                    className="input-field appearance-none"
                  >
                    {EMPLOYMENT_OPTIONS.map((option) => (
                      <option key={option} value={option} className="bg-slate-900">
                        {option}
                      </option>
                    ))}
                  </select>
                </div>
              </label>
            </div>

            <label className="field-label">
              Existing Monthly EMI
              <div className="input-shell">
                <WalletCards className="h-4 w-4 text-cyan-200" />
                <input
                  name="existingMonthlyEmi"
                  type="number"
                  value={formData.existingMonthlyEmi}
                  onChange={handleChange}
                  placeholder="450"
                  className="input-field"
                />
              </div>
            </label>

            {error ? (
              <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
                {error}
              </div>
            ) : null}

            <button
              type="submit"
              disabled={loading}
              className="group relative overflow-hidden rounded-2xl bg-gradient-to-r from-cyan-500 via-indigo-500 to-fuchsia-500 px-4 py-3 text-sm font-semibold text-white shadow-[0_0_25px_rgba(99,102,241,0.45)] transition hover:scale-[1.01] disabled:cursor-not-allowed disabled:opacity-70"
            >
              <span className="relative z-10 flex items-center justify-center gap-2">
                {loading ? "Scoring..." : "Check Loan Eligibility"}
                {loading ? <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" /> : null}
              </span>
              <span className="absolute inset-0 opacity-0 transition group-hover:opacity-100" style={{ background: "radial-gradient(circle at top, rgba(255,255,255,0.4), transparent 60%)" }} />
            </button>
          </form>
        </motion.section>

        <motion.aside {...cardMotion} transition={{ duration: 0.7, delay: 0.1 }} className="glass-card rounded-3xl p-8">
          <h2 className="text-lg font-semibold text-white">Decision Output</h2>
          <p className="mt-1 text-sm text-slate-300">Results appear instantly after scoring.</p>

          {!normalizedResult ? (
            <div className="mt-6 rounded-2xl border border-white/10 bg-white/5 p-6 text-sm text-slate-300">
              Submit the form to view approval status, PD risk, and top reasons.
            </div>
          ) : (
            <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="mt-6 space-y-5">
              <div className={`rounded-2xl border px-5 py-4 ${isApproved ? "border-emerald-400/40 bg-emerald-400/10 text-emerald-100" : isDeclined ? "border-rose-400/40 bg-rose-400/10 text-rose-100" : "border-amber-400/40 bg-amber-400/10 text-amber-100"}`}>
                <p className="text-xs uppercase tracking-[0.2em]">Decision</p>
                <p className="mt-2 text-3xl font-semibold">{isApproved ? "APPROVED" : isDeclined ? "DECLINED" : decisionLabel}</p>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between text-xs uppercase tracking-[0.2em] text-slate-400">
                  <span>PD Risk</span>
                  <span>{pdPercent.toFixed(2)}%</span>
                </div>
                <div className="h-2 rounded-full bg-white/10">
                  <div
                    className="h-2 rounded-full bg-gradient-to-r from-cyan-400 via-indigo-400 to-fuchsia-400 shadow-[0_0_12px_rgba(129,140,248,0.6)]"
                    style={{ width: `${pdPercent}%` }}
                  />
                </div>
              </div>

              <div className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                <span className="text-xs uppercase tracking-[0.2em] text-slate-400">Risk Tier</span>
                <span className="rounded-full border border-white/20 bg-white/10 px-4 py-1 text-sm font-semibold text-white">{normalizedResult.tier}</span>
              </div>

              <div>
                <p className="text-sm font-semibold text-white">Top Reasons</p>
                <ul className="mt-3 space-y-2">
                  {normalizedResult.reasons.slice(0, 5).map((reason, index) => (
                    <li key={`${reason}-${index}`} className="flex items-center justify-between gap-3 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-200">
                      <span>{reason}</span>
                      <span className="h-1 w-16 rounded-full bg-gradient-to-r from-cyan-400/70 to-indigo-400/70" />
                    </li>
                  ))}
                  {!normalizedResult.reasons.length && (
                    <li className="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-300">
                      Top reasons unavailable for this model response.
                    </li>
                  )}
                </ul>
              </div>

              {isDeclined && (
                <div className="rounded-2xl border border-amber-300/30 bg-amber-400/10 p-4">
                  <p className="text-sm font-semibold text-amber-100">What to improve</p>
                  <ul className="mt-3 space-y-2 text-sm text-amber-50">
                    {tips.map((tip, index) => (
                      <li key={`${tip}-${index}`} className="flex items-start gap-2">
                        <span className="mt-1 h-2 w-2 rounded-full bg-amber-300" />
                        <span>{tip}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </motion.div>
          )}
        </motion.aside>
      </main>
    </div>
  );
}
