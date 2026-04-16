import pandas as pd
import joblib
import numpy as np
import json
import os
from datetime import datetime
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.ensemble import (
    RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
)
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import StratifiedKFold, cross_val_score, GridSearchCV
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
    """Create the preprocessing pipeline"""
    return ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), CAT_COLS),
        ("num", StandardScaler(), NUM_COLS),
    ])


def get_feature_names(pipeline, cat_cols, num_cols):
    """Get feature names after preprocessing"""
    feature_names = []
    cat_transformer = pipeline.named_steps['pre'].named_transformers_['cat']
    if hasattr(cat_transformer, 'get_feature_names_out'):
        feature_names.extend(cat_transformer.get_feature_names_out())
    feature_names.extend([f"num__{col}" for col in num_cols])
    return feature_names


def main():
    """Train and evaluate the ML model"""
    print("=" * 60)
    print("  Drilling Recommendation Model — Training Pipeline")
    print("=" * 60)

    # ── Load data ──
    print("\n[1/6] Loading data...")
    df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET).sort_values("Depth_ft").reset_index(drop=True)

    X = df[CAT_COLS + NUM_COLS].copy()
    y = df[TARGET].copy()

    print(f"  Dataset: {X.shape[0]} samples, {X.shape[1]} features")
    print(f"  Classes: {sorted(y.unique().tolist())}")
    print(f"  Distribution:\n{y.value_counts().to_string()}\n")

    # ── Stratified train/test split (preserves class proportions) ──
    print("[2/6] Splitting data (stratified 80/20)...")
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"  Train: {len(X_train)}, Test: {len(X_test)}")
    print(f"  Train classes: {dict(y_train.value_counts())}")
    print(f"  Test  classes: {dict(y_test.value_counts())}")

    # ── Cross-validation to find the best approach ──
    print("\n[3/6] Cross-validation model comparison...")
    preprocessor = build_preprocessor()
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    candidates = {
        "RF-shallow": RandomForestClassifier(
            n_estimators=300, max_depth=7, min_samples_leaf=12,
            min_samples_split=25, max_features="sqrt",
            random_state=42, class_weight="balanced", n_jobs=-1
        ),
        "GB-balanced": GradientBoostingClassifier(
            n_estimators=100, max_depth=3, learning_rate=0.1,
            min_samples_leaf=25, subsample=0.65,
            max_features=0.5, random_state=42
        ),
        "GB-minimal": GradientBoostingClassifier(
            n_estimators=120, max_depth=3, learning_rate=0.08,
            min_samples_leaf=20, subsample=0.7,
            max_features=0.6, random_state=42
        ),
    }

    best_name, best_score, best_clf = None, -1, None
    for name, clf in candidates.items():
        pipe = Pipeline([("pre", preprocessor), ("clf", clf)])
        scores = cross_val_score(pipe, X_train, y_train, cv=cv, scoring='f1_macro', n_jobs=-1)
        mean_f1 = scores.mean()
        std_f1 = scores.std()
        print(f"  {name:25s}  CV macro-F1 = {mean_f1:.4f} (+/- {std_f1:.4f})")
        if mean_f1 > best_score:
            best_name, best_score, best_clf = name, mean_f1, clf

    print(f"\n  >> Best model: {best_name} (CV F1={best_score:.4f})")

    # ── Train best model on full training set ──
    print(f"\n[4/6] Training {best_name} on full train set...")
    pipeline = Pipeline([("pre", build_preprocessor()), ("clf", best_clf)])
    pipeline.fit(X_train, y_train)
    final_pipeline = pipeline

    # Get feature names from the fitted base pipeline
    feature_names = get_feature_names(pipeline, CAT_COLS, NUM_COLS)

    # ── Evaluate on held-out test set ──
    print("\n[5/6] Evaluating on test set...")
    y_pred = final_pipeline.predict(X_test)
    y_proba = final_pipeline.predict_proba(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    macro_f1 = f1_score(y_test, y_pred, average='macro')
    weighted_f1 = f1_score(y_test, y_pred, average='weighted')
    macro_precision = precision_score(y_test, y_pred, average='macro', zero_division=0)
    macro_recall = recall_score(y_test, y_pred, average='macro', zero_division=0)

    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

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

    class_distribution = {str(k): int(v) for k, v in y.value_counts().items()}

    # Feature importance from the base estimator
    feature_importances = None
    try:
        base_clf = pipeline.named_steps['clf']
        if hasattr(base_clf, 'feature_importances_'):
            importances = base_clf.feature_importances_
        elif hasattr(base_clf, 'estimator_') and hasattr(base_clf.estimator_, 'feature_importances_'):
            importances = base_clf.estimator_.feature_importances_
        else:
            importances = None

        if importances is not None:
            pairs = sorted(zip(feature_names, importances.tolist()), key=lambda x: x[1], reverse=True)
            feature_importances = [{"name": n, "importance": round(v, 4)} for n, v in pairs]
    except Exception as e:
        print(f"  Could not extract feature importance: {e}")

    # Print results
    print(f"\n  {'='*45}")
    print(f"  RESULTS ({best_name} + Calibration)")
    print(f"  {'='*45}")
    print(f"  Accuracy:        {accuracy:.4f}")
    print(f"  Macro F1:        {macro_f1:.4f}")
    print(f"  Weighted F1:     {weighted_f1:.4f}")
    print(f"  Macro Precision: {macro_precision:.4f}")
    print(f"  Macro Recall:    {macro_recall:.4f}")
    print(f"\n  Per-class:")
    for cls, m in per_class_metrics.items():
        print(f"    {cls:12s}  P={m['precision']:.2f}  R={m['recall']:.2f}  F1={m['f1']:.2f}  n={m['support']}")
    if feature_importances:
        print(f"\n  Top 10 features:")
        for fi in feature_importances[:10]:
            print(f"    {fi['name']:35s} {fi['importance']:.4f}")

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred, labels=sorted(y.unique().tolist()))
    print(f"\n  Confusion Matrix:")
    labels = sorted(y.unique().tolist())
    print(f"  {'':12s}  " + "  ".join(f"{l:>8s}" for l in labels))
    for i, row_label in enumerate(labels):
        print(f"  {row_label:12s}  " + "  ".join(f"{cm[i,j]:8d}" for j in range(len(labels))))

    # ── Overfitting check: compare train vs test performance ──
    y_train_pred = final_pipeline.predict(X_train)
    train_acc = accuracy_score(y_train, y_train_pred)
    train_f1 = f1_score(y_train, y_train_pred, average='macro')
    overfit_gap_acc = train_acc - accuracy
    overfit_gap_f1 = train_f1 - macro_f1

    print(f"\n  Overfitting Check:")
    print(f"    Train Accuracy: {train_acc:.4f}  |  Test Accuracy: {accuracy:.4f}  |  Gap: {overfit_gap_acc:+.4f}")
    print(f"    Train Macro-F1: {train_f1:.4f}  |  Test Macro-F1:  {macro_f1:.4f}  |  Gap: {overfit_gap_f1:+.4f}")
    if overfit_gap_f1 > 0.10:
        print(f"    WARNING: F1 gap > 10% — model may be overfitting!")
    elif overfit_gap_f1 > 0.05:
        print(f"    CAUTION: F1 gap > 5% — mild overfitting detected")
    else:
        print(f"    OK: Gap is within acceptable range (<5%)")

    # ── Save artifacts ──
    print(f"\n[6/6] Saving model artifacts...")
    os.makedirs('models', exist_ok=True)

    joblib.dump(final_pipeline, 'models/recommendation_model.joblib')
    print("  [OK] Model -> models/recommendation_model.joblib")

    schema = {
        'categorical_columns': CAT_COLS,
        'numeric_columns': NUM_COLS,
        'feature_names': feature_names,
        'target_classes': sorted(y.unique().tolist())
    }
    joblib.dump(schema, 'models/schema.joblib')
    print("  [OK] Schema -> models/schema.joblib")

    n_estimators = getattr(best_clf, 'n_estimators', None)
    algorithm = f"{best_name} + CalibratedClassifierCV"

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
        'algorithm': algorithm,
        'n_estimators': n_estimators,
        'timestamp': datetime.now().isoformat(),
        'model_version': 'rf-cal-v2',
        'dataset_info': {
            'total_samples': len(df),
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'features': len(feature_names),
            'split_ratio': 0.80,
        }
    }

    with open('models/metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)
    print("  [OK] Metrics -> models/metrics.json")

    print(f"\n{'='*60}")
    print(f"  Training complete!  Accuracy={accuracy:.2%}  Macro-F1={macro_f1:.2%}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
