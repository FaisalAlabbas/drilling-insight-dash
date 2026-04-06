# Quick Reference Guide

## 🟢 Both Servers Running?

- Backend: http://localhost:8000 (Uvicorn)
- Frontend: http://localhost:8081 (Vite)
- Dashboard: http://localhost:8081

## 📡 API Endpoints Reference

### Health & Status
```
GET /health
  Returns: { ok, status, model_loaded, uptime_seconds, timestamp }
  
GET /model-info  
  Returns: { model_loaded, model_type, classes, schema, controls }
```

### Predictions
```
POST /predict
  Input: PredictRequest
  Returns: { recommendation, confidence, gate_status, alert_message, decision_record }
  
POST /batch-predict
  Input: List[PredictRequest]
  Returns: { predictions: List, count: int }
```

## 🏗️ Project Structure

```
drilling-insight-dash/
├── ai_service/                 # Python backend
│   ├── api.py                 # FastAPI application
│   ├── train.py               # Model training script
│   ├── requirements.txt        # Python dependencies
│   └── models/
│       └── recommendation_model.pkl  # Trained ML model
├── src/                        # React frontend
│   ├── components/            # UI components
│   │   ├── LiveMonitoringView.tsx
│   │   ├── AlertsView.tsx
│   │   ├── HistoryView.tsx
│   │   ├── ReportingView.tsx
│   │   ├── AdminPanel.tsx
│   │   └── ... (20+ other components)
│   ├── pages/
│   │   ├── Index.tsx          # Main dashboard
│   │   ├── AIEvaluation.tsx   # Model evaluation
│   │   └── NotFound.tsx
│   ├── lib/
│   │   ├── dashboard-context.tsx  # State management
│   │   ├── api-service.ts         # Backend communication
│   │   ├── types.ts               # TypeScript types
│   │   ├── mock-data.ts           # Test data generation
│   │   └── utils.ts               # Utilities
│   └── App.tsx               # Main app component
├── package.json              # Node dependencies
├── vite.config.ts           # Vite configuration
├── tsconfig.json            # TypeScript configuration
├── SETUP.md                 # Setup instructions
├── SYSTEM_STATUS.md         # Current system status
└── startup.ps1              # Windows startup script
```

## 🚀 Common Tasks

### START SERVERS
**Terminal 1 - Backend:**
```powershell
cd ai_service
python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```powershell
npm run dev
# Vite will try 8080, fallback to 8081 if busy
```

### TRAIN MODEL
```powershell
cd ai_service
python train.py
```

### TEST API
```powershell
# Health check
curl http://localhost:8000/health

# Single prediction
$body = @{...} | ConvertTo-Json
Invoke-WebRequest -Uri http://localhost:8000/predict -Method POST -Body $body

# API docs (interactive)
Open http://localhost:8000/docs
```

### VIEW DASHBOARD
```
http://localhost:8081
```

### CHANGE USER ROLE
Edit `src/lib/dashboard-context.tsx` line 37:
```typescript
const [role, setRole] = useState<UserRole>('Engineer');  // Operator, Engineer, or Admin
```

## 📊 Live Features

| Feature | Update Rate | Source |
|---------|------------|--------|
| Telemetry | 1Hz/10Hz | Mock generator (configurable) |
| Predictions | 5 seconds | Backend API |
| Alerts | Per prediction | Threshold-based generation |
| Stats | Real-time | Computed from buffers |
| Charts | Real-time | Recharts components |

## 🔧 Configuration

### Backend Settings
File: `ai_service/api.py`, lines ~60-80

```python
CONTROLS = {
    "DLS normal max (deg/100ft)": 2.0,        # Yellow zone
    "DLS block max (deg/100ft)": 3.0,         # Red zone  
    "Vibration caution max (g)": 0.5,
    "WOB low preference (klbf)": 20,
    "WOB high preference (klbf)": 60,
    "Confidence threshold": 0.5,
}
```

### Frontend Settings
File: `.env.local`
```
VITE_API_URL=http://localhost:8000
```

## 🎯 Key Data Flows

### Real-Time Monitoring Flow
```
User Opens Dashboard
        ↓
Telemetry starts streaming (1Hz)
        ↓
Every 5 sec: fetch prediction from API
        ↓
Model returns: recommendation + confidence
        ↓
Safety gate validates against constraints
        ↓
Decision record created
        ↓
If thresholds exceeded: generate alert
        ↓
UI updates with new data
        ↓
Alerts persisted to localStorage
```

### Telemetry → Prediction Flow
```
Random telemetry packet generated
        ↓
Map to model input features
        ↓
POST to /predict endpoint
        ↓
Backend preprocessing:
  - One-hot encode Formation_Class
  - StandardScale numeric features
        ↓
Random Forest model predicts
        ↓
