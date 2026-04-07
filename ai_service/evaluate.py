import pandas as pd
import joblib
import json
import numpy as np
from sklearn.metrics import (
    classification_report, confusion_matrix, accuracy_score, f1_score
)

EXCEL_PATH = "models/rss_dashboard_dataset_built_recalc.xlsx"
SHEET = "Dashboard_Data"
TARGET = "Recommendation"

def main():
    """Load saved model and evaluate to verify serialization works"""
    print("Loading saved model and schema...")

    try:
        # Load model and schema
        model = joblib.load('models/recommendation_model.joblib')
        schema = joblib.load('models/schema.joblib')

        with open('models/metrics.json', 'r') as f:
            saved_metrics = json.load(f)

        print("✓ Model and artifacts loaded successfully")
        print(f"Model version: {saved_metrics.get('model_version', 'unknown')}")
        print(f"Training timestamp: {saved_metrics.get('timestamp', 'unknown')}")
        print()

    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("Make sure to run 'python train.py' first to create the model files.")
        return
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return

    # Load test data (same split as training)
    print("Loading test data for evaluation...")
    df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET).sort_values("Depth_ft").reset_index(drop=True)

    X = df[schema['categorical_columns'] + schema['numeric_columns']].copy()
    y = df[TARGET].copy()

    # Same split as training
    split = int(len(df) * 0.8)
    X_test = X.iloc[split:]
    y_test = y.iloc[split:]

    print(f"Test set: {X_test.shape[0]} samples")
    print()

    # Evaluate
    print("Evaluating loaded model on test set...")
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)

    # Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    macro_f1 = f1_score(y_test, y_pred, average='macro')
    weighted_f1 = f1_score(y_test, y_pred, average='weighted')

    print("EVALUATION RESULTS")
    print("=" * 50)
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Macro F1: {macro_f1:.4f}")
    print(f"Weighted F1: {weighted_f1:.4f}")
    print()

    # Compare with saved metrics
    print("COMPARISON WITH SAVED METRICS")
    print("=" * 50)
    print(f"Saved Accuracy:  {saved_metrics['accuracy']:.4f}")
    print(f"Current Accuracy: {accuracy:.4f}")
    print(f"Difference: {(accuracy - saved_metrics['accuracy']):.6f}")
    print()

    print(f"Saved Macro F1:  {saved_metrics['macro_f1']:.4f}")
    print(f"Current Macro F1: {macro_f1:.4f}")
    print(f"Difference: {(macro_f1 - saved_metrics['macro_f1']):.6f}")
    print()

    # Detailed report
    print("CLASSIFICATION REPORT")
    print("=" * 50)
    print(classification_report(y_test, y_pred))

    print("CONFUSION MATRIX")
    print("=" * 50)
    cm = confusion_matrix(y_test, y_pred)
    print(cm)

    # Sample predictions
    print("\nSAMPLE PREDICTIONS")
    print("=" * 50)
    sample_indices = np.random.choice(len(X_test), min(5, len(X_test)), replace=False)

    for idx in sample_indices:
        actual = y_test.iloc[idx]
        predicted = y_pred[idx]
        confidence = np.max(y_proba[idx])

        print(f"Sample {idx}:")
        print(f"  Actual: {actual}")
        print(f"  Predicted: {predicted}")
        print(f"  Confidence: {confidence:.4f}")
        print()

    print("✅ Model evaluation complete!")

if __name__ == "__main__":
    main()