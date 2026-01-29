# 🚀 Quick Start Guide

## Prerequisites Checklist

- [ ] Python 3.8+ installed
- [ ] 8GB+ RAM available
- [ ] Internet connection
- [ ] Kaggle account (for dataset)

## 5-Minute Setup

### 1. Install Dependencies (2 min)

```bash
# Clone repository
git clone https://github.com/yourusername/credit-risk-engine.git
cd credit-risk-engine

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# Install packages
pip install -r requirements.txt
```

### 2. Download Data (2 min)

**Option A: Kaggle API**
```bash
# Set up Kaggle API credentials
# Place kaggle.json in C:\Users\YourName\.kaggle\

# Download dataset
kaggle competitions download -c home-credit-default-risk
unzip home-credit-default-risk.zip -d data/raw/
```

**Option B: Manual**
- Visit: https://www.kaggle.com/c/home-credit-default-risk/data
- Download `application_train.csv` (minimum)
- Place in `data/raw/`

### 3. Train Model (10 min)

```bash
python scripts/train_model.py
```

You'll see:
```
[STEP 1] Loading Data...
[STEP 2] Preprocessing Data...
[STEP 3] Engineering Features...
[STEP 4] Training Model...
[STEP 5] Evaluating Model...
...
✅ TRAINING COMPLETED
```

### 4. Deploy API (1 min)

```bash
# Start server
cd src/api
python api_service.py
```

Server runs at: http://localhost:8000

### 5. Test API

Open browser: http://localhost:8000/docs

Or run test script:
```bash
python scripts/test_api.py
```

## 🎯 First API Call

```bash
curl -X POST "http://localhost:8000/score" \
  -H "Content-Type: application/json" \
  -d '{
    "age": 35,
    "income_total": 180000,
    "credit_amount": 50000,
    "ext_source_2": 0.75
  }'
```

Expected response:
```json
{
  "pd_score": 0.0342,
  "risk_tier": "A",
  "decision": "APPROVED",
  "credit_limit": 50000,
  "interest_rate": 8.68
}
```

## 🐳 Docker Deployment

```bash
# Build image
docker-compose build

# Start service
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop service
docker-compose down
```

## 📊 View Results

After training, check:

1. **Model Metrics**: `models/credit_risk_model_metrics.pkl`
2. **Performance Plots**: `models/model_performance.png`
3. **SHAP Analysis**: `models/shap_summary.png`
4. **Fairness Report**: `models/fairness_report.csv`

## ❓ Troubleshooting

**Dataset not found?**
```bash
# Ensure files are in data/raw/
ls data/raw/application_train.csv
```

**Import errors?**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**API won't start?**
```bash
# Check port 8000 is free
netstat -ano | findstr :8000
```

**Low memory?**
```python
# In config.yaml, reduce:
shap_sample_size: 500
background_samples: 50
```

## 🎓 Next Steps

1. ✅ Train model
2. ✅ Deploy API
3. 📊 Review performance metrics
4. ⚖️ Check fairness report
5. 🔍 Explore SHAP explanations
6. 🚀 Integrate with your application
7. 📈 Set up production monitoring

## 📚 Resources

- **Full Documentation**: README.md
- **API Docs**: http://localhost:8000/docs
- **Configuration**: config.yaml
- **Dataset Info**: https://www.kaggle.com/c/home-credit-default-risk

## 💡 Pro Tips

1. **Faster Training**: Reduce `n_estimators` in config.yaml
2. **Better Performance**: Add more bureau features
3. **Production Ready**: Set up monitoring alerts
4. **Scale Up**: Use Docker + Kubernetes
5. **CI/CD**: Add GitHub Actions workflow

---

**Time to first prediction: ~15 minutes** ⚡

Need help? Open an issue or reach out!
