# Drilling Insight Dashboard

A real-time drilling operations monitoring system with AI-powered decision support, built for oil and gas industry professionals. Monitor telemetry data, receive intelligent recommendations, and manage safety gates to optimize drilling performance and prevent costly incidents.

## 🚀 Key Features

- **Real-time Telemetry Monitoring**: Live visualization of drilling parameters with interactive charts
- **AI-Powered Recommendations**: Machine learning model provides operational insights and safety alerts
- **Safety Gate System**: Automated thresholds and controls to prevent hazardous conditions (ACCEPTED/REDUCED/REJECTED)
- **Data-Driven Operations**: Excel-based dataset integration with formation data and operational limits
- **Data Quality Monitoring**: Real-time metrics for data completeness, gaps, and outliers
- **Export Functionality**: CSV export of telemetry and decision data for analysis
- **Role-Based Access**: Dedicated views for Engineers, Operators, and Administrators
- **Alert Management**: Comprehensive alert system with unread filtering and historical tracking
- **Reporting & Analytics**: Historical data analysis and performance reporting tools

## 🛠 Tech Stack

- **Frontend**: React 18 + TypeScript + Vite
- **UI Framework**: Tailwind CSS + shadcn/ui components
- **Backend**: FastAPI (Python) with Uvicorn server
- **AI/ML**: Rule-based decision engine with configurable thresholds
- **Data Processing**: Pandas + OpenPyXL for Excel dataset integration
- **API Communication**: RESTful APIs with React Query for state management
- **Deployment**: Node.js for frontend build, Python virtual environment for backend

## 📸 Screenshots

_Coming soon - Dashboard screenshots will be added here_

## 🎯 Demo Flow

1. **Live Monitoring**: View real-time drilling telemetry with interactive charts and backend-driven data
2. **AI Evaluation**: Input current parameters to get AI recommendations with configurable safety gates
3. **Data Quality**: Monitor data completeness, identify gaps and outliers in real-time
4. **Alert Management**: Monitor and manage safety alerts across the system
5. **Historical Analysis**: Review past operations and performance metrics
6. **Export Data**: Download telemetry and decision data as CSV for external analysis
7. **Admin Controls**: Configure operational thresholds and system parameters

## 🏃‍♂️ Local Setup

### Prerequisites

- **Node.js 18+** - For frontend development
- **Python 3.8+** - For backend AI service
- **pip** - Python package manager

### Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd drilling-insight-dash
   ```

2. **Install frontend dependencies**

   ```bash
   npm ci
   ```

3. **Install backend dependencies**

   ```bash
   cd ai_service
   pip install -r requirements.txt
   cd ..
   ```

4. **Place the dataset file**

   ```bash
   # Place your Excel dataset in the ai_service/data/ directory
   # Expected filename: rss_dashboard_dataset_built_recalc.xlsx
   # The file should contain 'Dashboard_Data' and 'Controls' sheets
   ```

5. **Train the AI model** (if needed)

   ```bash
   cd ai_service
   python train.py
   cd ..
   ```

6. **Configure environment**

   ```bash
   cp .env.example .env.local
   # Edit .env.local if needed (default should work for local development)
   ```

7. **Start the application**

   ```bash
   # Terminal 1: Start backend
   cd ai_service
   python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000

   # Terminal 2: Start frontend
   npm run dev
   ```

8. **Access the dashboard**
   - Frontend: http://localhost:8080
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## 🤖 AI Training (Optional)

The system supports both rule-based and ML-based recommendations. For ML predictions:

### Prerequisites

- Excel dataset: `ai_service/data/rss_dashboard_dataset_built_recalc.xlsx`
- Dataset should contain `Dashboard_Data` sheet with telemetry and `Recommendation` target

### Training Steps

```bash
# Navigate to AI service
cd ai_service

# Train the model
python train.py

# Verify the trained model
python evaluate.py

# Start the service (model will be auto-detected)
python -m uvicorn api:app --reload --port 8000
```

### Model Specifications

- **Algorithm**: Random Forest (500 trees) + Probability Calibration
- **Features**: 13 total (12 numeric + 1 categorical)
- **Target**: Steering commands (Build/Hold/Drop/Turn Left/Turn Right)
- **Split**: 80/20 temporal (by depth order)
- **Calibration**: Sigmoid method for confidence scores

### Fallback Behavior

If no trained model is available, the system automatically falls back to rule-based recommendations while maintaining all safety gates and data quality features.

### Running Frontend + Backend Together

For development, you can run both services simultaneously:

```bash
# Option 1: Manual (two terminals)
# Terminal 1: Backend
cd ai_service && python -m uvicorn api:app --reload --port 8000

