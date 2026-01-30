# AI Credit Risk Decision Engine

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16+-000000)](https://nextjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Production-grade credit risk scoring for BNPL and installment lending.
The system returns probability of default (PD), risk tier, and explainability signals through a FastAPI backend and a premium Next.js frontend.

Maintained by **Nithiik Roshan** — LinkedIn: https://www.linkedin.com/in/nithik-roshan-devarajraj-8783192aa

## Overview

This project evaluates credit applications and produces a decision packet designed for real underwriting workflows.

**Why it is unique**:
- End-to-end decisioning: prediction, policying, and explanation in one service.
- Compliance-ready signals: explainability and fairness diagnostics.
- Production UI + API with deployment guidance.

## Key Features

- **PD scoring** with calibrated probabilities.
- **Explainability** with top contributing factors per decision.
- **Fairness analysis** for bias signals across sensitive attributes.
- **Monitoring hooks** for drift detection and retraining triggers.
- **Clean API contract** for easy integration into lending systems.

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
1. The UI submits the application payload.
2. FastAPI validates input and builds features.
3. The model returns PD and a decision tier.
4. The API responds with decision + top reasons.

## Live Demo & API

- **Live Demo (Vercel):** https://<your-vercel-app>.vercel.app
- **API Base URL (Render):** https://<your-render-service>.onrender.com

## Frontend (Next.js)

Location: [frontend](frontend)

### Local Run (Windows)

```bash
cd frontend
npm install
npm run dev
```

### Environment

Create `.env.local` in [frontend](frontend) with:

- **Local development**

```
NEXT_PUBLIC_API_BASE_URL=http://<your-local-backend-host>:<port>
```

- **Production (Vercel)**

```
NEXT_PUBLIC_API_BASE_URL=https://<your-render-service>.onrender.com
```

### Deployment (Vercel)

1. Set **Root Directory** to `frontend`.
2. Add environment variable `NEXT_PUBLIC_API_BASE_URL` (Render URL).
3. Deploy.

## Backend (FastAPI)

Location: [backend](backend)

### Local Run (Windows)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn src.serving.app:app --reload
```

### Deployment (Render)

1. Set **Root Directory** to `backend`.
2. **Build Command**: `pip install -r requirements.txt`
3. **Start Command**: `uvicorn src.serving.app:app --host 0.0.0.0 --port $PORT`
4. **Health Check Path**: `/health`
5. Add environment variables (optional): `ALLOWED_ORIGINS` for your Vercel domain.

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