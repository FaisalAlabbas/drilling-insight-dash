#!/usr/bin/env python3
"""
Simple Excel to Database Import for Drilling Insight Dashboard.
Uses synchronous SQLAlchemy for telemetry data import.
"""

import os
import sys
import pandas as pd
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, List

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default to SQLite for testing
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from database.db import get_session, SessionLocal
from database.models import Well, TelemetryPacket, SystemConfig
from datetime import datetime

def import_telemetry_from_excel(excel_path: str, well_id: str = "well_001", batch_size: int = 1000) -> Dict[str, Any]:
    """Import telemetry data from Excel file."""
    logger.info(f"Starting telemetry import from {excel_path}")
    
    # Ensure tables exist
    from database.db import create_database
    logger.info("Ensuring database tables exist...")
    create_database()
    logger.info("Database tables created/verified")
    
    try:
        # Read the Dashboard_Data sheet
        df = pd.read_excel(excel_path, sheet_name='Dashboard_Data')
        logger.info(f"Loaded {len(df)} rows from Excel")
        
        # Map column names
        column_mapping = {
            'Timestamp': 'timestamp',
            'Depth_ft': 'depth_ft',
            'WOB_klbf': 'wob_klbf',
            'Torque_kftlb': 'torque_kftlb',
            'RPM_demo': 'rpm',
            'Vibration_g': 'vibration_g',
            'Inclination_deg': 'inclination_deg',
            'Azimuth_deg': 'azimuth_deg',
            'ROP_ft_hr': 'rop_ft_hr',
            'DLS_deg_per_100ft': 'dls_deg_100ft',
            'Gamma_gAPI': 'gamma_gapi',
            'Resistivity_ohm_m': 'resistivity_ohm_m',
            'PHIF': 'phif',
            'VSH': 'vsh',
            'SW': 'sw',
            'KLOGH': 'klogh',
            'Formation_Class': 'formation_class',
        }
        
        # Process data
        session = SessionLocal()
        
        try:
            # Ensure well exists
            well = session.query(Well).filter(Well.id == well_id).first()
            if not well:
                logger.info(f"Creating well {well_id}")
                well = Well(
                    id=well_id,
                    name=f"Well {well_id}",
                    status="active"
                )
                session.add(well)
                session.commit()
            
            inserted_count = 0
            skipped_count = 0
            error_count = 0
            
            # Import in batches
            for idx, row in df.iterrows():
                try:
                    packet_id = str(uuid.uuid4())
                    
                    # Extract and validate data
                    timestamp = row.get('Timestamp')
                    if pd.isna(timestamp):
                        skipped_count += 1
                        continue
                    
                    # Handle timestamp conversion
                    if isinstance(timestamp, str):
                        timestamp = pd.to_datetime(timestamp)
                    elif pd.notna(timestamp):
                        timestamp = pd.Timestamp(timestamp)
                    else:
                        skipped_count += 1
                        continue
                    
                    # Create telemetry packet
                    packet_data = {
                        'id': packet_id,
                        'well_id': well_id,
                        'timestamp': timestamp,
                        'depth_ft': float(row.get('Depth_ft', 0)) if pd.notna(row.get('Depth_ft')) else 0,
                        'wob_klbf': float(row.get('WOB_klbf', 0)) if pd.notna(row.get('WOB_klbf')) else 0,
                        'torque_kftlb': float(row.get('Torque_kftlb', 0)) if pd.notna(row.get('Torque_kftlb')) else 0,
                        'rpm': float(row.get('RPM_demo', 0)) if pd.notna(row.get('RPM_demo')) else 0,
                        'vibration_g': float(row.get('Vibration_g', 0)) if pd.notna(row.get('Vibration_g')) else 0,
                        'inclination_deg': float(row.get('Inclination_deg', 0)) if pd.notna(row.get('Inclination_deg')) else 0,
                        'azimuth_deg': float(row.get('Azimuth_deg', 0)) if pd.notna(row.get('Azimuth_deg')) else 0,
                        'rop_ft_hr': float(row.get('ROP_ft_hr', 0)) if pd.notna(row.get('ROP_ft_hr')) else 0,
                        'dls_deg_100ft': float(row.get('DLS_deg_per_100ft', 0)) if pd.notna(row.get('DLS_deg_per_100ft')) else 0,
                        'gamma_gapi': float(row.get('Gamma_gAPI', 0)) if pd.notna(row.get('Gamma_gAPI')) else 0,
                        'resistivity_ohm_m': float(row.get('Resistivity_ohm_m', 0)) if pd.notna(row.get('Resistivity_ohm_m')) else 0,
                        'phif': float(row.get('PHIF', 0)) if pd.notna(row.get('PHIF')) else 0,
                        'vsh': float(row.get('VSH', 0)) if pd.notna(row.get('VSH')) else 0,
                        'sw': float(row.get('SW', 0)) if pd.notna(row.get('SW')) else 0,
                        'klogh': float(row.get('KLOGH', 0)) if pd.notna(row.get('KLOGH')) else 0,
                        'formation_class': str(row.get('Formation_Class', 'Unknown')) if pd.notna(row.get('Formation_Class')) else 'Unknown',
                    }
                    
                    # Create and add packet
                    packet = TelemetryPacket(**packet_data)
                    session.add(packet)
                    inserted_count += 1
                    
                    # Batch commit
                    if inserted_count % batch_size == 0:
                        session.commit()
                        logger.info(f"Inserted {inserted_count} telemetry packets...")
                        
                except Exception as e:
                    logger.error(f"Error processing row {idx}: {e}")
                    error_count += 1
                    session.rollback()
                    continue
            
            # Final commit
            session.commit()
            session.close()
            
            logger.info(f"Telemetry import complete: {inserted_count} inserted, {skipped_count} skipped, {error_count} errors")
            
            return {
                'inserted': inserted_count,
                'skipped': skipped_count,
                'errors': error_count,
                'total': len(df)
            }
            
        except Exception as e:
            logger.error(f"Database error: {e}")
            session.rollback()
            session.close()
            raise
            
    except Exception as e:
        logger.error(f"Import failed: {e}")
        raise


