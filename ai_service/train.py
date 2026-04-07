import pandas as pd
import joblib
import numpy as np
import json
import os
from datetime import datetime
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    classification_report, confusion_matrix, accuracy_score,
    precision_score, recall_score, f1_score
)
import warnings
warnings.filterwarnings('ignore')

EXCEL_PATH = "models/rss_dashboard_dataset_built_recalc.xlsx"
SHEET = "Dashboard_Data"
TARGET = "Recommendation"

CAT_COLS = ["Formation_Class"]
NUM_COLS = [
    "WOB_klbf", "RPM_demo", "ROP_ft_hr", "PHIF", "VSH", "SW", "KLOGH",
    "Torque_kftlb", "Vibration_g", "DLS_deg_per_100ft",
    "Inclination_deg", "Azimuth_deg"
]

def build_pipeline():
    """Create the ML pipeline with preprocessing and classifier"""
    preprocessor = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), CAT_COLS),
        ("num", StandardScaler(), NUM_COLS),
    ])

    # Base classifier
    rf_classifier = RandomForestClassifier(
        n_estimators=500,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1
    )

    pipeline = Pipeline([
        ("pre", preprocessor),
        ("clf", rf_classifier)
    ])

    return pipeline

def get_feature_names(pipeline, cat_cols, num_cols):
    """Get feature names after preprocessing"""
    # Get feature names from the already fitted preprocessor
    feature_names = []
    # Get categorical feature names
    if hasattr(pipeline.named_steps['pre'].named_transformers_['cat'], 'get_feature_names_out'):
        cat_features = pipeline.named_steps['pre'].named_transformers_['cat'].get_feature_names_out()
        feature_names.extend(cat_features)

    # Add numeric feature names
    feature_names.extend([f"num__{col}" for col in num_cols])
    
    return feature_names
    feature_names.extend(num_cols)

    return feature_names

def main():
    """Train and evaluate the ML model"""
    print("Loading data...")
    df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET).sort_values("Depth_ft").reset_index(drop=True)

    X = df[CAT_COLS + NUM_COLS].copy()
    y = df[TARGET].copy()

    print(f"Dataset shape: {X.shape}")
    print(f"Target distribution:\n{y.value_counts()}\n")

    # Split by depth order (temporal/spatial order - avoid leakage)
    split = int(len(df) * 0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    print(f"Train set: {X_train.shape[0]}, Test set: {X_test.shape[0]}\n")

    # Build and train pipeline
    print("Training Random Forest...")
    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)
    
    final_pipeline = pipeline
    
    final_pipeline = pipeline

    # Get feature names for schema
    feature_names = get_feature_names(pipeline, CAT_COLS, NUM_COLS)

    # Evaluate on test set
    print("Evaluating on test set...")
    y_pred = final_pipeline.predict(X_test)
    y_proba = final_pipeline.predict_proba(X_test)

    # Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    macro_f1 = f1_score(y_test, y_pred, average='macro')
    weighted_f1 = f1_score(y_test, y_pred, average='weighted')

    # Per-class F1 scores
    per_class_f1 = {}
    for class_name in y.unique():
        if class_name in y_test.values:
            class_f1 = f1_score(y_test, y_pred, labels=[class_name], average='macro')
            per_class_f1[class_name] = class_f1

    print(f"\nTest Results:")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Macro F1: {macro_f1:.4f}")
    print(f"Weighted F1: {weighted_f1:.4f}")
    print(f"Per-class F1: {per_class_f1}\n")

    print("=" * 60)
    print("CLASSIFICATION REPORT")
    print("=" * 60)
    print(classification_report(y_test, y_pred))

    print("\nCONFUSION MATRIX")
    print("=" * 60)
    cm = confusion_matrix(y_test, y_pred)
    print(cm)

    # Create models directory if it doesn't exist
    os.makedirs('models', exist_ok=True)

    # Save model
    print("\nSaving model artifacts...")
    joblib.dump(final_pipeline, 'models/recommendation_model.joblib')
    print("✓ Model saved to models/recommendation_model.joblib")

    # Save schema
    schema = {
        'categorical_columns': CAT_COLS,
        'numeric_columns': NUM_COLS,
        'feature_names': feature_names,
        'target_classes': sorted(y.unique().tolist())
    }
    joblib.dump(schema, 'models/schema.joblib')
    print("✓ Schema saved to models/schema.joblib")

    # Save metrics
    metrics = {
        'accuracy': accuracy,
        'macro_f1': macro_f1,
        'weighted_f1': weighted_f1,
        'per_class_f1': per_class_f1,
        'timestamp': datetime.now().isoformat(),
        'model_version': 'rf-cal-v1',
        'dataset_info': {
            'total_samples': len(df),
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'features': len(feature_names)
        }
    }

    with open('models/metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)
    print("✓ Metrics saved to models/metrics.json")

    # Feature importance
    try:
        rf_model = pipeline.named_steps['clf'].estimator_
        if hasattr(rf_model, 'feature_importances_'):
            importances = rf_model.feature_importances_
            top_features = sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)[:10]

            print("\nTop 10 Important Features:")
            for fname, importance in top_features:
                print(".4f")
    except Exception as e:
        print(f"Could not extract feature importance: {e}")

    print("\n🎉 Training complete!")
    print("Run 'python evaluate.py' to verify the saved model.")

if __name__ == "__main__":
    main()
    
