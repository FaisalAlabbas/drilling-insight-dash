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
    macro_precision = precision_score(y_test, y_pred, average='macro', zero_division=0)
    macro_recall = recall_score(y_test, y_pred, average='macro', zero_division=0)

    # Full classification report as dict — has per-class precision/recall/f1/support
    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

    # Build per-class metrics with precision, recall, f1, support
    per_class_metrics = {}
    for class_name in sorted(y.unique().tolist()):
        if class_name in report:
            entry = report[class_name]
            per_class_metrics[class_name] = {
                "precision": round(entry["precision"], 4),
                "recall": round(entry["recall"], 4),
                "f1": round(entry["f1-score"], 4),
                "support": int(entry["support"]),
            }

    # Class distribution from full dataset
    class_distribution = {str(k): int(v) for k, v in y.value_counts().items()}

    # Feature importance from the base Random Forest
    feature_importances = None
    try:
        clf = pipeline.named_steps['clf']
        if hasattr(clf, 'feature_importances_'):
            importances = clf.feature_importances_
        elif hasattr(clf, 'estimator_') and hasattr(clf.estimator_, 'feature_importances_'):
            importances = clf.estimator_.feature_importances_
        else:
            importances = None

        if importances is not None:
            pairs = sorted(zip(feature_names, importances.tolist()), key=lambda x: x[1], reverse=True)
            feature_importances = [{"name": n, "importance": round(v, 4)} for n, v in pairs]
    except Exception as e:
        print(f"Could not extract feature importance: {e}")

    print(f"\nTest Results:")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Macro F1: {macro_f1:.4f}")
    print(f"Weighted F1: {weighted_f1:.4f}")
    print(f"Macro Precision: {macro_precision:.4f}")
    print(f"Macro Recall: {macro_recall:.4f}")
    print(f"\nPer-class metrics:")
    for cls, m in per_class_metrics.items():
        print(f"  {cls}: P={m['precision']:.2f} R={m['recall']:.2f} F1={m['f1']:.2f} support={m['support']}")
    if feature_importances:
        print(f"\nTop 10 features:")
        for fi in feature_importances[:10]:
            print(f"  {fi['name']}: {fi['importance']:.4f}")

    # Create models directory if it doesn't exist
    os.makedirs('models', exist_ok=True)

    # Save model
    print("\nSaving model artifacts...")
    joblib.dump(final_pipeline, 'models/recommendation_model.joblib')
    print("[OK] Model saved to models/recommendation_model.joblib")

    # Save schema
    schema = {
        'categorical_columns': CAT_COLS,
        'numeric_columns': NUM_COLS,
        'feature_names': feature_names,
        'target_classes': sorted(y.unique().tolist())
    }
    joblib.dump(schema, 'models/schema.joblib')
    print("[OK] Schema saved to models/schema.joblib")

    # Save metrics — complete set consumed by frontend AI Evaluation page
    split_ratio = round(split / len(df), 2)
    metrics = {
        'accuracy': accuracy,
        'macro_f1': macro_f1,
        'weighted_f1': weighted_f1,
        'precision': macro_precision,
        'recall': macro_recall,
        'per_class_metrics': per_class_metrics,
        'class_distribution': class_distribution,
        'feature_importances': feature_importances,
        'feature_names': NUM_COLS + CAT_COLS,
        'algorithm': 'RandomForest + CalibratedClassifierCV',
        'n_estimators': 500,
        'timestamp': datetime.now().isoformat(),
        'model_version': 'rf-cal-v1',
        'dataset_info': {
            'total_samples': len(df),
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'features': len(feature_names),
            'split_ratio': split_ratio,
        }
    }

    with open('models/metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)
    print("[OK] Metrics saved to models/metrics.json")

    print("\nTraining complete!")
    print("Run 'python evaluate.py' to verify the saved model.")

if __name__ == "__main__":
    main()
    