# Terminal 2: Frontend
npm run dev

# Option 2: Using the dev:all script (requires concurrently)
npm run dev:all
```

The frontend automatically connects to the backend using the `VITE_AI_BASE_URL` environment variable.

## 🤖 Backend AI Service

The backend provides REST API endpoints for AI predictions, data streaming, and system monitoring.

### Key Endpoints

- `GET /health` - System health check
- `GET /config` - Operational limits and thresholds configuration
- `GET /telemetry/next` - Next telemetry packet from dataset
- `GET /telemetry/quality` - Data quality metrics and statistics
- `POST /predict` - AI decision recommendations with formation data lookup
- `POST /batch-predict` - Bulk predictions for historical analysis

### Data Integration

The system integrates with Excel datasets containing:

- **Dashboard_Data sheet**: Telemetry and formation data by depth
- **Controls sheet**: Operational limits and thresholds

Place your dataset at `ai_service/data/rss_dashboard_dataset_built_recalc.xlsx` for data-driven operation.

### Connecting Frontend to Backend

The frontend connects to the backend using the `VITE_AI_BASE_URL` environment variable:

```typescript
const baseUrl = import.meta.env.VITE_AI_BASE_URL || "http://localhost:8000";
```

Set this in your `.env.local` file:

```
VITE_AI_BASE_URL=http://localhost:8000
```

## 📁 Folder Structure

```
drilling-insight-dash/
├── ai_service/              # Python FastAPI backend
│   ├── api.py              # Main API application
│   ├── train.py            # ML model training script
│   ├── models/             # Trained models and data
│   └── requirements.txt    # Python dependencies
├── public/                  # Static assets
├── src/                     # React frontend
│   ├── components/         # Reusable UI components
│   ├── pages/              # Page components
│   ├── lib/                # Utilities and API clients
│   └── hooks/              # Custom React hooks
├── .env.example            # Environment variables template
├── package.json            # Node.js dependencies and scripts
├── vite.config.ts          # Vite configuration
└── README.md               # This file
```

## ⚙️ Configuration

### AI Model Thresholds

The system uses configurable thresholds for safety gates and recommendations:

- **Pressure Limits**: Maximum/minimum drilling pressure thresholds
- **Temperature Ranges**: Safe operating temperature windows
- **Vibration Thresholds**: Acceptable vibration levels
- **Flow Rate Controls**: Optimal mud flow parameters

These are loaded from `ai_service/models/rss_dashboard_dataset_built_recalc.xlsx` and can be adjusted by updating the Excel file and retraining the model.

### Environment Variables

- `VITE_AI_BASE_URL`: Backend API base URL (default: http://localhost:8000)

## 🔧 Troubleshooting

### Common Issues

**CORS Errors**

- Ensure backend is running on the correct port (8000)
- Check that frontend `.env.local` has correct `VITE_AI_BASE_URL`
- Backend CORS is configurable via `AI_CORS_ORIGINS` environment variable
- Default allowed origins: `localhost:5173`, `127.0.0.1:5173`

**API Not Responding**

- Verify backend server is running: `curl http://localhost:8000/health`
- Check backend logs for errors
- Ensure Python virtual environment is activated
- Backend startup log will show if ML model was loaded or fell back to rules

**Wrong Environment Variable**

- Confirm `.env.local` exists in project root
- Check variable name: `VITE_AI_BASE_URL` (not `VITE_API_URL`)
- Restart frontend dev server after changing env vars

**Port Conflicts**

- Backend default port: 8000
- Frontend default port: 5173 (Vite dev server)
- Change ports in startup commands if needed

**Model Loading Errors**

- Ensure `recommendation_model.joblib` exists in `ai_service/models/`
- Run `python train.py` in `ai_service/` directory if model is missing
- Check train.py logs for errors
- System will automatically fall back to rule-based recommendations if model unavailable
- Check `ai_service/models/metrics.json` for model performance details

**Missing Dataset**

- Ensure Excel file is at `ai_service/models/rss_dashboard_dataset_built_recalc.xlsx`
- File should contain `Dashboard_Data` and `Controls` sheets
- System works offline with mock data if dataset is missing

**Backend Connection Issues**

- Backend has 15-second timeout for API calls
- If backend is unresponsive, frontend automatically falls back to mock recommendations
- Check frontend browser console for detailed error messages
- Review backend logs at startup for model loading status

### Getting Help

