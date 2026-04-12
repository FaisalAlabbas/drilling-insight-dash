-- Migration: 002_seed_demo.sql
-- Seed demo data for Drilling Insight Dashboard
-- Generated on: 2026-04-11

-- Insert demo users
INSERT INTO users (id, username, email, password_hash, role, is_active) VALUES
('550e8400-e29b-41d4-a716-446655440000', 'operator', 'operator@drilling.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPjYLC7hZwXG', 'operator', true),
('550e8400-e29b-41d4-a716-446655440001', 'engineer', 'engineer@drilling.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPjYLC7hZwXG', 'engineer', true),
('550e8400-e29b-41d4-a716-446655440002', 'admin', 'admin@drilling.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPjYLC7hZwXG', 'admin', true);

-- Insert demo wells
INSERT INTO wells (id, name, location, operator, spud_date, total_depth_ft, current_depth_ft, status, metadata) VALUES
('660e8400-e29b-41d4-a716-446655440000', 'Well-A1', 'Gulf of Mexico, Block 123', 'DeepDrill Corp', '2026-01-15', 15000.00, 8750.50, 'active', '{"field": "Thunderbird", "rig_type": "semi-submersible", "mud_type": "oil-based"}'),
('660e8400-e29b-41d4-a716-446655440001', 'Well-B2', 'North Sea, Quadrant 15', 'OceanRig Ltd', '2026-02-01', 12000.00, 12000.00, 'completed', '{"field": "Valkyrie", "rig_type": "jack-up", "mud_type": "water-based"}'),
('660e8400-e29b-41d4-a716-446655440002', 'Well-C3', 'Permian Basin, TX', 'Permian Drilling LLC', '2026-03-10', 8500.00, 4200.75, 'active', '{"field": "Wolfcamp", "rig_type": "land-rig", "mud_type": "water-based"}');

-- Insert demo telemetry packets (recent data for Well-A1)
INSERT INTO telemetry_packets (id, well_id, timestamp, wob_klbf, rpm, rop_ft_hr, torque_kftlb, vibration_g, dls_deg_100ft, inclination_deg, azimuth_deg, depth_ft, temperature_c, pressure_psi, mud_flow_gpm, quality_score) VALUES
('770e8400-e29b-41d4-a716-446655440000', '660e8400-e29b-41d4-a716-446655440000', '2026-04-11 08:00:00+00', 28.5, 125.0, 42.3, 14.2, 0.08, 1.2, 35.5, 85.0, 8750.50, 85.5, 4250.0, 650.0, 0.95),
('770e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440000', '2026-04-11 08:01:00+00', 29.1, 128.0, 44.1, 14.8, 0.06, 1.1, 35.7, 85.2, 8752.83, 86.0, 4280.0, 648.0, 0.97),
('770e8400-e29b-41d4-a716-446655440002', '660e8400-e29b-41d4-a716-446655440000', '2026-04-11 08:02:00+00', 27.8, 122.0, 40.8, 13.9, 0.12, 1.4, 35.9, 85.1, 8755.17, 84.8, 4220.0, 652.0, 0.93),
('770e8400-e29b-41d4-a716-446655440003', '660e8400-e29b-41d4-a716-446655440000', '2026-04-11 08:03:00+00', 30.2, 130.0, 46.5, 15.5, 0.05, 0.9, 36.1, 85.3, 8757.50, 87.2, 4320.0, 645.0, 0.98),
('770e8400-e29b-41d4-a716-446655440004', '660e8400-e29b-41d4-a716-446655440000', '2026-04-11 08:04:00+00', 26.9, 118.0, 38.2, 12.8, 0.15, 1.8, 36.3, 85.0, 8759.83, 83.9, 4180.0, 655.0, 0.89),
('770e8400-e29b-41d4-a716-446655440005', '660e8400-e29b-41d4-a716-446655440000', '2026-04-11 08:05:00+00', 31.5, 135.0, 48.9, 16.2, 0.04, 0.7, 36.5, 85.4, 8762.17, 88.1, 4380.0, 642.0, 0.99),
('770e8400-e29b-41d4-a716-446655440006', '660e8400-e29b-41d4-a716-446655440000', '2026-04-11 08:06:00+00', 29.8, 127.0, 45.2, 15.1, 0.09, 1.3, 36.7, 85.2, 8764.50, 86.5, 4300.0, 647.0, 0.94),
('770e8400-e29b-41d4-a716-446655440007', '660e8400-e29b-41d4-a716-446655440000', '2026-04-11 08:07:00+00', 27.2, 120.0, 39.8, 13.2, 0.18, 2.1, 36.9, 84.9, 8766.83, 84.2, 4200.0, 653.0, 0.87),
('770e8400-e29b-41d4-a716-446655440008', '660e8400-e29b-41d4-a716-446655440000', '2026-04-11 08:08:00+00', 32.1, 138.0, 50.3, 16.8, 0.03, 0.5, 37.1, 85.5, 8769.17, 88.8, 4420.0, 640.0, 1.00),
('770e8400-e29b-41d4-a716-446655440009', '660e8400-e29b-41d4-a716-446655440000', '2026-04-11 08:09:00+00', 28.7, 124.0, 43.1, 14.5, 0.11, 1.6, 37.3, 85.1, 8771.50, 85.7, 4260.0, 649.0, 0.91);

