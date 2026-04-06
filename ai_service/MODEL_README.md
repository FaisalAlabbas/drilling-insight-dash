# Drilling Recommendation Classification Model

## Overview

A multi-class classification model trained on drilling operational data to predict steering recommendations based on real-time well parameters.

**Model Type:** Random Forest Classifier  
**Training Samples:** 151 (120 train / 31 test)  
**Output Classes:** Build, Hold, Drop, Turn Left, Turn Right

---

## Model Performance

### Test Set Metrics
- **Overall Accuracy:** 77.4%
- **Weighted F1-Score:** 0.74
- **Weighted Precision:** 0.71
- **Weighted Recall:** 0.77

### Per-Class Performance

| Class | Precision | Recall | F1-Score | Support |
|-------|-----------|--------|----------|---------|
| Build | 0.60 | 1.00 | 0.75 | 3 |
| Drop | 0.75 | 0.75 | 0.75 | 4 |
| Hold | 0.82 | 0.86 | 0.84 | 21 |
| Turn Left | 0.00 | 0.00 | 0.00 | 2 |
| Turn Right | 0.00 | 0.00 | 0.00 | 1 |

**Note:** Classes with 0% recall (Turn Left/Right) had very few test samples. The model performs well on the dominant classes (Build, Hold, Drop).

---

## Top 10 Feature Importance

The model relies most heavily on these drilling parameters:

1. **PHIF** (Porosity) - 15.56%
2. **DLS_deg_per_100ft** (Dogleg Severity) - 14.93%
3. **VSH** (Shale Volume) - 12.55%
4. **Azimuth_deg** (Azimuth) - 10.06%
5. **Vibration_g** (Vibration) - 8.63%
6. **Torque_kftlb** (Torque) - 6.56%
7. **Inclination_deg** (Inclination) - 5.95%
8. **ROP_ft_hr** (Rate of Penetration) - 5.82%
9. **WOB_klbf** (Weight on Bit) - 5.59%
10. **RPM_demo** (RPM) - 4.86%

---

## Usage

### Option 1: Direct Python Function

```python
from api import get_recommendation

# Prepare input features
inputs = {
    "WOB_klbf": 35,           # Weight on Bit (1000s lbf)
    "RPM_demo": 110,           # Rotations per minute
    "ROP_ft_hr": 75,           # Rate of penetration (ft/hr)
    "PHIF": 0.22,              # Porosity index
    "VSH": 0.32,               # Shale volume
    "SW": 0.42,                # Water saturation
    "KLOGH": 0.52,             # Permeability log
    "Torque_kftlb": 3500,      # Torque (kft-lbf)
    "Vibration_g": 0.35,       # Vibration (g)
    "DLS_deg_per_100ft": 1.8,  # Dogleg severity
    "Inclination_deg": 50,     # Well inclination
    "Azimuth_deg": 105,        # Azimuth
    "Formation_Class": "Limestone"  # Formation type
}

# Get recommendation
result = get_recommendation(inputs)

print(f"Recommendation: {result['recommendation']}")
print(f"Confidence: {result['confidence']:.2%}")
print(f"All class probabilities: {result['all_classes']}")
```

### Option 2: FastAPI Endpoint

```bash
# Start the API server
uvicorn api:app --host 0.0.0.0 --port 8000
```

```bash
# Make a prediction request
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "WOB_klbf": 35,
    "RPM_demo": 110,
    "ROP_ft_hr": 75,
    "PHIF": 0.22,
    "VSH": 0.32,
    "SW": 0.42,
    "KLOGH": 0.52,
    "Torque_kftlb": 3500,
    "Vibration_g": 0.35,
    "DLS_deg_per_100ft": 1.8,
    "Inclination_deg": 50,
    "Azimuth_deg": 105,
    "Formation_Class": "Limestone"
  }'
```

---

## Input Features

All 13 input features are required:

### Drilling Parameters
- **WOB_klbf** (float): Weight on Bit in thousands of pounds-force
- **RPM_demo** (float): Rotations per minute
- **ROP_ft_hr** (float): Rate of penetration in feet per hour
- **Torque_kftlb** (float): Torque in thousand foot-pounds
- **Vibration_g** (float): Vibration magnitude in g-forces

### Formation Properties
- **PHIF** (float): Porosity index [0-1]
- **VSH** (float): Shale volume [0-1]
- **SW** (float): Water saturation [0-1]
- **KLOGH** (float): Permeability log value
- **Formation_Class** (str): Formation type (e.g., "Shale", "Sandstone", "Limestone")

### Well Geometry
- **DLS_deg_per_100ft** (float): Dogleg severity in degrees per 100 feet
- **Inclination_deg** (float): Well inclination in degrees
- **Azimuth_deg** (float): Azimuth direction in degrees

---

## Output

The `get_recommendation()` function returns:

```python
{
    "recommendation": "Hold",                    # Predicted steering command
    "confidence": 0.4437,                        # Confidence score [0-1]
    "all_classes": {                             # Probability for each class
        "Build": 0.2534,
        "Drop": 0.0656,
        "Hold": 0.4437,
        "Turn Left": 0.0953,
        "Turn Right": 0.1425
    }
}
```

---

## Model Files

- **models/recommendation_model.pkl** - Trained Random Forest model with preprocessing pipeline
- **train.py** - Training script
- **api.py** - FastAPI application with `get_recommendation()` function
- **test_prediction.py** - Test script with example predictions

---

## Recommendations

1. **Low Confidence Predictions:** Consider requesting human approval for recommendations with confidence < 0.5
2. **Class Imbalance:** Turn Left/Right classes have limited training data. Use caution when model predicts these classes
3. **Retraining:** Periodically retrain the model as new drilling data becomes available
4. **Feature Quality:** Ensure all input features are validated and within historical data ranges

---

## Data Split Strategy

The model uses **temporal/spatial ordering** for the train-test split (80/20) to avoid data leakage:
- Training samples are sorted by depth and take the first 80% (Depth 0-3800 ft)
- Test samples are the remaining 20% (Depth 3800+ ft)

This mimics real-world prediction scenarios where the model predicts ahead of drilling progress.

