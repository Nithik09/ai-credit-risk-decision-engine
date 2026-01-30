# AI Credit Risk Engine — Portfolio Project

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/react-18.2-61dafb.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An end-to-end AI credit risk assessment system for BNPL and installment loans, combining real-time scoring, explainable AI, fairness analysis, and a production-ready API with a modern React frontend.

---

## Executive Summary

- **AUC 0.7658** on **307,511** real loan applications
- **< 500ms** end-to-end scoring latency
- **Explainability** with SHAP and adverse-action reasons
- **Fairness** checks for demographic parity and equal opportunity
- **Production-ready** FastAPI backend + React/Tailwind frontend

---

## Live Demo

- Frontend: https://your-app.vercel.app
- API Docs: https://your-api.onrender.com/docs
- Demo Video: https://youtube.com/your-video

---

## Resume Highlights

- Built a full-stack ML system for credit risk with real-time scoring and explainability.
- Implemented bias monitoring and model drift detection for responsible AI.
- Deployed a FastAPI service with a React dashboard and Dockerized runtime.

---

## System Architecture

```
React + Vite UI  →  FastAPI /score  →  LightGBM Model  →  SHAP Explainer
                         │
                         └─ Fairness + Drift Monitoring
```

---

## Key Capabilities

### Machine Learning
- LightGBM classifier with calibrated probabilities
- 80 engineered features across applicant, bureau, and payment history
- Stratified validation with strong AUC and KS performance

### Explainability
- SHAP global and local attributions
- Top contributing factors per decision
- Clear adverse-action reasons

### Fairness & Monitoring
- Demographic parity and equal opportunity analysis
- Drift checks with PSI and KS statistics
- Alert-ready monitoring hooks

### Decision Engine
- 4 risk tiers (A–D)
- Automated approval / decline / manual review
- Risk-based credit limits and APR bands

---

## Model Performance

| Metric | Value |
|--------|-------|
| AUC-ROC | 0.7658 |
| Gini | 0.5315 |
| KS | 0.3972 |
| Log Loss | 0.3892 |
| Precision (Top 10%) | 0.6847 |
| Recall (Top 10%) | 0.5234 |

Dataset: Home Credit Default Risk (Kaggle)

---

## Quick Start

### Backend

```bash
pip install -r requirements.txt
python src/api/api_service.py
```

Backend runs at https://<your-backend-url>

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at https://<your-frontend-url>

---

## API Endpoints

- `POST /score` — score an applicant
- `GET /health` — health check

---

## Project Structure (Top-Level)

```
credit-risk-engine/
├── frontend/                 # React UI
├── src/                      # API + ML pipeline
├── models/                   # Trained artifacts
├── data/                     # Raw/processed data
├── ARCHITECTURE.md
├── DELIVERABLES.md
├── QUICKSTART.md
└── README.md
```

---

## Documentation

- Architecture overview: ARCHITECTURE.md
- End-to-end guide: QUICKSTART.md
- Deliverables list: DELIVERABLES.md
- Frontend guide: frontend/QUICKSTART.md
- Deployment guide: frontend/DEPLOYMENT.md
- Demo script: frontend/DEMO_VIDEO_SCRIPT.md

---

## Deployment

- Backend: Render, Railway, Azure App Service
- Frontend: Vercel, Netlify, GitHub Pages

---

## Contact

- GitHub: https://github.com/your-username
- LinkedIn: https://linkedin.com/in/your-profile
- Email: your.email@example.com

---

## License

MIT License — see LICENSE

---

**Built with ❤️ by [Your Name] | 2024**

*Perfect for portfolio showcases, job interviews, and learning ML system design!*
