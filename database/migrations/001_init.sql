-- Migration: 001_init.sql
-- Create production-ready PostgreSQL schema for Drilling Insight Dashboard
-- Generated on: 2026-04-11

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create enum types
CREATE TYPE user_role AS ENUM ('operator', 'engineer', 'admin');
CREATE TYPE alert_severity AS ENUM ('low', 'medium', 'high', 'critical');
CREATE TYPE gate_outcome AS ENUM ('ACCEPTED', 'REJECTED');
CREATE TYPE execution_status AS ENUM ('SENT', 'PENDING', 'FAILED');
CREATE TYPE alert_status AS ENUM ('ACTIVE', 'ACKNOWLEDGED', 'RESOLVED');

-- Create users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role user_role NOT NULL DEFAULT 'operator',
    is_active BOOLEAN NOT NULL DEFAULT true,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create wells table
CREATE TABLE wells (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    location VARCHAR(255),
    operator VARCHAR(100),
    spud_date DATE,
    total_depth_ft DECIMAL(10,2),
    current_depth_ft DECIMAL(10,2),
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create telemetry_packets table (time-series optimized)
CREATE TABLE telemetry_packets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    well_id UUID NOT NULL REFERENCES wells(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL,
    wob_klbf DECIMAL(8,3),
    rpm DECIMAL(8,2),
    rop_ft_hr DECIMAL(8,3),
    torque_kftlb DECIMAL(8,3),
    vibration_g DECIMAL(6,4),
    dls_deg_100ft DECIMAL(6,3),
    inclination_deg DECIMAL(6,3),
    azimuth_deg DECIMAL(6,3),
    depth_ft DECIMAL(10,2),
    temperature_c DECIMAL(6,2),
    pressure_psi DECIMAL(10,2),
    mud_flow_gpm DECIMAL(8,2),
    raw_data JSONB,
    quality_score DECIMAL(3,2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (timestamp);

-- Create partitions for telemetry_packets (last 12 months + future)
-- Note: In production, you'd want to automate partition creation
CREATE TABLE telemetry_packets_2026_04 PARTITION OF telemetry_packets
    FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');
CREATE TABLE telemetry_packets_2026_05 PARTITION OF telemetry_packets
    FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');
CREATE TABLE telemetry_packets_2026_06 PARTITION OF telemetry_packets
    FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');
CREATE TABLE telemetry_packets_2026_07 PARTITION OF telemetry_packets
    FOR VALUES FROM ('2026-07-01') TO ('2026-08-01');
CREATE TABLE telemetry_packets_2026_08 PARTITION OF telemetry_packets
    FOR VALUES FROM ('2026-08-01') TO ('2026-09-01');
CREATE TABLE telemetry_packets_2026_09 PARTITION OF telemetry_packets
    FOR VALUES FROM ('2026-09-01') TO ('2026-10-01');
CREATE TABLE telemetry_packets_2026_10 PARTITION OF telemetry_packets
    FOR VALUES FROM ('2026-10-01') TO ('2026-11-01');
CREATE TABLE telemetry_packets_2026_11 PARTITION OF telemetry_packets
    FOR VALUES FROM ('2026-11-01') TO ('2026-12-01');
CREATE TABLE telemetry_packets_2026_12 PARTITION OF telemetry_packets
    FOR VALUES FROM ('2026-12-01') TO ('2027-01-01');
CREATE TABLE telemetry_packets_2027_01 PARTITION OF telemetry_packets
    FOR VALUES FROM ('2027-01-01') TO ('2027-02-01');
CREATE TABLE telemetry_packets_2027_02 PARTITION OF telemetry_packets
    FOR VALUES FROM ('2027-02-01') TO ('2027-03-01');
CREATE TABLE telemetry_packets_2027_03 PARTITION OF telemetry_packets
    FOR VALUES FROM ('2027-03-01') TO ('2027-04-01');
CREATE TABLE telemetry_packets_future PARTITION OF telemetry_packets
    FOR VALUES FROM ('2027-04-01') TO (MAXVALUE);

-- Create decisions table
CREATE TABLE decisions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    well_id UUID NOT NULL REFERENCES wells(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    model_version VARCHAR(50),
    steering_command VARCHAR(20) NOT NULL,
    confidence_score DECIMAL(4,3),
    gate_outcome gate_outcome,
    rejection_reason TEXT,
    execution_status execution_status DEFAULT 'PENDING',
    feature_summary JSONB,
    event_tags JSONB,
    related_signals JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create alerts table
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    well_id UUID NOT NULL REFERENCES wells(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    severity alert_severity NOT NULL DEFAULT 'medium',
    status alert_status NOT NULL DEFAULT 'ACTIVE',
    title VARCHAR(255) NOT NULL,
    message TEXT,
    alert_type VARCHAR(50),
    threshold_value DECIMAL(10,4),
    actual_value DECIMAL(10,4),
    acknowledged_at TIMESTAMPTZ,
    acknowledged_by UUID REFERENCES users(id),
    resolved_at TIMESTAMPTZ,
    resolved_by UUID REFERENCES users(id),
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create model_versions table
CREATE TABLE model_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    version VARCHAR(50) UNIQUE NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    algorithm VARCHAR(100),
    training_date TIMESTAMPTZ,
    accuracy DECIMAL(5,4),
    precision DECIMAL(5,4),
    recall DECIMAL(5,4),
    f1_score DECIMAL(5,4),
    metrics JSONB,
    schema JSONB,
    is_active BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create system_config table
CREATE TABLE system_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key VARCHAR(100) UNIQUE NOT NULL,
    value JSONB NOT NULL,
    description TEXT,
    is_encrypted BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create audit_logs table
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(255)
);

-- Create indexes for performance optimization

-- Users indexes
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active);

-- Wells indexes
CREATE INDEX idx_wells_name ON wells(name);
CREATE INDEX idx_wells_status ON wells(status);
CREATE INDEX idx_wells_operator ON wells(operator);
CREATE INDEX idx_wells_metadata ON wells USING GIN(metadata);

-- Telemetry packets indexes (time-series optimized)
CREATE INDEX idx_telemetry_well_timestamp ON telemetry_packets(well_id, timestamp DESC);
CREATE INDEX idx_telemetry_timestamp ON telemetry_packets(timestamp DESC);
CREATE INDEX idx_telemetry_well ON telemetry_packets(well_id);
CREATE INDEX idx_telemetry_depth ON telemetry_packets(well_id, depth_ft);
CREATE INDEX idx_telemetry_raw_data ON telemetry_packets USING GIN(raw_data);

-- Decisions indexes (optimized for well_id + timestamp queries)
CREATE INDEX idx_decisions_well_timestamp ON decisions(well_id, timestamp DESC);
CREATE INDEX idx_decisions_user ON decisions(user_id);
CREATE INDEX idx_decisions_status ON decisions(execution_status);
CREATE INDEX idx_decisions_gate_outcome ON decisions(gate_outcome);
CREATE INDEX idx_decisions_feature_summary ON decisions USING GIN(feature_summary);
CREATE INDEX idx_decisions_event_tags ON decisions USING GIN(event_tags);

-- Alerts indexes (optimized for well_id + timestamp queries)
CREATE INDEX idx_alerts_well_timestamp ON alerts(well_id, timestamp DESC);
CREATE INDEX idx_alerts_status ON alerts(status);
CREATE INDEX idx_alerts_severity ON alerts(severity);
CREATE INDEX idx_alerts_type ON alerts(alert_type);
CREATE INDEX idx_alerts_acknowledged_by ON alerts(acknowledged_by);
CREATE INDEX idx_alerts_resolved_by ON alerts(resolved_by);
CREATE INDEX idx_alerts_metadata ON alerts USING GIN(metadata);

-- Model versions indexes
CREATE INDEX idx_model_versions_version ON model_versions(version);
CREATE INDEX idx_model_versions_type ON model_versions(model_type);
CREATE INDEX idx_model_versions_active ON model_versions(is_active);
CREATE INDEX idx_model_versions_metrics ON model_versions USING GIN(metrics);
CREATE INDEX idx_model_versions_schema ON model_versions USING GIN(schema);

-- System config indexes
CREATE INDEX idx_system_config_key ON system_config(key);
CREATE INDEX idx_system_config_value ON system_config USING GIN(value);

-- Audit logs indexes
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_session ON audit_logs(session_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add updated_at triggers
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_wells_updated_at BEFORE UPDATE ON wells
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_decisions_updated_at BEFORE UPDATE ON decisions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_alerts_updated_at BEFORE UPDATE ON alerts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_model_versions_updated_at BEFORE UPDATE ON model_versions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_config_updated_at BEFORE UPDATE ON system_config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function for telemetry data retention (optional)
CREATE OR REPLACE FUNCTION cleanup_old_telemetry(days_old INTEGER DEFAULT 365)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM telemetry_packets
    WHERE timestamp < NOW() - INTERVAL '1 day' * days_old;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create function for alert auto-resolution (optional)
CREATE OR REPLACE FUNCTION auto_resolve_alerts(hours_old INTEGER DEFAULT 24)
RETURNS INTEGER AS $$
DECLARE
    resolved_count INTEGER;
BEGIN
    UPDATE alerts
    SET status = 'RESOLVED',
        resolved_at = NOW(),
        updated_at = NOW()
    WHERE status = 'ACTIVE'
      AND timestamp < NOW() - INTERVAL '1 hour' * hours_old
      AND severity IN ('low', 'medium');

    GET DIAGNOSTICS resolved_count = ROW_COUNT;
    RETURN resolved_count;
END;
$$ LANGUAGE plpgsql;

-- Insert default system configuration
INSERT INTO system_config (key, value, description) VALUES
('confidence_threshold', '{"reject": 0.3, "reduce": 0.5}', 'AI confidence thresholds for decision gating'),
('dls_limits', '{"reject": 3.0, "reduce": 2.0}', 'DLS limits in deg/100ft'),
('vibration_limits', '{"reject": 0.5, "reduce": 0.3}', 'Vibration limits in g'),
('telemetry_sampling_rate', '{"hz": 1}', 'Telemetry sampling rate in Hz'),
('alert_retention_days', '{"days": 90}', 'Days to retain resolved alerts'),
('telemetry_retention_days', '{"days": 365}', 'Days to retain telemetry data');

-- Insert default model version
INSERT INTO model_versions (
    version, model_type, algorithm, accuracy, precision, recall, f1_score,
    metrics, schema, is_active
) VALUES (
    'rf-cal-v1',
    'steering_recommendation',
    'RandomForestClassifier',
    0.8065,
    0.494,
    0.494,
    0.494,
    '{
        "accuracy": 0.8065,
        "macro_f1": 0.494,
        "precision": 0.494,
        "recall": 0.494,
        "training_samples": 1000,
        "validation_samples": 200
    }',
    '{
        "features": ["WOB_klbf", "RPM_demo", "ROP_ft_hr", "Torque_kftlb", "Vibration_g", "DLS_deg_per_100ft", "Inclination_deg", "Azimuth_deg"],
        "target": "steering_command",
        "classes": ["Hold", "Build", "Drop"]
    }',
    true
);