def import_config_from_excel(excel_path: str) -> Dict[str, Any]:
    """Import configuration data from Excel file."""
    logger.info(f"Starting configuration import from {excel_path}")
    
    try:
        # Read the Controls sheet
        df = pd.read_excel(excel_path, sheet_name='Controls')
        logger.info(f"Loaded {len(df)} configuration rows from Excel")
        
        session = SessionLocal()
        inserted_count = 0
        
        try:
            for idx, row in df.iterrows():
                try:
                    param_name = row.get('Prototype Control Parameters')
                    param_value = row.get('Unnamed: 1')
                    
                    if pd.isna(param_name) or pd.isna(param_value):
                        continue
                    
                    # Create config entry
                    config = SystemConfig(
                        id=str(uuid.uuid4()),
                        key=str(param_name).strip(),
                        value=str(param_value),
                        config_type='control_parameter'
                    )
                    session.add(config)
                    inserted_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing config row {idx}: {e}")
                    session.rollback()
                    continue
            
            session.commit()
            session.close()
            
            logger.info(f"Configuration import complete: {inserted_count} entries imported")
            
            return {
                'inserted': inserted_count,
                'total': len(df)
            }
            
        except Exception as e:
            logger.error(f"Database error: {e}")
            session.rollback()
            session.close()
            raise
            
    except Exception as e:
        logger.error(f"Config import failed: {e}")
        raise


def main():
    """Main import function."""
    excel_file = Path(__file__).parent / "data" / "rss_dashboard_dataset_built_recalc.xlsx"
    
    if not excel_file.exists():
        logger.error(f"Excel file not found: {excel_file}")
        sys.exit(1)
    
    logger.info("=" * 80)
    logger.info("Drilling Insight Dashboard - Excel to Database Import")
    logger.info("=" * 80)
    
    try:
        # Import telemetry data
        telemetry_results = import_telemetry_from_excel(str(excel_file))
        
        # Import configuration data
        config_results = import_config_from_excel(str(excel_file))
        
        # Print summary
        logger.info("\n" + "=" * 80)
        logger.info("IMPORT SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Telemetry: {telemetry_results['inserted']}/{telemetry_results['total']} imported")
        logger.info(f"Configuration: {config_results['inserted']}/{config_results['total']} imported")
        logger.info("=" * 80)
        logger.info("✅ Import completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
