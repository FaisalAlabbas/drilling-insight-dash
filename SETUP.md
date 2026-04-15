# Drilling Insight Dashboard - Complete Setup & Run Guide

A real-time AI-powered drilling operations monitoring dashboard with machine learning recommendations, alert system, and comprehensive analytics.

## 📋 Prerequisites

- **Python 3.8+** - Download from [python.org](https://www.python.org/downloads/)
- **Node.js 18+** - For frontend development
- **pip** - Python package manager (comes with Python)

## 🚀 Quick Start (Windows PowerShell)

### Option 1: One-Click Startup (Easiest)

```powershell
# Run the startup script (opens both servers automatically)
.\startup.ps1
```

This will:

1. ✓ Install Python dependencies
2. ✓ Train ML model (if needed)
3. ✓ Configure frontend
4. ✓ Launch backend server (http://localhost:8001)
5. ✓ Launch frontend server (http://localhost:8080)
6. ✓ Open dashboard in browser

### Option 2: Manual Setup

**Terminal 1 - Backend (FastAPI)**

```powershell
cd ai_service
python -m pip install -r requirements.txt
python train.py              # Only needed first time
python -m uvicorn api:app --reload --host 0.0.0.0 --port 8001
```

**Terminal 2 - Frontend (React)**

```powershell
npm install                  # Only needed first time
npm run dev
```

Then open your browser to **http://localhost:8080**

## 🛑 Troubleshooting

### Backend won't start

```powershell
# Check Python version
python --version

# Reinstall dependencies
cd ai_service
python -m pip install --upgrade -r requirements.txt

# Check if port 8001 is free
netstat -ano | findstr :8001
```

### Model not found

```powershell
# Train the model manually
cd ai_service
python train.py

# Verify model was created
ls models/recommendation_model.pkl
```

### Frontend won't start

```powershell
# Clear cache and reinstall
rm -r node_modules
npm install
npm run dev
```

### API connection error

```powershell
# 1. Verify backend is running on port 8001
curl http://localhost:8001/health

# 2. Check .env.local exists
cat .env.local
# Should contain: VITE_AI_BASE_URL=http://localhost:8001

# 3. Restart both servers in order: backend first, then frontend
```

## 📊 System Overview

### Backend (Python/FastAPI)

- **Location**: `ai_service/api.py`
- **Port**: http://localhost:8001
- **Endpoints**:
  - `POST /predict` - Get steering recommendation
  - `POST /batch-predict` - Batch predictions
  - `GET /health` - Health status
  - `GET /model-info` - Model details
  - `GET /docs` - API documentation (Swagger UI)

### Frontend (React/TypeScript/Vite)

- **Location**: `src/pages/Index.tsx`
- **Port**: http://localhost:8080
- **Modules**:
  - **Live Monitoring** - Real-time telemetry & AI recommendations
  - **Alerts** - Alert feed with severity filtering & unread tracking
  - **Run History** - Decision records with export to CSV
  - **Reporting** - Performance/safety/operations reports (Engineer+)
  - **Admin Panel** - User management & system configuration (Admin only)

## 🔑 Role-Based Access

| Feature         | Operator | Engineer | Admin |
| --------------- | -------- | -------- | ----- |
| Live Monitoring | ✓        | ✓        | ✓     |
| Alerts          | ✓        | ✓        | ✓     |
| Run History     | ✓        | ✓        | ✓     |
| Reporting       | ✗        | ✓        | ✓     |
| AI Evaluation   | ✗        | ✓        | ✓     |
| Admin Panel     | ✗        | ✗        | ✓     |

## 📡 Real-Time Features

- **Telemetry Streaming**: 1Hz/10Hz configurable rates
- **Live Predictions**: 5-second polling from backend
- **Alert Generation**: Data-driven based on threshold violations
- **Persistent Storage**: Alerts saved in browser localStorage
- **Health Monitoring**: Continuous backend availability checking

## 🏗️ Architecture

```
Frontend (React 18, TypeScript, Vite)
         ↓
    Dashboard Context (State Management)
         ↓
    API Service (Axios HTTP Client)
         ↓
Backend (FastAPI, Python)
    ↓         ↓        ↓
Model   Gating  Logging
```

## 🎯 Key Capabilities

✅ **ML Model**: Random Forest classifier (77.4% accuracy)

- 5 steering command classes: Build, Hold, Drop, Turn Left, Turn Right
- 13 input features (geological + operational telemetry)
- Real-time confidence scoring

✅ **Safety Gating**: Multi-layer validation

- Confidence threshold (50%)
- DLS (Dogleg Severity) limits
- Vibration thresholds
- WOB (Weight on Bit) constraints

✅ **Alert System**: Intelligent notifications

- Threshold-based generation
- Severity levels: CRITICAL, WARN, INFO
- Read/unread tracking
- Persistent history

✅ **Analytics**: Comprehensive reporting

- Performance metrics (confidence, acceptance rate)
- Safety analysis (rejections, alerts)
- Operations monitoring (uptime, latency, data quality)

## 🔧 Configuration

### Backend Settings (`ai_service/api.py`)

```python
CONTROLS = {
    "DLS normal max (deg/100ft)": 2.0,        # Caution threshold
    "DLS block max (deg/100ft)": 3.0,         # Critical threshold
    "Vibration caution max (g)": 0.5,         # Vibration limit
    "WOB low preference (klbf)": 20,          # Min WOB
    "WOB high preference (klbf)": 60,         # Max WOB
    "Confidence threshold": 0.5,              # Min confidence
}
```

### Frontend Settings (`src/lib/api-service.ts`)

```typescript
const API_BASE_URL = import.meta.env.VITE_AI_BASE_URL || "http://localhost:8001";
```

## 📈 Performance Targets

- **Backend Response Time**: < 50ms
- **Model Prediction Latency**: < 10ms
- **System Uptime**: > 99.5%
- **API Error Rate**: < 0.5%
- **Frontend Responsiveness**: 60 FPS

## 🐛 Debug Mode

### Backend Logging

```powershell
# Run with detailed logging
python -m uvicorn api:app --reload --log-level debug
```

### Frontend Console

```javascript
// Check in browser DevTools Console
localStorage.getItem("drilling_alerts"); // View saved alerts
```

## 📚 API Response Examples

### Prediction Response

```json
{
  "recommendation": "Hold",
  "confidence": 0.787,
  "gate_status": "ACCEPTED",
  "alert_message": "Normal operation",
  "decision_record": {
    "timestamp": "2024-01-15T10:30:45.123Z",
    "steering_command": "Hold",
    "confidence_score": 0.787,
    "gate_outcome": "ACCEPTED",
    "execution_status": "SENT"
  }
}
```

### Health Check Response

```json
{
  "ok": true,
  "status": "healthy",
  "model_loaded": true,
  "uptime_seconds": 3847,
  "timestamp": "2024-01-15T10:30:45.123Z"
}
```

## 🚢 Production Deployment

For production, consider:

1. **Backend**:
   - Use production ASGI server (Gunicorn + Uvicorn)
   - Environment variables for configuration
   - Logging to file with rotation
   - Model versioning system

2. **Frontend**:
   - Build optimized production bundle: `npm run build`
   - Serve with static web server (nginx)
   - CDN for assets
   - Compressed bundle (gzip)

3. **Infrastructure**:
   - Load balancing for multiple backend instances
   - Database for persistent alert storage
   - Real-time WebSocket support for telemetry
   - API rate limiting and authentication

## 📞 Support

For issues or questions:

1. Check the **Troubleshooting** section above
2. Review backend logs: `http://localhost:8001/docs`
3. Check browser console for frontend errors
4. Verify all prerequisites are installed correctly

## 📄 License

This project is part of a Senior Project for real-time drilling operations monitoring.

---

**Happy drilling! 🛢️**
