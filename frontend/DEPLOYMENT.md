# 🚀 Complete Deployment Guide
## Credit Risk AI Engine - Backend & Frontend

---

## 📋 Table of Contents
1. [Backend Deployment (FastAPI)](#backend-deployment)
2. [Frontend Deployment (React)](#frontend-deployment)
3. [Environment Variables](#environment-variables)
4. [Post-Deployment Testing](#testing)
5. [Troubleshooting](#troubleshooting)

---

## 🖥️ Backend Deployment

### Option 1: Render (Recommended)

#### Step 1: Prepare Files

Create `render.yaml` in project root:

```yaml
services:
  - type: web
    name: credit-risk-api
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "uvicorn src.api.api_service:app --host 0.0.0.0 --port $PORT"
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: PORT
        generateValue: true
```

Create `requirements.txt`:

```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pandas==2.1.4
numpy==1.26.3
scikit-learn==1.4.0
lightgbm==4.2.0
xgboost==2.0.3
shap==0.44.1
joblib==1.3.2
pyyaml==6.0.1
loguru==0.7.2
requests==2.31.0
python-multipart==0.0.6
```

#### Step 2: Deploy

1. **Sign up**: https://render.com
2. **New Web Service** → Connect GitHub repo
3. **Configure**:
   - Name: `credit-risk-api`
   - Branch: `main`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn src.api.api_service:app --host 0.0.0.0 --port $PORT`
4. **Advanced**:
   - Add `models/` folder to persisted disk
   - Health Check Path: `/health`
5. **Deploy**: Click "Create Web Service"

#### Step 3: Upload Model Files

After deployment:

```bash
# Option 1: Via Render Shell
# Dashboard → Shell → Upload files to models/

# Option 2: Via Git LFS (if models < 100MB)
git lfs install
git lfs track "models/*.pkl"
git add .gitattributes models/
git commit -m "Add model files"
git push
```

#### Step 4: Verify

```bash
curl https://your-app.onrender.com/health
```

---

### Option 2: Railway

#### Step 1: Install Railway CLI

```bash
npm i -g @railway/cli
```

#### Step 2: Deploy

```bash
railway login
railway init
railway up
```

#### Step 3: Configure

```bash
railway variables set PYTHON_VERSION=3.11
railway variables set PORT=8000
```

#### Step 4: Get URL

```bash
railway domain
```

---

### Option 3: Azure App Service

#### Step 1: Install Azure CLI

```bash
az login
```

#### Step 2: Create Resources

```bash
# Create resource group
az group create --name credit-risk-rg --location eastus

# Create App Service plan
az appservice plan create \
  --name credit-risk-plan \
  --resource-group credit-risk-rg \
  --sku B1 --is-linux

# Create web app
az webapp create \
  --name credit-risk-api \
  --resource-group credit-risk-rg \
  --plan credit-risk-plan \
  --runtime "PYTHON:3.11"
```

#### Step 3: Deploy Code

```bash
az webapp up \
  --name credit-risk-api \
  --resource-group credit-risk-rg \
  --runtime "PYTHON:3.11"
```

#### Step 4: Configure Startup

```bash
az webapp config set \
  --resource-group credit-risk-rg \
  --name credit-risk-api \
  --startup-file "uvicorn src.api.api_service:app --host 0.0.0.0 --port 8000"
```

---

## 🌐 Frontend Deployment

### Option 1: Vercel (Recommended)

#### Step 1: Install Vercel CLI

```bash
npm i -g vercel
```

#### Step 2: Build Frontend

```bash
cd frontend
npm install
npm run build
```

#### Step 3: Deploy

```bash
vercel
```

Follow prompts:
- **Project name**: `credit-risk-frontend`
- **Framework**: React (detected automatically)
- **Build command**: `npm run build`
- **Output directory**: `dist`

#### Step 4: Set Environment Variables

```bash
vercel env add VITE_API_BASE_URL production
# Enter: https://your-backend.onrender.com
```

#### Step 5: Deploy to Production

```bash
vercel --prod
```

Your app: `https://credit-risk-frontend.vercel.app`

---

### Option 2: Netlify

#### Step 1: Install Netlify CLI

```bash
npm i -g netlify-cli
```

#### Step 2: Build

```bash
cd frontend
npm install
npm run build
```

#### Step 3: Deploy

```bash
netlify login
netlify init
netlify deploy --prod --dir=dist
```

#### Step 4: Configure Environment Variables

Dashboard → Site Settings → Environment Variables:
- `VITE_API_BASE_URL` = `https://your-backend.onrender.com`

#### Step 5: Trigger Rebuild

```bash
netlify build
netlify deploy --prod --dir=dist
```

---

### Option 3: GitHub Pages

#### Step 1: Update `vite.config.js`

```js
export default defineConfig({
  base: '/credit-risk-engine/',  // Your repo name
  plugins: [react()],
  server: { host: true, port: 5173 }
})
```

#### Step 2: Build

```bash
npm run build
```

#### Step 3: Deploy Script

Create `deploy.sh`:

```bash
#!/usr/bin/env sh
set -e
npm run build
cd dist
git init
git add -A
git commit -m 'Deploy to GitHub Pages'
git push -f git@github.com:your-username/credit-risk-engine.git main:gh-pages
cd -
```

Run:

```bash
chmod +x deploy.sh
./deploy.sh
```

#### Step 4: Enable GitHub Pages

Repository Settings → Pages → Source: `gh-pages` branch

---

## 🔐 Environment Variables

### Backend (.env or deployment platform)

```env
# Production
ENVIRONMENT=production
LOG_LEVEL=INFO

# Model Settings
MODEL_VERSION=1.0.0
MODEL_PATH=/app/models

# API Settings
API_RATE_LIMIT=100
CORS_ORIGINS=https://your-frontend.vercel.app,http://localhost:5173

# Optional: Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# Optional: Monitoring
SENTRY_DSN=https://...
```

### Frontend (.env.production)

```env
VITE_API_BASE_URL=https://your-backend.onrender.com
```

---

## ✅ Post-Deployment Testing

### Backend Health Check

```bash
curl https://your-backend.onrender.com/health
```

Expected:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_version": "1.0.0"
}
```

### Frontend Test

1. Open: `https://your-frontend.vercel.app`
2. Click "Load Example Applicant"
3. Submit form
4. Verify results display

### End-to-End Test

```bash
curl -X POST https://your-backend.onrender.com/score \
  -H "Content-Type: application/json" \
  -d '{
    "age": 30,
    "income_total": 50000,
    "credit_amount": 10000,
    "ext_source_1": 0.7,
    "ext_source_2": 0.65,
    "ext_source_3": 0.6
  }'
```

---

## 🐛 Troubleshooting

### Issue 1: CORS Errors

**Symptom**: "Access-Control-Allow-Origin" error in browser console

**Solution**: Update backend CORS in `api_service.py`:

```python
allow_origins=[
    "https://your-frontend.vercel.app",
    "http://localhost:5173"
]
```

Redeploy backend.

---

### Issue 2: Model Not Found

**Symptom**: 500 error, "Model not loaded"

**Solution**: Upload model files to backend

**Render**:
1. Dashboard → Shell
2. Upload `models/*.pkl` files

**Railway**:
```bash
railway shell
# Then upload files via SFTP
```

**Azure**:
```bash
az webapp deploy --src-path models.zip --name credit-risk-api --resource-group credit-risk-rg
```

---

### Issue 3: Build Fails

**Symptom**: Deployment fails during build

**Solutions**:

**Backend**:
- Check `requirements.txt` has all dependencies
- Verify Python version (3.11 recommended)
- Check logs: `railway logs` or Render dashboard

**Frontend**:
- Clear cache: `rm -rf node_modules package-lock.json`
- Reinstall: `npm install`
- Check Node version: v18+ required

---

### Issue 4: Slow Response Times

**Symptom**: API takes > 2 seconds

**Solutions**:
1. **Upgrade plan**: Free tiers have cold starts
2. **Enable caching**: Add Redis for model caching
3. **Optimize model**: Use smaller model variant
4. **Health check**: Keep backend warm with scheduled pings

**Keep-Alive Script** (run on Vercel Cron or external):

```js
// keep-alive.js
setInterval(() => {
  fetch('https://your-backend.onrender.com/health')
    .then(res => console.log('Ping:', res.status))
    .catch(err => console.error(err));
}, 5 * 60 * 1000); // Every 5 minutes
```

---

### Issue 5: Environment Variables Not Working

**Symptom**: App uses default localhost URL

**Solutions**:

**Vercel**:
```bash
vercel env add VITE_API_BASE_URL production
vercel --prod
```

**Netlify**:
- Dashboard → Site Settings → Environment Variables
- Trigger rebuild after adding

**Render**:
- Dashboard → Environment → Add Variable
- Auto-deploys on save

---

## 📊 Monitoring & Logging

### Backend Logs

**Render**:
```bash
# Real-time logs
Dashboard → Logs tab
```

**Railway**:
```bash
railway logs
```

**Azure**:
```bash
az webapp log tail --name credit-risk-api --resource-group credit-risk-rg
```

### Frontend Analytics

Add to `index.html`:

```html
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Render
        env:
          RENDER_API_KEY: ${{ secrets.RENDER_API_KEY }}
        run: |
          curl -X POST https://api.render.com/deploy/srv-xxxxx?key=$RENDER_API_KEY

  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Vercel
        env:
          VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
        run: |
          npm i -g vercel
          cd frontend
          vercel --token=$VERCEL_TOKEN --prod
```

---

## 🎉 Success Checklist

- [ ] Backend deployed and accessible
- [ ] Frontend deployed and accessible
- [ ] CORS configured correctly
- [ ] Environment variables set
- [ ] Model files uploaded
- [ ] Health checks passing
- [ ] End-to-end test successful
- [ ] Monitoring enabled
- [ ] Custom domain configured (optional)
- [ ] SSL/HTTPS enabled
- [ ] CI/CD pipeline working

---

## 🔗 Quick Links

- **Render Docs**: https://render.com/docs
- **Vercel Docs**: https://vercel.com/docs
- **Netlify Docs**: https://docs.netlify.com
- **Railway Docs**: https://docs.railway.app
- **Azure App Service**: https://docs.microsoft.com/azure/app-service

---

**Need help? Open an issue on GitHub or reach out via LinkedIn!**
