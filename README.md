# AI Credit Risk Decision Engine

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16+-000000)](https://nextjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Production-grade credit risk scoring for BNPL and installment lending.
The platform returns probability of default (PD), risk tier, and explainability signals via a FastAPI service and a modern Next.js UI.

Maintained by **Nithiik Roshan** — LinkedIn: https://www.linkedin.com/in/nithik-roshan-devarajraj-8783192aa

## Overview

This system evaluates credit applications and produces a decision packet built for FinTech underwriting workflows.

**Why it is unique**:
- End-to-end decisioning: prediction, policying, and explanation in one service.
- Built-in compliance support: explainability and fairness diagnostics.
- Production-ready interface: API + UI with deployment guidance.

## Key Features

- **PD scoring** with calibrated probabilities.
- **Explainability** with top feature contributors per decision.
- **Fairness analysis** for bias signals across sensitive attributes.
- **Monitoring hooks** for drift detection and retraining triggers.
- **Clean API contract** for easy integration into underwriting systems.

## Architecture

```
┌──────────────────────┐        ┌─────────────────────────┐
│  Next.js Frontend    │  --->  │  FastAPI /score API     │
│  (Vercel)            │        │  (Render)               │
└──────────────────────┘        └───────────┬─────────────┘
                                            │
                                            ▼
                                 ┌───────────────────────┐
                                 │  ML Model Artifacts   │
                                 │  + Explainability     │
                                 └───────────────────────┘
```

**How it works**:
1. The UI submits an application payload.
2. FastAPI validates input and builds features.
3. The model returns PD and a decision tier.
4. The API responds with decision + top drivers.

## Live Demo & API

- **Live Demo (Vercel):** https://<your-vercel-app>.vercel.app
- **API Docs (Render):** https://<your-render-service>.onrender.com/docs

## Frontend (Next.js)

Location: [frontend-next](frontend-next)

### Local Run

```bash
cd frontend-next
npm install
npm run dev
```

### Environment

Create `.env.local` in [frontend-next](frontend-next) with:

```
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

### Deployment (Vercel)

1. Import [frontend-next](frontend-next) into Vercel.
2. Set `NEXT_PUBLIC_API_BASE_URL` to your Render API base.
3. Deploy.

## Backend (FastAPI)

Entry point: `src/serving/app.py`

### Local Run

```bash
python -m uvicorn src.serving.app:app --host 0.0.0.0 --port 8000
```

### Deployment (Render)

**Build Command**

```
pip install -r requirements.txt
```

**Start Command**

```
uvicorn src.serving.app:app --host 0.0.0.0 --port $PORT
```

## Screenshots

Add screenshots here:

- `screenshots/home.png`
- `screenshots/result.png`

## Business Value

- Faster, consistent credit decisions at scale.
- Transparent underwriting aligned with regulatory expectations.
- Deployable stack suitable for real production pipelines.

## License

MIT — see [LICENSE](LICENSE).