import pandas as pd
import os
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# Cache for loaded data
_dashboard_data = None
_controls = None
_telemetry_index = 0

def get_data_dir() -> str:
    """Get the data directory path"""
    return os.path.join(os.path.dirname(__file__), "data")

def load_dashboard_data() -> pd.DataFrame:
    """Load dashboard data from Excel, cached"""
    global _dashboard_data
    if _dashboard_data is not None:
        return _dashboard_data

    try:
        excel_path = os.path.join(get_data_dir(), "rss_dashboard_dataset_built_recalc.xlsx")
        _dashboard_data = pd.read_excel(excel_path, sheet_name="Dashboard_Data")
        logger.info(f"Loaded {len(_dashboard_data)} rows from dashboard data")
        return _dashboard_data
    except Exception as e:
        logger.error(f"Failed to load dashboard data: {e}")
        # Return empty DataFrame as fallback
        return pd.DataFrame()

def load_controls() -> Dict[str, Any]:
    """Load controls from Excel, cached"""
    global _controls
    if _controls is not None:
        return _controls

    try:
        excel_path = os.path.join(get_data_dir(), "rss_dashboard_dataset_built_recalc.xlsx")
        controls_df = pd.read_excel(excel_path, sheet_name="Controls")
        _controls = dict(zip(controls_df["Prototype Control Parameters"], controls_df["Unnamed: 1"]))
        logger.info(f"Loaded {len(_controls)} control parameters")
        return _controls
    except Exception as e:
        logger.error(f"Failed to load controls: {e}")
        # Return default controls
        return {
            "DLS normal max (deg/100ft)": 2.0,
            "DLS block max (deg/100ft)": 3.0,
            "Vibration caution max (g)": 0.5,
            "WOB low preference (klbf)": 20,
            "WOB high preference (klbf)": 60,
            "Confidence threshold": 0.5,
        }

def get_next_telemetry() -> Dict[str, Any]:
    """Get next telemetry record from dataset, cycling through"""
    global _telemetry_index
    df = load_dashboard_data()

    if df.empty:
        return {}

    if _telemetry_index >= len(df):
        _telemetry_index = 0

    row = df.iloc[_telemetry_index]
    _telemetry_index += 1

    # Map Excel columns to our telemetry format
    return {
        "timestamp": str(row.get("Timestamp", "")),
        "depth_ft": float(row.get("Depth_ft", 0)),
        "wob_klbf": float(row.get("WOB_klbf", 0)),
        "torque_kftlb": float(row.get("Torque_kftlb", 0)),
        "rpm": float(row.get("RPM_demo", 0)),
        "vibration_g": float(row.get("Vibration_g", 0)),
        "inclination_deg": float(row.get("Inclination_deg", 0)),
        "azimuth_deg": float(row.get("Azimuth_deg", 0)),
        "rop_ft_hr": float(row.get("ROP_ft_hr", 0)),
        "dls_deg_100ft": float(row.get("DLS_deg_per_100ft", 0)),
        "gamma_gapi": float(row.get("Gamma_gAPI", 0)),
        "resistivity_ohm_m": float(row.get("Resistivity_ohm_m", 0)),
        "phif": float(row.get("PHIF", 0)),
        "vsh": float(row.get("VSH", 0)),
        "sw": float(row.get("SW", 0)),
        "klogh": float(row.get("KLOGH", 0)),
        "formation_class": str(row.get("Formation_Class", "Unknown")),
    }

def get_data_quality() -> Dict[str, Any]:
    """Compute data quality metrics"""
    df = load_dashboard_data()

    if df.empty:
        return {
            "total_rows": 0,
            "missing_rate_by_column": {},
            "gaps_detected": 0,
            "outlier_counts": {"vibration": 0, "dls": 0, "wob": 0}
        }

    total_rows = len(df)

    # Missing rates
    missing_rates = {}
    for col in df.columns:
        missing_rate = df[col].isnull().sum() / total_rows
        if missing_rate > 0:
            missing_rates[col] = round(missing_rate, 3)

    # Gaps detection (simple: based on depth spacing)
    if "Depth_ft" in df.columns:
        depths = df["Depth_ft"].dropna().sort_values()
        gaps = ((depths.diff() > 10).sum()) if len(depths) > 1 else 0
    else:
        gaps = 0

    # Outlier counts (simple z-score approximation)
    outlier_counts = {}
    for col, threshold_col in [("Vibration_g", "vibration"), ("DLS_deg_per_100ft", "dls"), ("WOB_klbf", "wob")]:
        if col in df.columns:
            values = df[col].dropna()
            if len(values) > 0:
                mean_val = values.mean()
                std_val = values.std()
                if std_val > 0:
                    outliers = ((values - mean_val).abs() > 3 * std_val).sum()
                else:
                    outliers = 0
                outlier_counts[threshold_col] = int(outliers)

    return {
        "total_rows": total_rows,
        "missing_rate_by_column": missing_rates,
        "gaps_detected": int(gaps),
        "outlier_counts": outlier_counts
    }