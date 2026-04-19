# Server Configuration

## Port Configuration (FIXED)

**Frontend:** `http://localhost:8080`
**Backend:** `http://localhost:8001`

These ports are configured across the entire codebase and should NOT be changed.

### Environment Files

#### .env
```
VITE_AI_BASE_URL=http://localhost:8001
```

#### .env.local
```
VITE_AI_BASE_URL=http://localhost:8001
```

#### .env.development
```
VITE_AI_BASE_URL=http://localhost:8001
```

### Frontend Configuration

**File:** `vite.config.ts`
- Port: 8080
- Host: `::`

**Run Command:**
```bash
npm run dev
```
Access: `http://localhost:8080`

### Backend Configuration

**File:** `ai_service/settings.py`
- Port: 8001
- Host: `0.0.0.0`

**Run Command:**
```bash
cd ai_service
python -m uvicorn main:app --host 0.0.0.0 --port 8001
```
Access: `http://localhost:8001`

### CORS Configuration

**File:** `ai_service/main.py`

Allowed origins include:
- `http://localhost:8080`
- `http://127.0.0.1:8080`
- `http://localhost:8081`
- `http://127.0.0.1:8081`
- `http://localhost:8082`
- `http://127.0.0.1:8082`

### Quick Start

1. **Terminal 1 - Backend:**
```bash
cd ai_service
python -m uvicorn main:app --host 0.0.0.0 --port 8001
```

2. **Terminal 2 - Frontend:**
```bash
npm run dev
```

3. **Access Application:**
```
http://localhost:8080
```

### API Endpoints

All API endpoints are accessible at:
- Base URL: `http://localhost:8001`
- Health: `http://localhost:8001/health`
- Model Metrics: `http://localhost:8001/model/metrics`
- Predictions: `http://localhost:8001/predict`

### Important Notes

- Frontend automatically connects to backend at `http://localhost:8001`
- CORS is configured to allow requests from port 8080
- Do NOT change these ports without updating all configuration files
- The `.env` files have been configured with these ports as defaults
