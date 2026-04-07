# Drilling Insight AI Service

Python FastAPI backend providing AI-powered steering recommendations for drilling operations.

## Setup (Windows PowerShell)

1. **Create virtual environment**

   ```powershell
   python -m venv .venv
   ```

2. **Activate virtual environment**

   ```powershell
   .venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**

   ```powershell
   pip install -r requirements.txt
   ```

4. **Run the service**

   ```powershell
   python -m uvicorn api:app --reload --port 8000
   ```

5. **Test endpoints**
   - Health check: `curl http://localhost:8000/health`
   - API docs: Open `http://localhost:8000/docs` in browser
   - Test prediction:
     ```powershell
     curl -X POST http://localhost:8000/predict \
       -H "Content-Type: application/json" \
       -d '{
         "WOB_klbf": 35.0,
         "RPM_demo": 110.0,
         "ROP_ft_hr": 75.0,
         "PHIF": 0.18,
         "VSH": 0.25,
         "SW": 0.35,
         "KLOGH": 120.0,
         "Formation_Class": "Sandstone",
         "Torque_kftlb": 25000.0,
         "Vibration_g": 0.5,
         "DLS_deg_per_100ft": 2.0,
         "Inclination_deg": 30.0,
         "Azimuth_deg": 90.0
       }'
     ```

## Train the ML Model

The service supports both rule-based and ML-based recommendations. To use the ML model:

1. **Place the dataset**

   ```powershell
   # Ensure rss_dashboard_dataset_built_recalc.xlsx is in the data/ directory
   ```

2. **Train the model**

   ```powershell
   python train.py
   ```

   This will:
   - Load the Excel dataset from `data/rss_dashboard_dataset_built_recalc.xlsx`
   - Train a Random Forest classifier with probability calibration
   - Save model artifacts to `models/` directory
   - Print evaluation metrics on test set

3. **Verify the trained model**

   ```powershell
   python evaluate.py
   ```

   This loads the saved model and evaluates it again to ensure serialization works.

4. **Start the service**
   ```powershell
   python -m uvicorn api:app --reload --port 8000
   ```
   The API will automatically detect and use the trained model for predictions.

### Model Details

- **Algorithm**: Random Forest Classifier (500 trees) with probability calibration
- **Features**: 12 numerical + 1 categorical (Formation_Class)
- **Target**: Steering recommendation (Build/Hold/Drop/Turn Left/Turn Right)
- **Split**: Temporal order (first 80% by depth for training, last 20% for testing)
- **Calibration**: Sigmoid calibration for reliable probability estimates
- **Fallback**: Rule-based logic when model is not available

### Model Artifacts

Training saves the following files to `models/`:

- `recommendation_model.joblib` - Trained and calibrated model
- `schema.joblib` - Feature schema and preprocessing information
- `metrics.json` - Performance metrics and metadata

  ```

  ```

## API Endpoints

- `GET /health` - Service health check
- `POST /predict` - Get AI steering recommendation
- `GET /docs` - Interactive API documentation (Swagger UI)

## Features

- Rule-based AI recommendations (Build/Hold/Drop)
- Safety gating (ACCEPTED/REDUCED/REJECTED)
- Confidence scoring
- Detailed decision records
- CORS enabled for frontend integration
