#!/usr/bin/env python3
"""
Excel to Database Import Script for Drilling Insight Dashboard.

This script imports data from rss_dashboard_dataset_built_recalc.xlsx into the database:
- Dashboard_Data sheet -> telemetry_packets table
- Controls sheet -> system_config table

Features:
- Column name normalization
- Numeric range validation
- Safe handling of missing values
- Batch inserts for performance
- Comprehensive summary reporting
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path
import uuid
import logging
from dataclasses import dataclass

# Set default database URL if not set (for testing)
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Database imports
from database.db import get_session, check_database_connection
from database.repositories import TelemetryRepository, ConfigRepository
from database.schemas import TelemetryPacketCreate, SystemConfigCreate
from database.models import Well

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ImportStats:
    """Statistics for import operations."""
    total_rows: int = 0
    inserted_rows: int = 0
    skipped_rows: int = 0
    error_rows: int = 0
    validation_errors: Dict[str, int] = None
    missing_values: Dict[str, int] = None
    outliers: Dict[str, int] = None

    def __post_init__(self):
        if self.validation_errors is None:
            self.validation_errors = {}
        if self.missing_values is None:
            self.missing_values = {}
        if self.outliers is None:
            self.outliers = {}

class ExcelToDatabaseImporter:
    """Main importer class for Excel to PostgreSQL operations."""

    def __init__(self, excel_path: str, batch_size: int = 1000):
        self.excel_path = Path(excel_path)
        self.batch_size = batch_size
        self.well_id = "well_001"  # Default well for telemetry data

        # Validation ranges (based on typical drilling parameters)
        self.validation_ranges = {
            'wob_klbf': (0, 100),          # Weight on bit: 0-100 klbf
            'rpm': (0, 400),               # RPM: 0-400
            'rop_ft_hr': (0, 500),         # Rate of penetration: 0-500 ft/hr
            'torque_kftlb': (0, 50),       # Torque: 0-50 kft-lb
            'vibration_g': (0, 10),        # Vibration: 0-10g
            'dls_deg_100ft': (0, 20),      # DLS: 0-20 deg/100ft
            'inclination_deg': (0, 180),   # Inclination: 0-180 degrees
            'azimuth_deg': (0, 360),       # Azimuth: 0-360 degrees
            'depth_ft': (0, 50000),        # Depth: 0-50,000 ft
            'gamma_gapi': (0, 500),        # Gamma ray: 0-500 gAPI
            'resistivity_ohm_m': (0.1, 10000),  # Resistivity: 0.1-10,000 ohm-m
            'phif': (0, 0.5),              # Porosity: 0-0.5 (50%)
            'vsh': (0, 1),                 # Volume shale: 0-1 (100%)
            'sw': (0, 1),                  # Water saturation: 0-1 (100%)
            'klogh': (0.001, 10000),       # Permeability: 0.001-10,000 mD
        }

    def normalize_column_name(self, col: str) -> str:
        """Normalize Excel column names to database field names."""
        # Remove spaces, special characters, and normalize case
        col = str(col).strip()

        # Common mappings from Excel to database
        column_mappings = {
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

        return column_mappings.get(col, col.lower().replace(' ', '_').replace('-', '_'))

    def validate_numeric_value(self, value: Any, field: str, min_val: float, max_val: float) -> Tuple[bool, Optional[float]]:
        """Validate a numeric value against acceptable ranges."""
        if pd.isna(value):
            return True, None  # Missing values are allowed

        try:
            numeric_value = float(value)
            if min_val <= numeric_value <= max_val:
                return True, numeric_value
            else:
                return False, numeric_value
        except (ValueError, TypeError):
            return False, None

    def parse_timestamp(self, timestamp_str: Any) -> Optional[datetime]:
        """Parse timestamp from various formats."""
        if pd.isna(timestamp_str):
            return None

        try:
            # Try different timestamp formats
            if isinstance(timestamp_str, str):
                # Try ISO format first
                try:
                    return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                except ValueError:
                    pass

                # Try common Excel date formats
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%m/%d/%Y %H:%M:%S']:
                    try:
                        return datetime.strptime(timestamp_str, fmt)
                    except ValueError:
                        continue

            # If it's already a datetime object
            elif isinstance(timestamp_str, (datetime, pd.Timestamp)):
                return timestamp_str.to_pydatetime()

            return None
        except Exception as e:
            logger.warning(f"Failed to parse timestamp '{timestamp_str}': {e}")
            return None

    def ensure_well_exists(self, session) -> None:
        """Ensure the default well exists in the database."""
        from database.repositories import BaseRepository

        well_repo = BaseRepository(session, Well)
        existing_well = session.query(Well).filter_by(id=self.well_id).first()

        if not existing_well:
            well = Well(
                id=self.well_id,
                name="Well Alpha-1 (Imported)",
                location="Imported from Excel",
                operator="Data Import",
                status="active"
            )
            session.add(well)
            session.commit()
            logger.info(f"Created default well: {self.well_id}")

    def import_telemetry_data(self, df: pd.DataFrame) -> ImportStats:
        """Import telemetry data from DataFrame to database."""
        stats = ImportStats(total_rows=len(df))
        batch_data = []

        logger.info(f"Starting telemetry import: {len(df)} rows")

        with get_session() as session:
            self.ensure_well_exists(session)
            telemetry_repo = TelemetryRepository(session)

            for idx, row in df.iterrows():
                try:
                    # Parse timestamp
                    timestamp = self.parse_timestamp(row.get('Timestamp'))
                    if not timestamp:
                        stats.error_rows += 1
                        stats.validation_errors['invalid_timestamp'] = stats.validation_errors.get('invalid_timestamp', 0) + 1
                        continue

                    # Validate and convert numeric fields
                    telemetry_data = {
                        'id': str(uuid.uuid4()),
                        'well_id': self.well_id,
                        'timestamp': timestamp,
                        'raw_data': {}  # Store original data
                    }

                    # Track missing values
                    for excel_col, db_field in [
                        ('Depth_ft', 'depth_ft'),
                        ('WOB_klbf', 'wob_klbf'),
                        ('Torque_kftlb', 'torque_kftlb'),
                        ('RPM_demo', 'rpm'),
                        ('Vibration_g', 'vibration_g'),
                        ('Inclination_deg', 'inclination_deg'),
                        ('Azimuth_deg', 'azimuth_deg'),
                        ('ROP_ft_hr', 'rop_ft_hr'),
                        ('DLS_deg_per_100ft', 'dls_deg_100ft'),
                        ('Gamma_gAPI', 'gamma_gapi'),
                        ('Resistivity_ohm_m', 'resistivity_ohm_m'),
                        ('PHIF', 'phif'),
                        ('VSH', 'vsh'),
                        ('SW', 'sw'),
                        ('KLOGH', 'klogh'),
                    ]:
                        value = row.get(excel_col)
                        if pd.isna(value):
                            stats.missing_values[db_field] = stats.missing_values.get(db_field, 0) + 1
                            telemetry_data['raw_data'][excel_col] = None
                            continue

                        # Validate numeric ranges
                        if db_field in self.validation_ranges:
                            min_val, max_val = self.validation_ranges[db_field]
                            is_valid, numeric_value = self.validate_numeric_value(value, db_field, min_val, max_val)
                            if not is_valid:
                                stats.outliers[db_field] = stats.outliers.get(db_field, 0) + 1
                                logger.warning(f"Outlier in {db_field}: {value} (expected {min_val}-{max_val})")
                                # Still include outlier data but mark it
                                telemetry_data[db_field] = numeric_value
                            else:
                                telemetry_data[db_field] = numeric_value
                        else:
                            # For non-validated fields, just convert to float if possible
                            try:
                                telemetry_data[db_field] = float(value) if str(value).replace('.', '').replace('-', '').isdigit() else str(value)
                            except (ValueError, TypeError):
                                telemetry_data[db_field] = str(value)

                        telemetry_data['raw_data'][excel_col] = value

                    # Add formation class if available
                    formation_class = row.get('Formation_Class')
                    if pd.notna(formation_class):
                        telemetry_data['raw_data']['formation_class'] = str(formation_class)

                    # Create telemetry packet
                    packet_data = TelemetryPacketCreate(**telemetry_data)
                    batch_data.append(packet_data)

                    # Insert in batches
                    if len(batch_data) >= self.batch_size:
                        success_count = self._insert_telemetry_batch(telemetry_repo, batch_data)
                        stats.inserted_rows += success_count
                        stats.error_rows += (len(batch_data) - success_count)
                        batch_data = []

                except Exception as e:
                    logger.error(f"Error processing row {idx}: {e}")
                    stats.error_rows += 1
                    stats.validation_errors['processing_error'] = stats.validation_errors.get('processing_error', 0) + 1

            # Insert remaining batch
            if batch_data:
                success_count = self._insert_telemetry_batch(telemetry_repo, batch_data)
                stats.inserted_rows += success_count
                stats.error_rows += (len(batch_data) - success_count)

        stats.skipped_rows = stats.total_rows - stats.inserted_rows - stats.error_rows
        return stats

    def _insert_telemetry_batch(self, repo: TelemetryRepository, batch_data: List[TelemetryPacketCreate]) -> int:
        """Insert a batch of telemetry data."""
        success_count = 0
        for packet_data in batch_data:
            try:
                repo.create(packet_data.model_dump())
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to insert telemetry packet: {e}")
        return success_count

    def import_config_data(self, df: pd.DataFrame) -> ImportStats:
        """Import configuration data from DataFrame to database."""
        stats = ImportStats(total_rows=len(df))

        logger.info(f"Starting config import: {len(df)} rows")

        with get_session() as session:
            config_repo = ConfigRepository(session)

            for idx, row in df.iterrows():
                try:
                    # Get parameter name and value
                    param_name = str(row.get('Prototype Control Parameters', '')).strip()
                    param_value = row.get('Unnamed: 1')

                    if not param_name or pd.isna(param_value):
                        stats.skipped_rows += 1
                        continue

                    # Normalize parameter name to config key
                    config_key = param_name.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_')

                    # Convert value to appropriate type
                    if isinstance(param_value, (int, float)):
                        config_value = param_value
                    else:
                        # Try to convert to float, otherwise keep as string
                        try:
                            config_value = float(param_value)
                        except (ValueError, TypeError):
                            config_value = str(param_value)

                    # Create config entry
                    config_data = SystemConfigCreate(
                        key=config_key,
                        value={'value': config_value, 'source': 'excel_import'},
                        description=f"Imported from Excel: {param_name}"
                    )

                    try:
                        config_repo.create(config_data.model_dump())
                        stats.inserted_rows += 1
                        logger.debug(f"Imported config: {config_key} = {config_value}")
                    except Exception as e:
                        if 'unique constraint' in str(e).lower():
                            # Update existing config
                            existing_config = session.query(SystemConfig).filter_by(key=config_key).first()
                            if existing_config:
                                existing_config.value = {'value': config_value, 'source': 'excel_import'}
                                existing_config.description = f"Updated from Excel: {param_name}"
                                session.commit()
                                stats.inserted_rows += 1
                                logger.debug(f"Updated existing config: {config_key}")
                            else:
                                stats.error_rows += 1
                                logger.error(f"Failed to update config {config_key}: {e}")
                        else:
                            stats.error_rows += 1
                            logger.error(f"Failed to import config {config_key}: {e}")

                except Exception as e:
                    logger.error(f"Error processing config row {idx}: {e}")
                    stats.error_rows += 1

        return stats

    def run_import(self) -> Dict[str, ImportStats]:
        """Run the complete import process."""
        logger.info("Starting Excel to database import")
        logger.info(f"Excel file: {self.excel_path}")

        if not self.excel_path.exists():
            raise FileNotFoundError(f"Excel file not found: {self.excel_path}")

        # Check database connection
        # if not check_database_connection():
        #     raise ConnectionError("Cannot connect to database")

        # Create database tables if they don't exist
        logger.info("Ensuring database tables exist...")
        from database.db import create_database
        create_database()

        results = {}

        try:
            # Read Excel file
            logger.info("Reading Excel file...")
            excel_data = pd.read_excel(self.excel_path, sheet_name=None)

            # Import telemetry data
            if 'Dashboard_Data' in excel_data:
                logger.info("Importing telemetry data...")
                telemetry_df = excel_data['Dashboard_Data']
                results['telemetry'] = self.import_telemetry_data(telemetry_df)
            else:
                logger.warning("Dashboard_Data sheet not found in Excel file")
                results['telemetry'] = ImportStats()

            # Import configuration data
            if 'Controls' in excel_data:
                logger.info("Importing configuration data...")
                controls_df = excel_data['Controls']
                results['config'] = self.import_config_data(controls_df)
            else:
                logger.warning("Controls sheet not found in Excel file")
                results['config'] = ImportStats()

        except Exception as e:
            logger.error(f"Import failed: {e}")
            raise

        return results

def print_summary(results: Dict[str, ImportStats]) -> None:
    """Print a comprehensive summary of the import operation."""
    print("\n" + "="*80)
    print("EXCEL TO POSTGRESQL IMPORT SUMMARY")
    print("="*80)

    total_inserted = 0
    total_errors = 0
    total_skipped = 0

    for table_name, stats in results.items():
        print(f"\n{table_name.upper()} TABLE:")
        print(f"  Total rows processed: {stats.total_rows}")
        print(f"  Successfully inserted: {stats.inserted_rows}")
        print(f"  Skipped rows: {stats.skipped_rows}")
        print(f"  Error rows: {stats.error_rows}")

        total_inserted += stats.inserted_rows
        total_errors += stats.error_rows
        total_skipped += stats.skipped_rows

        if stats.missing_values:
            print("  Missing values by field:")
            for field, count in sorted(stats.missing_values.items()):
                print(f"    {field}: {count}")

        if stats.outliers:
            print("  Outlier values by field:")
            for field, count in sorted(stats.outliers.items()):
                print(f"    {field}: {count}")

        if stats.validation_errors:
            print("  Validation errors:")
            for error_type, count in sorted(stats.validation_errors.items()):
                print(f"    {error_type}: {count}")

    print(f"\nOVERALL SUMMARY:")
    print(f"  Total inserted: {total_inserted}")
    print(f"  Total errors: {total_errors}")
    print(f"  Total skipped: {total_skipped}")
    print(f"  Success rate: {(total_inserted / max(total_inserted + total_errors + total_skipped, 1) * 100):.1f}%")

    if total_errors > 0:
        print(f"\n⚠️  {total_errors} rows had errors - check logs for details")
    if total_skipped > 0:
        print(f"ℹ️  {total_skipped} rows were skipped (missing required data)")

    print("\n✅ Import completed!")
    print("="*80)

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Import Excel data to PostgreSQL")
    parser.add_argument(
        "--excel-file",
        default="data/rss_dashboard_dataset_built_recalc.xlsx",
        help="Path to Excel file (default: data/rss_dashboard_dataset_built_recalc.xlsx)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Batch size for inserts (default: 1000)"
    )
    parser.add_argument(
        "--well-id",
        default="well_001",
        help="Well ID for telemetry data (default: well_001)"
    )

    args = parser.parse_args()

    # Set well ID
    importer = ExcelToDatabaseImporter(args.excel_file, args.batch_size)
    importer.well_id = args.well_id

    try:
        results = importer.run_import()
        print_summary(results)
        return 0
    except Exception as e:
        logger.error(f"Import failed: {e}")
        print(f"\n❌ Import failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())