- Check API documentation: http://localhost:8000/docs
- Review backend logs in terminal for error details
- Frontend logs visible in browser console (F12)
- Verify all prerequisites are installed
- Test individual components: frontend alone, backend alone

## 📋 Development Workflow

### Quick Start Development

```bash
# 1. Install all dependencies
npm ci
cd ai_service && pip install -r requirements.txt && cd ..

# 2. Train the ML model (if you have the dataset)
cd ai_service
python train.py
cd ..

# 3. Start both services in one command
npm run dev:all

# 4. Access the dashboard
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000/docs
```

### Running Quality Checks

```bash
# Frontend linting and formatting
npm run lint                # Run ESLint
npm run format              # Auto-format with Prettier
npm run check:format        # Check formatting without changes

# Frontend tests
npm run test                # Run all tests once
npm run test:watch          # Watch mode during development

# Backend tests
cd ai_service
pytest test_api.py -v       # Run API tests
cd ..

# Build frontend
npm run build               # Production build
```

### Development Without ML Model

The system is designed to work offline with rule-based fallback:

```bash
# Start without training a model - system will use rules-based recommendations
npm run dev:all
```

The frontend will display "Model Not Available" in the AI Evaluation tab, but:

- All other features work normally
- Safety gates function correctly
- Rules-based steering recommendations are provided
- No dataset or training required for development

### Code Quality Standards

Before committing:

1. **Format code**: `npm run format`
2. **Run linter**: `npm run lint` (must pass with 0 warnings)
3. **Run tests**: `npm run test` (all tests must pass)
4. **Build check**: `npm run build` (production build must succeed)
5. **Backend tests**: `cd ai_service && pytest test_api.py && cd ..`

## 🔄 CI/CD Pipeline

This project uses GitHub Actions for continuous integration:

### Workflow

- **Trigger**: On every push and pull request to `main` or `develop` branches
- **Frontend checks**: Lint, format check, tests, build (Node 18.x & 20.x)
- **Backend checks**: Tests with pytest (Python 3.9-3.12)
- **Security checks**: Basic hardcoded secret detection

### Viewing CI Results

1. Go to **Actions** tab on GitHub
2. Select the workflow run to see detailed logs
3. All checks must pass before merging to main

### Local CI Check

Run the same checks locally before pushing:

```bash
# Frontend
npm run lint && npm run check:format && npm run test && npm run build

# Backend
cd ai_service
pip install -r requirements.txt
pytest test_api.py -v
cd ..
```

## 📊 Backend Configuration

### Environment Variables

The backend supports configuration via environment variables:

```bash
# Model and data paths
EXCEL_PATH=models/rss_dashboard_dataset_built_recalc.xlsx
MODEL_PATH=models/recommendation_model.joblib
SCHEMA_PATH=models/schema.joblib
METRICS_PATH=models/metrics.json

# CORS security (comma-separated list)
AI_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Logging
LOG_LEVEL=INFO

# Safety thresholds
CONFIDENCE_THRESHOLD=0.6
DLS_BLOCK_THRESHOLD=3.0
```

### Backend Logging

The backend uses structured JSON logging:

- **Startup**: Model loading status and version
- **Predictions**: Each prediction logs recommendation, confidence, gate status, and source (ML or rules)
- **Errors**: Detailed error messages with context

View logs in the terminal where backend is running.

## 📦 API Response Format

All API responses include structured decision records:

```json
{
  "recommendation": "Build",
  "confidence": 0.85,
  "gate_status": "ACCEPTED",
  "alert_message": "Recommendation accepted",
  "decision_record": {
    "timestamp": "2024-04-07T12:00:00Z",
    "model_version": "rf-cal-v1",
    "steering_command": "Build",
    "confidence_score": 0.85,
    "gate_outcome": "ACCEPTED",
    "execution_status": "SENT",
    "event_tags": []
  }
}
```

## ✅ Testing

### Frontend Tests

```bash
npm run test                # Run tests once
npm run test:watch          # Watch mode
```

Tests cover:

- AI Recommendation component styling for different gate outcomes
- Telemetry to prediction payload mapping
- Validation of required fields

### Backend Tests

```bash
cd ai_service
pytest test_api.py -v       # Verbose output
pytest test_api.py -k confidence  # Run specific test
```

Tests cover:

- `/health` endpoint returns 200
- `/predict` returns decision record with required fields
- Gate logic rejects high vibration and high DLS cases
- Fallback to rules-based recommendations when model unavailable
- Error handling and validation

## 📄 License

This project is proprietary software for drilling operations monitoring.
