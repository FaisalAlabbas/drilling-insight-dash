import pandas as pd
import joblib
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import StratifiedKFold, cross_validate
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

def build_preprocessor():
    """Create preprocessing pipeline"""
    return ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), CAT_COLS),
        ("num", StandardScaler(), NUM_COLS),
    ])

def get_models():
    """Return multiple candidate models"""
    preprocessor = build_preprocessor()
    
    models = {
        "RandomForest": Pipeline([
            ("pre", preprocessor),
            ("clf", RandomForestClassifier(
                n_estimators=500,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                class_weight="balanced",
                n_jobs=-1
            ))
        ]),
        "GradientBoosting": Pipeline([
            ("pre", preprocessor),
            ("clf", GradientBoostingClassifier(
                n_estimators=500,
                learning_rate=0.05,
                max_depth=5,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                subsample=0.8
            ))
        ])
    }
    
    return models

def main():
    """Train and evaluate models"""
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
    
    models = get_models()
    best_model_name = None
    best_f1_score = -1
    results = {}
    
    # Evaluate each model
    for model_name, model in models.items():
        print(f"Evaluating {model_name}...")
        
        # Cross-validation on training data
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        cv_scores = cross_validate(
            model, X_train, y_train, cv=cv,
            scoring=['accuracy', 'precision_weighted', 'recall_weighted', 'f1_weighted'],
            n_jobs=-1
        )
        
        cv_f1 = cv_scores['test_f1_weighted'].mean()
        cv_acc = cv_scores['test_accuracy'].mean()
        
        # Train on full training set
        model.fit(X_train, y_train)
        
        # Test set evaluation
        y_pred = model.predict(X_test)
        test_acc = accuracy_score(y_test, y_pred)
        test_f1 = f1_score(y_test, y_pred, average='weighted')
        test_prec = precision_score(y_test, y_pred, average='weighted', zero_division=0)
        test_rec = recall_score(y_test, y_pred, average='weighted', zero_division=0)
        
        results[model_name] = {
            'cv_f1': cv_f1,
            'cv_acc': cv_acc,
            'test_acc': test_acc,
            'test_f1': test_f1,
            'test_precision': test_prec,
            'test_recall': test_rec,
            'model': model,
            'pred': y_pred
        }
        
        print(f"  CV F1: {cv_f1:.4f}, CV Acc: {cv_acc:.4f}")
        print(f"  Test F1: {test_f1:.4f}, Test Acc: {test_acc:.4f}\n")
        
        if test_f1 > best_f1_score:
            best_f1_score = test_f1
            best_model_name = model_name
    
    # Use best model
    print(f"Best model: {best_model_name} (F1: {best_f1_score:.4f})\n")
    best_model = results[best_model_name]['model']
    best_pred = results[best_model_name]['pred']
    
    # Calibrate for probability estimates (optional)
    print("Using Random Forest directly (no calibration)...")
    final_model = best_model
    
    y_pred_final = final_model.predict(X_test)
    final_f1 = f1_score(y_test, y_pred_final, average='weighted')
    print(f"Final F1 Score: {final_f1:.4f}\n")
    
    # Detailed evaluation
    print("=" * 60)
    print("DETAILED CLASSIFICATION REPORT (Test Set)")
    print("=" * 60)
    print(classification_report(y_test, y_pred_final))
    
    print("Confusion Matrix:")
    cm = confusion_matrix(y_test, y_pred_final)
    print(cm)
    print()
    
    # Save model
    print("Saving model...")
    joblib.dump(final_model, 'models/recommendation_model.pkl')
    print("Model saved to models/recommendation_model.pkl\n")
    
    # Feature importance (if available)
    try:
        clf = final_model.named_steps['clf']
        if hasattr(clf, 'feature_importances_'):
            pre = final_model.named_steps['pre']
            feature_names = []
            
            # Get cat feature names
            if hasattr(pre.named_transformers_['cat'], 'get_feature_names_out'):
                feature_names.extend(pre.named_transformers_['cat'].get_feature_names_out())
            
            # Add numeric feature names
            feature_names.extend(NUM_COLS)
            
            importances = clf.feature_importances_
            top_features = sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)[:10]
            
            print("Top 10 Important Features:")
            for fname, importance in top_features:
                print(f"  {fname}: {importance:.4f}")
    except Exception as e:
        print(f"Could not extract feature importance: {e}")

if __name__ == "__main__":
    main()