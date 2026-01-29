# ⚡ Quick Start - Get Running in 5 Minutes

Follow these steps to get the Credit Risk AI Engine frontend running on your machine.

## 🎯 Prerequisites Check

```bash
node --version  # Should be v18.0.0 or higher
npm --version   # Should be v9.0.0 or higher
```

If not installed, download from: https://nodejs.org/

---

## 🚀 Setup Steps

### Step 1: Navigate to Frontend Directory

```powershell
cd C:\credit-risk-engine\frontend
```

### Step 2: Install Dependencies

```powershell
npm install
```

This will install:
- React 18.2.0
- Vite 5.0.8
- Tailwind CSS 3.4.0
- Axios 1.6.5
- Lucide Icons

**Estimated time**: 1-2 minutes

### Step 3: Configure Environment

```powershell
copy .env.example .env
```

The default `.env` is already configured for local development:
```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### Step 4: Start the Backend (Separate Terminal)

Open a **new PowerShell window** and run:

```powershell
cd C:\credit-risk-engine
python src/api/api_service.py
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Model loaded with 80 features
```

**Keep this terminal running!**

### Step 5: Start the Frontend

Back in your frontend terminal:

```powershell
npm run dev
```

You should see:
```
VITE v5.0.8  ready in 500 ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

### Step 6: Open in Browser

Open: **http://localhost:5173**

---

## 🎉 Test the Application

### Quick Test

1. Click **"Load Example Applicant"** button
2. Click **"Check Credit Risk"**
3. See results appear in ~500ms

### Manual Test

Fill out the form:
- **Full Name**: John Doe
- **Age**: 30
- **Annual Income**: ₹500,000
- **Savings Balance**: ₹200,000
- **Credit Score**: 700
- **Loan Amount**: ₹300,000
- **Loan Term**: 36 months
- **Employment Status**: Full-time Employed
- **Existing Debt**: ₹50,000
- **Education Level**: Bachelor's Degree

Click **"Check Credit Risk"** and view results!

---

## 🐛 Troubleshooting

### Problem: `npm install` fails

**Solution**:
```powershell
npm cache clean --force
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm install
```

### Problem: Port 5173 already in use

**Solution**:
```powershell
# Find and kill the process
netstat -ano | findstr :5173
taskkill /PID <PID> /F

# Or change port in vite.config.js
```

### Problem: Backend connection fails

**Check 1**: Is backend running?
```powershell
curl http://127.0.0.1:8000/health
```

**Check 2**: CORS configured?
- Open `src/api/api_service.py`
- Verify line ~117: `allow_origins=["http://localhost:5173", ...]`

**Check 3**: Firewall blocking?
```powershell
# Allow through Windows Firewall
New-NetFirewallRule -DisplayName "Python Dev" -Direction Inbound -Program "python.exe" -Action Allow
```

### Problem: "Module not found" errors

**Solution**: Reinstall dependencies
```powershell
Remove-Item -Recurse -Force node_modules
npm install
```

---

## 📝 Development Tips

### Hot Reload

Both frontend and backend support hot reload:
- **Frontend**: Save any `.jsx` file → instant browser update
- **Backend**: Changes require manual restart

### Browser Console

Open DevTools (F12) to see:
- Network requests to backend
- API responses
- Any errors

### API Testing

Test backend directly:
```powershell
curl -X POST http://127.0.0.1:8000/score `
  -H "Content-Type: application/json" `
  -d '{"age": 30, "income_total": 50000, "credit_amount": 10000}'
```

---

## 🎨 Customization

### Change Colors

Edit `tailwind.config.js`:
```js
colors: {
  primary: {
    500: '#3b82f6',  // Change to your brand color
  }
}
```

Save → See instant changes!

### Add Fields

Edit `src/App.jsx`:
1. Add state: `const [newField, setNewField] = useState('')`
2. Add input: `<input value={newField} onChange={e => setNewField(e.target.value)} />`
3. Update `src/api.js` to include in feature conversion

---

## 📊 Project Structure

```
frontend/
├── src/
│   ├── App.jsx          ← Main component (edit UI here)
│   ├── api.js           ← API client (edit requests here)
│   ├── config.js        ← Environment config
│   └── index.css        ← Global styles
├── package.json         ← Dependencies
├── vite.config.js       ← Build config
└── .env                 ← Environment variables
```

---

## 🔄 Stopping the Servers

### Stop Frontend
Press `Ctrl+C` in the frontend terminal

### Stop Backend
Press `Ctrl+C` in the backend terminal

---

## 🚀 Next Steps

1. ✅ **Working locally?** → See `DEPLOYMENT.md` to deploy to production
2. 📹 **Want to showcase?** → See `DEMO_VIDEO_SCRIPT.md` for LinkedIn demo
3. 📚 **Need more details?** → See `README.md` for full documentation

---

## 💡 Common Commands

```powershell
# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Clean install
Remove-Item -Recurse node_modules; npm install
```

---

## ✅ Success Checklist

- [ ] Node.js v18+ installed
- [ ] Dependencies installed (`npm install`)
- [ ] Backend running on port 8000
- [ ] Frontend running on port 5173
- [ ] Browser shows form at http://localhost:5173
- [ ] Example applicant test works
- [ ] Results display correctly

---

**🎉 Congratulations! Your FinTech app is running!**

If you have issues, check the troubleshooting section or open an issue on GitHub.
