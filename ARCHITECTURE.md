# 🏗️ System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT APPLICATIONS                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │   Web App    │  │  Mobile App  │  │  Partner API │             │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │
└─────────┼──────────────────┼──────────────────┼────────────────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │ HTTPS/REST
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      API GATEWAY / LOAD BALANCER                     │
│                         (Nginx / AWS ALB)                            │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          │                               │
          ▼                               ▼
┌─────────────────────┐         ┌─────────────────────┐
│  FastAPI Instance 1 │         │  FastAPI Instance N │
│                     │         │                     │
│  ┌───────────────┐ │         │  ┌───────────────┐ │
│  │ Rate Limiter  │ │   ...   │  │ Rate Limiter  │ │
│  ├───────────────┤ │         │  ├───────────────┤ │
│  │ Auth Handler  │ │         │  │ Auth Handler  │ │
│  ├───────────────┤ │         │  ├───────────────┤ │
│  │  Endpoints    │ │         │  │  Endpoints    │ │
│  └───────────────┘ │         │  └───────────────┘ │
└──────────┬──────────┘         └──────────┬──────────┘
           │                               │
           └───────────────┬───────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       CORE ML PIPELINE                               │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                    1. Feature Engineering                   │    │
│  │  • Data validation                                          │    │
│  │  • Missing value imputation                                 │    │
│  │  • Feature creation (100+ features)                         │    │
│  │  • Feature encoding & scaling                               │    │
│  └──────────────────────────┬─────────────────────────────────┘    │
│                              ▼                                       │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                    2. Model Inference                       │    │
│  │  • LightGBM/XGBoost prediction                             │    │
│  │  • Probability calibration (Isotonic/Platt)               │    │
│  │  • PD score output (0-1)                                   │    │
│  └──────────────────────────┬─────────────────────────────────┘    │
│                              ▼                                       │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                    3. Decision Engine                       │    │
│  │  • Risk tier assignment (A/B/C/D)                          │    │
│  │  • Approval/rejection logic                                │    │
│  │  • Credit limit calculation                                │    │
│  │  • Interest rate pricing                                   │    │
│  │  • Manual review flagging                                  │    │
│  └──────────────────────────┬─────────────────────────────────┘    │
│                              ▼                                       │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                    4. Explainability                        │    │
│  │  • SHAP value computation                                  │    │
│  │  • Top feature contributions                               │    │
│  │  • Adverse action reasons                                  │    │
│  │  • Regulatory compliance output                            │    │
│  └──────────────────────────┬─────────────────────────────────┘    │
│                              ▼                                       │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                    5. Monitoring                            │    │
│  │  • Prediction logging                                      │    │
│  │  • Drift detection (PSI)                                   │    │
│  │  • Alert generation                                        │    │
│  │  • Metrics tracking                                        │    │
│  └────────────────────────────────────────────────────────────┘    │
└───────────────────────────┬───────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA STORAGE                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │   Models     │  │  Monitoring  │  │   Logs       │             │
│  │   (.pkl)     │  │   State      │  │  (Loguru)    │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. API Layer (FastAPI)

**Responsibilities:**
- Request validation (Pydantic)
- Authentication & authorization
- Rate limiting
- Request routing
- Response formatting
- Error handling

**Endpoints:**
- `POST /score` - Single application scoring
- `POST /score/batch` - Batch processing
- `GET /health` - Health check
- `GET /model/info` - Model metadata
- `GET /monitoring/stats` - Monitoring dashboard

### 2. Feature Engineering Pipeline

**Process Flow:**
```
Raw Application Data
        ↓
Clean & Validate
        ↓
Handle Missing Values
        ↓
Create Derived Features
  • Credit-to-income ratio
  • Payment burden
  • Employment stability
  • External score combinations
  • 100+ domain features
        ↓
Encode Categoricals
        ↓
Scale Numeric Features
        ↓
Select Final Features
        ↓
Feature Vector [1 x N]
```

### 3. ML Model Pipeline

**Architecture:**
```
Input: Feature Vector [1 x 200]
        ↓
LightGBM Classifier
  • 500 trees
  • Max depth: 7
  • Learning rate: 0.05
        ↓
Raw Probability [0-1]
        ↓
Calibration Layer
  • Isotonic Regression
  • 5-fold CV
        ↓
Calibrated PD Score [0-1]
```

**Model Artifacts:**
- `credit_risk_model_base.pkl` - Base LightGBM
- `credit_risk_model_calibrated.pkl` - Calibrated model
- `feature_names.pkl` - Feature list
- `label_encoders.pkl` - Categorical encoders
- `scaler.pkl` - Feature scaler

### 4. Decision Engine

**Logic Flow:**
```
PD Score Input
        ↓
    Is PD > 15%?
     /        \
   Yes        No
    ↓          ↓
REJECT     APPROVE
            ↓
    Assign Risk Tier
      • A: 0-4%
      • B: 4-8%
      • C: 8-15%
            ↓
    Calculate Limits
      • A: $50K
      • B: $25K
      • C: $10K
            ↓
    Calculate Rate
      • A: 8-12% APR
      • B: 15-18% APR
      • C: 22-28% APR
            ↓
    Check Manual Review
      • Near boundary?
      • High amount?
      • Missing data?
            ↓
      Final Decision
```

