
-- SCHEMA PARA SIMULACIÓN DE TRÁFICO SUMO - SAN JOSÉ, CR
-- PostgreSQL + TimescaleDB
-- Base: Datos de Barcelona adaptados a San José


-- Habilitar extensiones
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS postgis;


-- TABLAS ESTÁTICAS (Configuración)


-- Tabla de cantidad simulaciones
CREATE TABLE simulation_runs (
    run_id SERIAL PRIMARY KEY,
    run_name VARCHAR(100) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    config_file TEXT,
    status VARCHAR(20) DEFAULT 'running',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tipos de vehículos
CREATE TABLE vehicle_types (
    vtype_id VARCHAR(50) PRIMARY KEY,
    vclass VARCHAR(30) NOT NULL,
    description TEXT,
    max_speed DOUBLE PRECISION,
    length DOUBLE PRECISION,
    width DOUBLE PRECISION,
    color VARCHAR(20)
);

-- Periodos del día
CREATE TABLE time_periods (
    period_id SERIAL PRIMARY KEY,
    period_name VARCHAR(20) NOT NULL,
    start_hour INTEGER NOT NULL,
    end_hour INTEGER NOT NULL,
    description TEXT
);

-- Insertar tipos de vehículos base
INSERT INTO vehicle_types (vtype_id, vclass, description) VALUES
    ('veh_passenger', 'passenger', 'Vehículo de pasajeros'),
    ('veh_bus', 'bus', 'Autobús urbano'),
    ('veh_motorcycle', 'motorcycle', 'Motocicleta'),
    ('veh_truck', 'truck', 'Camión de carga'),
    ('pt_bus', 'bus', 'Autobús de transporte público'),
    ('pt_tram', 'bus', 'Tranvía')
ON CONFLICT (vtype_id) DO NOTHING;

-- Insertar periodos del día
INSERT INTO time_periods (period_name, start_hour, end_hour, description) VALUES
    ('MADRUGADA', 0, 5, 'Madrugada (00:00-05:00)'),
    ('MAÑANA', 5, 7, 'Mañana temprano (05:00-07:00)'),
    ('PICO_AM', 7, 9, 'Pico matutino (07:00-09:00)'),
    ('DIA', 9, 17, 'Día normal (09:00-17:00)'),
    ('PICO_PM', 17, 19, 'Pico vespertino (17:00-19:00)'),
    ('NOCHE', 19, 24, 'Noche (19:00-24:00)')
ON CONFLICT DO NOTHING;

-- ============================================================
-- TABLAS DE DATOS DE SIMULACIÓN (Time-Series)
-- ============================================================

-- Viajes de vehículos (tripinfo.xml)
CREATE TABLE vehicle_trips (
    time TIMESTAMP NOT NULL,
    run_id INTEGER NOT NULL REFERENCES simulation_runs(run_id),
    vehicle_id VARCHAR(50) NOT NULL,
    vehicle_type VARCHAR(50) REFERENCES vehicle_types(vtype_id),
    depart DOUBLE PRECISION,
    arrival DOUBLE PRECISION,
    duration DOUBLE PRECISION,
    route_length DOUBLE PRECISION,
    waiting_time DOUBLE PRECISION,
    time_loss DOUBLE PRECISION,
    avg_speed DOUBLE PRECISION,
    max_speed DOUBLE PRECISION,
    departed DOUBLE PRECISION,
    arrived DOUBLE PRECISION,
    vaporized BOOLEAN,
    period VARCHAR(20),
    depart_delay DOUBLE PRECISION,
    stop_time DOUBLE PRECISION
);

-- Convertir a hypertable (TimescaleDB)
SELECT create_hypertable('vehicle_trips', 'time', if_not_exists => TRUE);

-- Índices para vehicle_trips
CREATE INDEX IF NOT EXISTS idx_vehicle_trips_run_id ON vehicle_trips(run_id);
CREATE INDEX IF NOT EXISTS idx_vehicle_trips_vehicle_type ON vehicle_trips(vehicle_type);
CREATE INDEX IF NOT EXISTS idx_vehicle_trips_period ON vehicle_trips(period);
CREATE INDEX IF NOT EXISTS idx_vehicle_trips_vehicle_id ON vehicle_trips(vehicle_id);

-- Datos de calles/edges (edgeData.xml)
CREATE TABLE edge_data (
    time TIMESTAMP NOT NULL,
    run_id INTEGER NOT NULL REFERENCES simulation_runs(run_id),
    edge_id VARCHAR(50) NOT NULL,
    begin_time DOUBLE PRECISION,
    end_time DOUBLE PRECISION,
    num_vehicles INTEGER,
    avg_speed DOUBLE PRECISION,
    avg_occupancy DOUBLE PRECISION,
    avg_density DOUBLE PRECISION,
    avg_waiting_time DOUBLE PRECISION,
    avg_travel_time DOUBLE PRECISION
);

-- Convertir a hypertable (TimescaleDB)
SELECT create_hypertable('edge_data', 'time', if_not_exists => TRUE);

-- Índices para edge_data
CREATE INDEX IF NOT EXISTS idx_edge_data_run_id ON edge_data(run_id);
CREATE INDEX IF NOT EXISTS idx_edge_data_edge_id ON edge_data(edge_id);

-- Estadísticas globales (stats.xml)
CREATE TABLE simulation_stats (
    time TIMESTAMP NOT NULL,
    run_id INTEGER NOT NULL REFERENCES simulation_runs(run_id),
    step INTEGER,
    vehicles_loaded INTEGER,
    vehicles_inserted INTEGER,
    vehicles_running INTEGER,
    vehicles_waiting INTEGER,
    vehicles_ended INTEGER,
    vehicles_arrived INTEGER,
    vehicles_collisions INTEGER,
    vehicles_teleports INTEGER,
    total_travel_time DOUBLE PRECISION,
    total_waiting_time DOUBLE PRECISION
);

-- Convertir a hypertable (TimescaleDB)
SELECT create_hypertable('simulation_stats', 'time', if_not_exists => TRUE);

-- Índices para simulation_stats
CREATE INDEX IF NOT EXISTS idx_simulation_stats_run_id ON simulation_stats(run_id);
CREATE INDEX IF NOT EXISTS idx_simulation_stats_step ON simulation_stats(step);

-- Paradas de transporte público (stopinfo.xml)
CREATE TABLE IF NOT EXISTS pt_stops (
    time TIMESTAMP NOT NULL,
    run_id INTEGER NOT NULL REFERENCES simulation_runs(run_id),
    stop_id VARCHAR(50),
    vehicle_id VARCHAR(50),
    delay DOUBLE PRECISION,
    passengers_loaded INTEGER,
    passengers_unloaded INTEGER,
    passengers_count INTEGER
);

-- Convertir a hypertable (TimescaleDB)
SELECT create_hypertable('pt_stops', 'time', if_not_exists => TRUE);

-- Índices para pt_stops
CREATE INDEX IF NOT EXISTS idx_pt_stops_run_id ON pt_stops(run_id);
CREATE INDEX IF NOT EXISTS idx_pt_stops_stop_id ON pt_stops(stop_id);
CREATE INDEX IF NOT EXISTS idx_pt_stops_vehicle_id ON pt_stops(vehicle_id);


-- VISTAS DE ANÁLISIS


-- Vista: Calles congestionadas
CREATE OR REPLACE VIEW congested_streets AS
SELECT 
    edge_id,
    COUNT(*) as measurement_count,
    ROUND(AVG(avg_speed)::numeric, 2) as avg_speed,
    ROUND(AVG(avg_density)::numeric, 2) as avg_density,
    ROUND(AVG(avg_occupancy)::numeric, 2) as avg_occupancy
FROM edge_data
WHERE avg_speed > 0 AND avg_speed < 5.0
GROUP BY edge_id
ORDER BY avg_density DESC;

-- Vista: Resumen de simulación
CREATE OR REPLACE VIEW simulation_summary AS
SELECT 
    sr.run_id,
    sr.run_name,
    sr.start_time,
    sr.end_time,
    COUNT(DISTINCT vt.vehicle_id) as total_vehicles,
    ROUND(AVG(vt.duration)::numeric, 2) as avg_trip_duration,
    ROUND(AVG(vt.avg_speed)::numeric, 2) as avg_trip_speed,
    ROUND(SUM(vt.route_length)::numeric, 2) as total_distance_traveled
FROM simulation_runs sr
LEFT JOIN vehicle_trips vt ON sr.run_id = vt.run_id
GROUP BY sr.run_id, sr.run_name, sr.start_time, sr.end_time;

-- Vista: Tráfico por período
CREATE OR REPLACE VIEW traffic_by_period AS
SELECT 
    vt.period,
    COUNT(*) as total_trips,
    ROUND(AVG(vt.duration)::numeric, 2) as avg_duration,
    ROUND(AVG(vt.avg_speed)::numeric, 2) as avg_speed,
    ROUND(AVG(vt.waiting_time)::numeric, 2) as avg_waiting_time
FROM vehicle_trips vt
WHERE vt.period IS NOT NULL
GROUP BY vt.period
ORDER BY 
    CASE vt.period
        WHEN 'MADRUGADA' THEN 1
        WHEN 'MAÑANA' THEN 2
        WHEN 'PICO_AM' THEN 3
        WHEN 'DIA' THEN 4
        WHEN 'PICO_PM' THEN 5
        WHEN 'NOCHE' THEN 6
    END;


-- FUNCIONES


-- Función: Obtener período del día según hora
CREATE OR REPLACE FUNCTION get_period(hour_of_day INTEGER)
RETURNS VARCHAR AS $$
BEGIN
    RETURN (
        SELECT period_name 
        FROM time_periods 
        WHERE hour_of_day >= start_hour AND hour_of_day < end_hour
        LIMIT 1
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;



-- COMENTARIOS


COMMENT ON TABLE simulation_runs IS 'Registro de ejecuciones de simulación SUMO';
COMMENT ON TABLE vehicle_trips IS 'Información de viajes completados por vehículos (tripinfo.xml)';
COMMENT ON TABLE edge_data IS 'Métricas agregadas por calle/edge y período (edgeData.xml)';
COMMENT ON TABLE simulation_stats IS 'Estadísticas globales de la simulación por timestep (stats.xml)';
COMMENT ON TABLE pt_stops IS 'Información de paradas de transporte público (stopinfo.xml)';
COMMENT ON TABLE vehicle_types IS 'Catálogo de tipos de vehículos SUMO';
COMMENT ON TABLE time_periods IS 'Franjas horarias para análisis de tráfico';

COMMENT ON VIEW congested_streets IS 'Calles con velocidad promedio < 5 m/s ordenadas por densidad';
COMMENT ON VIEW simulation_summary IS 'Resumen agregado por simulación';
COMMENT ON VIEW traffic_by_period IS 'Estadísticas de tráfico agrupadas por franja horaria';

COMMENT ON FUNCTION get_period(INTEGER) IS 'Retorna el nombre del período según la hora del día (0-23)';