-- Insert demo decisions
INSERT INTO decisions (id, well_id, user_id, timestamp, model_version, steering_command, confidence_score, gate_outcome, execution_status, feature_summary, event_tags) VALUES
('880e8400-e29b-41d4-a716-446655440000', '660e8400-e29b-41d4-a716-446655440000', '550e8400-e29b-41d4-a716-446655440001', '2026-04-11 08:00:00+00', 'rf-cal-v1', 'Hold', 0.85, 'ACCEPTED', 'SENT', '{"WOB_klbf": 28.5, "RPM_demo": 125.0, "ROP_ft_hr": 42.3, "Torque_kftlb": 14.2, "Vibration_g": 0.08, "DLS_deg_per_100ft": 1.2, "Inclination_deg": 35.5, "Azimuth_deg": 85.0}', '["normal_operation", "optimal_parameters"]'),
('880e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440000', '550e8400-e29b-41d4-a716-446655440001', '2026-04-11 08:05:00+00', 'rf-cal-v1', 'Build', 0.72, 'ACCEPTED', 'SENT', '{"WOB_klbf": 31.5, "RPM_demo": 135.0, "ROP_ft_hr": 48.9, "Torque_kftlb": 16.2, "Vibration_g": 0.04, "DLS_deg_per_100ft": 0.7, "Inclination_deg": 36.5, "Azimuth_deg": 85.4}', '["build_required", "low_vibration"]'),
('880e8400-e29b-41d4-a716-446655440002', '660e8400-e29b-41d4-a716-446655440000', '550e8400-e29b-41d4-a716-446655440001', '2026-04-11 08:07:00+00', 'rf-cal-v1', 'Hold', 0.45, 'REJECTED', 'PENDING', '{"WOB_klbf": 27.2, "RPM_demo": 120.0, "ROP_ft_hr": 39.8, "Torque_kftlb": 13.2, "Vibration_g": 0.18, "DLS_deg_per_100ft": 2.1, "Inclination_deg": 36.9, "Azimuth_deg": 84.9}', '["high_vibration", "low_confidence"]');