Safety gate evaluates:
  - Confidence >= threshold?
  - DLS <= limits?
  - Vibration <= max?
  - WOB in preferred band?
        ↓
Return decision_record to frontend
        ↓
Update dashboard + add to history
```

## 📝 Common Response Examples

### Successful Prediction
```json
{
  "recommendation": "Hold",
  "confidence": 0.74,
  "gate_status": "ACCEPTED",
  "alert_message": "Normal operation",
  "decision_record": {
    "timestamp": "2026-04-06T12:51:01Z",
    "steering_command": "Hold",
    "confidence_score": 0.74,
    "gate_outcome": "ACCEPTED",
    "execution_status": "SENT",
    "event_tags": []
  }
}
```

### Rejected Prediction  
```json
{
  "recommendation": "Build",
  "confidence": 0.42,
  "gate_status": "REJECTED",
  "alert_message": "Confidence 0.42 below threshold 0.5",
  "decision_record": {
    "timestamp": "2026-04-06T12:51:01Z",
    "steering_command": "Build",
    "confidence_score": 0.42,
    "gate_outcome": "REJECTED",
    "rejection_reason": "LOW_CONFIDENCE",
    "execution_status": "BLOCKED",
    "fallback_mode": "HOLD_STEERING",
    "event_tags": ["Confidence 0.42 below threshold 0.5"]
  }
}
```

### Health Check
```json
{
  "ok": true,
  "status": "healthy",
  "model_loaded": true,
  "uptime_seconds": 245.67,
  "timestamp": "2026-04-06T12:52:15.123Z"
}
```

## 🐛 Troubleshooting Quick Fixes

| Issue | Solution |
|-------|----------|
| Backend won't start | `python -m pip install -r ai_service/requirements.txt` |
| Model not found | `cd ai_service && python train.py` |
| Port 8000 in use | `netstat -ano \| findstr :8000` to find process |
| Port 8080 in use | Vite auto-tries 8081, 8082, etc. |
| API returns 500 error | Check backend logs for error details |
| Frontend can't reach API | Verify `.env.local` has `VITE_API_URL=http://localhost:8000` |
| Alerts not persisting | Check browser localStorage (F12 > Application) |
| Charts not rendering | Clear browser cache, refresh page |

## 📚 File Dependencies

**Frontend → Backend:**
- `src/lib/api-service.ts` → `ai_service/api.py:8000`
- `src/lib/dashboard-context.tsx` → `getRecommendation()` from api-service
- `src/components/LiveMonitoringView.tsx` → real-time predictions

**Backend → Files:**
- `ai_service/api.py` → `models/recommendation_model.pkl`
- `train.py` → `models/rss_dashboard_dataset_built_recalc.xlsx`
- `api.py` → `models/Controls` sheet from Excel

## 🎓 Understanding Model Classes

The Random Forest model predicts one of 5 steering commands:

1. **Build** - Increase inclination (build angle)
2. **Hold** - Maintain current angle (most common)
3. **Drop** - Decrease inclination
4. **Turn Left** - Rotate azimuth counter-clockwise
5. **Turn Right** - Rotate azimuth clockwise

Confidence scores range from 0-1 (0-100%).

## 📊 Model Performance

```
Test Accuracy:        77.4%
Test F1-Score:        0.74 (weighted)
Cross-Val F1:         0.78
Most Frequent Class:  "Hold" (68% of training data)

Per-Class Performance:
┌─────────────┬───────────┬────────┬──────────┐
│ Class       │ Precision │ Recall │ F1-Score │
├─────────────┼───────────┼────────┼──────────┤
│ Build       │ 0.60      │ 1.00   │ 0.75     │
│ Hold        │ 0.82      │ 0.86   │ 0.84     │
│ Drop        │ 0.75      │ 0.75   │ 0.75     │
│ Turn Left   │ 0.00      │ 0.00   │ 0.00     │
│ Turn Right  │ 0.00      │ 0.00   │ 0.00     │
└─────────────┴───────────┴────────┴──────────┘
```

## 🔗 Useful URLs

- Dashboard: http://localhost:8081
- Backend Docs: http://localhost:8000/docs  
- Health Check: http://localhost:8000/health
- Model Info: http://localhost:8000/model-info
- AI Evaluation: http://localhost:8081/ai-evaluation

## 💾 Persistent Data

- **Alerts**: Stored in localStorage `drilling_alerts` key
- **Telemetry**: Kept in memory (300 packets buffer)
- **Decisions**: Kept in memory (200 records buffer)
- **Model**: Pickled file on disk (`models/recommendation_model.pkl`)

## 🎨 UI Theming

- Dark theme with CSS variables
- Colors: Primary (cyan), Red, Yellow, Green for status
- Responsive design (mobile-first)
- shadcn/ui components with Tailwind CSS

---

**Pro Tip**: Open two terminal windows - one for backend, one for frontend - to see logs side-by-side! 🚀