### 5. Explainability Module

**SHAP Pipeline:**
```
Model + Background Data
        ↓
TreeExplainer Init
        ↓
Compute SHAP Values
  • Per-feature contributions
  • Positive = increases risk
  • Negative = decreases risk
        ↓
Rank by Absolute Impact
        ↓
Top 5 Factors
        ↓
Generate Human-Readable
Adverse Action Reasons
```

### 6. Monitoring System

**Drift Detection:**
```
Production Data Batch
        ↓
Compare to Baseline
  • Feature distributions
  • Prediction distributions
        ↓
Compute PSI per Feature
        ↓
    PSI < 0.1?
     /        \
   Yes        No
    ↓          ↓
   OK      ALERT!
            ↓
    Retrain Trigger
```

## Data Flow Diagram

```
┌─────────┐
│ Request │
└────┬────┘
     │ {age: 35, income: 180K, ...}
     ▼
┌─────────────────┐
│ Data Validation │
└────┬────────────┘
     │ Validated JSON
     ▼
┌─────────────────────┐
│ Feature Engineering │
└────┬────────────────┘
     │ [0.28, 0.75, -1825, ...] (200 features)
     ▼
┌──────────────┐
│ ML Inference │
└────┬─────────┘
     │ PD = 0.0342
     ▼
┌────────────────┐
│ Decision Logic │
└────┬───────────┘
     │ {decision: APPROVED, tier: A, limit: 50K, rate: 8.68%}
     ▼
┌──────────────┐
│ SHAP Explain │
└────┬─────────┘
     │ [EXT_SOURCE_2: -0.23, CREDIT_RATIO: 0.05, ...]
     ▼
┌─────────────┐
│ Format JSON │
└────┬────────┘
     │ Full Response
     ▼
┌──────────┐
│ Response │ → Client
└──────────┘
```

## Deployment Architecture

### Production Setup

```
┌─────────────────────────────────────────────────────────────┐
│                       AWS / Azure / GCP                      │
│                                                               │
│  ┌────────────────────────────────────────────────────┐    │
│  │               Load Balancer (ALB)                   │    │
│  └───────┬────────────────────────────────────────────┘    │
│          │                                                   │
│    ┌─────┴─────┬──────────┬──────────┐                     │
│    ▼           ▼          ▼          ▼                     │
│  ┌────┐     ┌────┐     ┌────┐     ┌────┐                  │
│  │ VM1│     │ VM2│     │ VM3│     │ VMN│                  │
│  │    │     │    │     │    │     │    │                  │
│  │API │     │API │     │API │     │API │                  │
│  └────┘     └────┘     └────┘     └────┘                  │
│    │          │          │          │                      │
│    └──────────┴──────────┴──────────┘                      │
│               │                                             │
│               ▼                                             │
│  ┌────────────────────────────┐                            │
│  │      Shared Storage         │                            │
│  │  • Model artifacts (S3)     │                            │
│  │  • Logs (CloudWatch)        │                            │
│  │  • Metrics (Prometheus)     │                            │
│  └────────────────────────────┘                            │
└─────────────────────────────────────────────────────────────┘
```

### Docker Deployment

```bash
# Build image
docker build -t credit-risk-engine:v1.0.0 .

# Run container
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/models:/app/models \
  -e ENV=production \
  credit-risk-engine:v1.0.0

# Or use docker-compose
docker-compose up -d
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: credit-risk-engine
spec:
  replicas: 3
  selector:
    matchLabels:
      app: credit-risk-api
  template:
    metadata:
      labels:
        app: credit-risk-api
    spec:
      containers:
      - name: api
        image: credit-risk-engine:v1.0.0
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
```

## Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| **Latency (p50)** | 35ms | Single prediction |
| **Latency (p95)** | 80ms | Includes SHAP |
| **Latency (p99)** | 120ms | Cold start + SHAP |
| **Throughput** | 500 req/s | Per instance |
| **Memory** | 2-4 GB | With models loaded |
| **CPU** | 1-2 cores | Optimal performance |
| **Startup Time** | 10-15s | Model loading |

## Scalability

**Horizontal Scaling:**
- Stateless API design
- Load balancer distribution
- Auto-scaling based on CPU/memory
- Target: 10,000 req/s with 20 instances

**Optimization Tips:**
- Cache feature engineering results
- Batch SHAP computations
- Use model quantization
- Implement request queuing

## Security Considerations

1. **Input Validation**: Pydantic schemas
2. **Rate Limiting**: Token bucket algorithm
3. **API Keys**: JWT authentication
4. **Encryption**: TLS 1.3 in transit
5. **PII Protection**: Hash sensitive fields
6. **Audit Logging**: All decisions logged

## Monitoring & Observability

**Metrics to Track:**
- Request rate & latency
- Error rates (4xx, 5xx)
- Model inference time
- Feature drift (PSI)
- Decision distribution
- Memory & CPU usage

**Alerting Rules:**
- PSI > 0.15 on critical features
- Error rate > 1%
- Latency p99 > 200ms
- Memory usage > 90%
- Unusual rejection rate changes

---

**Last Updated**: January 2026  
**Version**: 1.0.0