-- Insert demo alerts
INSERT INTO alerts (id, well_id, user_id, timestamp, severity, status, title, message, alert_type, threshold_value, actual_value, metadata) VALUES
('990e8400-e29b-41d4-a716-446655440000', '660e8400-e29b-41d4-a716-446655440000', '550e8400-e29b-41d4-a716-446655440001', '2026-04-11 08:04:00+00', 'medium', 'ACTIVE', 'High Vibration Detected', 'Vibration levels have exceeded the caution threshold', 'vibration_alert', 0.15, 0.18, '{"sensor": "vibration_sensor_1", "duration_seconds": 45, "peak_value": 0.22}'),
('990e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440000', '550e8400-e29b-41d4-a716-446655440001', '2026-04-11 08:02:00+00', 'low', 'ACKNOWLEDGED', 'ROP Below Target', 'Rate of penetration is below optimal range', 'performance_alert', 40.0, 38.2, '{"target_rop": 45.0, "efficiency_loss": 0.15}'),
('990e8400-e29b-41d4-a716-446655440002', '660e8400-e29b-41d4-a716-446655440000', '550e8400-e29b-41d4-a716-446655440001', '2026-04-11 08:09:00+00', 'high', 'ACTIVE', 'DLS Exceeding Limit', 'Dogleg severity approaching maximum allowed', 'trajectory_alert', 2.0, 1.6, '{"remaining_tolerance": 0.4, "predicted_max": 2.2}');

-- Insert additional model versions
INSERT INTO model_versions (version, model_type, algorithm, accuracy, precision, recall, f1_score, metrics, schema, is_active) VALUES
('rf-cal-v0.9', 'steering_recommendation', 'RandomForestClassifier', 0.7823, 0.456, 0.456, 0.456, '{"accuracy": 0.7823, "macro_f1": 0.456, "precision": 0.456, "recall": 0.456}', '{"features": ["WOB_klbf", "RPM_demo", "ROP_ft_hr", "Torque_kftlb", "Vibration_g", "DLS_deg_per_100ft", "Inclination_deg", "Azimuth_deg"], "target": "steering_command"}', false),
('xgb-v1.0', 'steering_recommendation', 'XGBoostClassifier', 0.8234, 0.512, 0.512, 0.512, '{"accuracy": 0.8234, "macro_f1": 0.512, "precision": 0.512, "recall": 0.512}', '{"features": ["WOB_klbf", "RPM_demo", "ROP_ft_hr", "Torque_kftlb", "Vibration_g", "DLS_deg_per_100ft", "Inclination_deg", "Azimuth_deg"], "target": "steering_command"}', false);

-- Insert demo audit logs
INSERT INTO audit_logs (user_id, action, resource_type, resource_id, old_values, new_values, ip_address) VALUES
('550e8400-e29b-41d4-a716-446655440001', 'CREATE', 'decision', '880e8400-e29b-41d4-a716-446655440000', null, '{"steering_command": "Hold", "confidence_score": 0.85}', '192.168.1.100'),
('550e8400-e29b-41d4-a716-446655440001', 'UPDATE', 'alert', '990e8400-e29b-41d4-a716-446655440001', '{"status": "ACTIVE"}', '{"status": "ACKNOWLEDGED"}', '192.168.1.100'),
('550e8400-e29b-41d4-a716-446655440002', 'CREATE', 'well', '660e8400-e29b-41d4-a716-446655440002', null, '{"name": "Well-C3", "operator": "Permian Drilling LLC"}', '192.168.1.101');

-- Insert additional system configuration
INSERT INTO system_config (key, value, description) VALUES
('alert_email_recipients', '["engineer@drilling.com", "admin@drilling.com"]', 'Email addresses for alert notifications'),
('maintenance_schedule', '{"next_maintenance": "2026-05-01", "maintenance_type": "rig_inspection"}', 'Scheduled maintenance information'),
('safety_limits', '{"max_vibration_g": 0.5, "max_dls_deg_100ft": 3.0, "emergency_shutdown_vibration": 1.0}', 'Safety thresholds for emergency shutdown'),
('data_export_settings', '{"format": "csv", "compression": "gzip", "retention_days": 2555}', 'Settings for data export functionality'),
('api_rate_limits', '{"requests_per_minute": 100, "burst_limit": 200}', 'API rate limiting configuration');

-- Update user last login times
UPDATE users SET last_login_at = '2026-04-11 07:30:00+00' WHERE username = 'operator';
UPDATE users SET last_login_at = '2026-04-11 07:45:00+00' WHERE username = 'engineer';
UPDATE users SET last_login_at = '2026-04-11 08:00:00+00' WHERE username = 'admin';