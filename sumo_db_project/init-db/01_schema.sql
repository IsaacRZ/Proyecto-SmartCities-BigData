-- ============================================================
-- SCHEMA PARA SIMULACIÓN DE TRÁFICO SUMO - SAN JOSÉ, CR
-- Base: Datos de Barcelona adaptados a San José
-- ============================================================

-- Habilitar extensión TimescaleDB
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS postgis;

-- ============================================================
-- TABLAS ESTÁTICAS (Configuración y Red)
-- ============================================================

-- Tabla: Configuración de Simulaciones
CREATE TABLE simulation_runs (
    run_id SERIAL PRIMARY KEY,
    run_name VARCHAR(100) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    config_file TEXT,
    fringe_factor INTEGER,
    status VARCHAR(20) DEFAULT 'running',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tabla: Tipos de Vehículos
CREATE TABLE vehicle_types (
    vtype_id VARCHAR(50) PRIMARY KEY,
    vclass VARCHAR(30) NOT NULL,
    description TEXT,
    max_speed FLOAT,
    length FLOAT,
    width FLOAT,
    color VARCHAR(20)
);

-- Insertar tipos de vehículos predefinidos
INSERT INTO vehicle_types (vtype_id, vclass, description) VALUES
('veh_passenger', 'passenger', 'Vehículo de pasajeros'),
('veh_bus', 'bus', 'Bus de transporte público'),
('veh_motorcycle', 'motorcycle', 'Motocicleta'),
('veh_truck', 'truck', 'Camión de carga'),
('pt_bus', 'bus', 'Bus de línea de transporte público'),
('pt_tram', 'tram', 'Tranvía');

-- Tabla: Franjas Horarias (para análisis)
CREATE TABLE time_periods (
    period_id SERIAL PRIMARY KEY,
    period_name VARCHAR(50) NOT NULL,
    start_hour INTEGER NOT NULL,
    end_hour INTEGER NOT NULL,
    description TEXT
);

-- Insertar franjas horarias según el .bat
INSERT INTO time_periods (period_name, start_hour, end_hour, description) VALUES
('MADRUGADA', 0, 5, 'Madrugada (00:00-05:00)'),
('MAÑANA', 5, 7, 'Mañana temprano (05:00-07:00)'),
('PICO_AM', 7, 9, 'Hora pico matutina (07:00-09:00)'),
('DIA', 9, 17, 'Día normal (09:00-17:00)'),
('PICO_PM', 17, 19, 'Hora pico vespertina (17:00-19:00)'),
('NOCHE', 19, 24, 'Noche (19:00-24:00)');

-- ============================================================
-- TABLAS DINÁMICAS (Datos de Simulación - Time-Series)
-- ============================================================

-- Tabla: Viajes de Vehículos (tripinfo.xml)
CREATE TABLE vehicle_trips (
    time TIMESTAMPTZ NOT NULL,
    run_id INTEGER REFERENCES simulation_runs(run_id),
    vehicle_id VARCHAR(100) NOT NULL,
    vehicle_type VARCHAR(50) REFERENCES vehicle_types(vtype_id),
    depart_time FLOAT NOT NULL,
    arrival_time FLOAT,
    duration FLOAT,
    route_length FLOAT,
    waiting_time FLOAT,
    time_loss FLOAT,
    depart_delay FLOAT,
    depart_lane VARCHAR(100),
    from_edge VARCHAR(100),
    to_edge VARCHAR(100),
    max_speed FLOAT,
    avg_speed FLOAT,
    -- Campos adicionales
    period VARCHAR(50),
    completed BOOLEAN DEFAULT FALSE
);

-- Convertir a hypertable (time-series optimizada)
SELECT create_hypertable('vehicle_trips', 'time');

-- Índices para consultas comunes
CREATE INDEX idx_vehicle_trips_vehicle ON vehicle_trips(vehicle_id);
CREATE INDEX idx_vehicle_trips_type ON vehicle_trips(vehicle_type);
CREATE INDEX idx_vehicle_trips_period ON vehicle_trips(period);
CREATE INDEX idx_vehicle_trips_run ON vehicle_trips(run_id);

-- Tabla: Datos de Aristas/Calles (edgeData.xml)
CREATE TABLE edge_data (
    time TIMESTAMPTZ NOT NULL,
    run_id INTEGER REFERENCES simulation_runs(run_id),
    edge_id VARCHAR(100) NOT NULL,
    interval_begin FLOAT NOT NULL,
    interval_end FLOAT NOT NULL,
    -- Métricas agregadas por intervalo
    num_vehicles INTEGER DEFAULT 0,
    avg_speed FLOAT,
    avg_occupancy FLOAT,
    avg_density FLOAT,
    avg_waiting_time FLOAT,
    total_travel_time FLOAT,
    total_co2 FLOAT,
    total_fuel FLOAT
);

-- Convertir a hypertable
SELECT create_hypertable('edge_data', 'time');

-- Índices
CREATE INDEX idx_edge_data_edge ON edge_data(edge_id);
CREATE INDEX idx_edge_data_run ON edge_data(run_id);

-- Tabla: Estadísticas Generales por Timestep (stats.xml)
CREATE TABLE simulation_stats (
    time TIMESTAMPTZ NOT NULL,
    run_id INTEGER REFERENCES simulation_runs(run_id),
    timestep FLOAT NOT NULL,
    -- Vehículos
    vehicles_loaded INTEGER DEFAULT 0,
    vehicles_inserted INTEGER DEFAULT 0,
    vehicles_running INTEGER DEFAULT 0,
    vehicles_waiting INTEGER DEFAULT 0,
    -- Teleports y seguridad
    teleports_total INTEGER DEFAULT 0,
    teleports_jam INTEGER DEFAULT 0,
    teleports_yield INTEGER DEFAULT 0,
    collisions INTEGER DEFAULT 0,
    emergency_stops INTEGER DEFAULT 0,
    emergency_braking INTEGER DEFAULT 0,
    -- Estadísticas de viaje
    avg_route_length FLOAT,
    avg_speed FLOAT,
    avg_duration FLOAT,
    avg_waiting_time FLOAT,
    avg_time_loss FLOAT,
    total_travel_time FLOAT
);

-- Convertir a hypertable
SELECT create_hypertable('simulation_stats', 'time');
CREATE INDEX idx_simulation_stats_run ON simulation_stats(run_id);

-- Tabla: Paradas de Transporte Público (stopinfos.xml)
CREATE TABLE pt_stops (
    time TIMESTAMPTZ NOT NULL,
    run_id INTEGER REFERENCES simulation_runs(run_id),
    stop_id VARCHAR(100) NOT NULL,
    vehicle_id VARCHAR(100),
    started FLOAT,
    ended FLOAT,
    delay FLOAT,
    passengers_boarding INTEGER DEFAULT 0,
    passengers_alighting INTEGER DEFAULT 0,
    passengers_loaded INTEGER DEFAULT 0
);

-- Convertir a hypertable
SELECT create_hypertable('pt_stops', 'time');
CREATE INDEX idx_pt_stops_stop ON pt_stops(stop_id);
CREATE INDEX idx_pt_stops_vehicle ON pt_stops(vehicle_id);

-- ============================================================
-- VISTAS ÚTILES PARA ANÁLISIS
-- ============================================================

-- Vista: Tráfico por Franja Horaria
CREATE VIEW traffic_by_period AS
SELECT 
    tp.period_name,
    vt.vclass,
    COUNT(*) as total_trips,
    AVG(duration) as avg_duration,
    AVG(route_length) as avg_distance,
    AVG(avg_speed) as avg_speed,
    SUM(waiting_time) as total_waiting_time
FROM vehicle_trips vtrip
JOIN time_periods tp ON 
    EXTRACT(HOUR FROM vtrip.time) >= tp.start_hour 
    AND EXTRACT(HOUR FROM vtrip.time) < tp.end_hour
JOIN vehicle_types vt ON vtrip.vehicle_type = vt.vtype_id
GROUP BY tp.period_name, vt.vclass
ORDER BY tp.start_hour, vt.vclass;

-- Vista: Top Calles Congestionadas
CREATE VIEW congested_streets AS
SELECT 
    edge_id,
    COUNT(*) as measurements,
    AVG(num_vehicles) as avg_vehicles,
    AVG(avg_speed) as avg_speed,
    AVG(avg_density) as avg_density,
    AVG(avg_waiting_time) as avg_wait
FROM edge_data
GROUP BY edge_id
HAVING AVG(avg_speed) < 20  -- Velocidad < 20 km/h = congestionado
ORDER BY avg_wait DESC
LIMIT 50;

-- Vista: Resumen de Simulación
CREATE VIEW simulation_summary AS
SELECT 
    sr.run_id,
    sr.run_name,
    sr.start_time,
    sr.end_time,
    COUNT(DISTINCT vt.vehicle_id) as total_vehicles,
    AVG(vt.duration) as avg_trip_duration,
    AVG(vt.avg_speed) as avg_speed,
    SUM(vt.waiting_time) as total_waiting_time,
    MAX(ss.vehicles_running) as max_concurrent_vehicles
FROM simulation_runs sr
LEFT JOIN vehicle_trips vt ON sr.run_id = vt.run_id
LEFT JOIN simulation_stats ss ON sr.run_id = ss.run_id
GROUP BY sr.run_id, sr.run_name, sr.start_time, sr.end_time;

-- ============================================================
-- FUNCIONES AUXILIARES
-- ============================================================

-- Función: Obtener franja horaria desde segundos de simulación
CREATE OR REPLACE FUNCTION get_time_period(seconds FLOAT)
RETURNS VARCHAR AS $$
DECLARE
    hour INTEGER;
BEGIN
    hour := FLOOR(seconds / 3600) % 24;
    
    IF hour >= 0 AND hour < 5 THEN
        RETURN 'MADRUGADA';
    ELSIF hour >= 5 AND hour < 7 THEN
        RETURN 'MAÑANA';
    ELSIF hour >= 7 AND hour < 9 THEN
        RETURN 'PICO_AM';
    ELSIF hour >= 9 AND hour < 17 THEN
        RETURN 'DIA';
    ELSIF hour >= 17 AND hour < 19 THEN
        RETURN 'PICO_PM';
    ELSE
        RETURN 'NOCHE';
    END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================
-- POLÍTICAS DE RETENCIÓN (opcional - para bases de datos grandes)
-- ============================================================

-- Mantener datos detallados por 30 días, agregar datos antiguos
-- SELECT add_retention_policy('vehicle_trips', INTERVAL '30 days');
-- SELECT add_retention_policy('edge_data', INTERVAL '30 days');

-- Agregar datos cada hora (continuous aggregates)
-- CREATE MATERIALIZED VIEW edge_data_hourly
-- WITH (timescaledb.continuous) AS
-- SELECT time_bucket('1 hour', time) AS hour,
--        edge_id,
--        AVG(avg_speed) as avg_speed,
--        AVG(num_vehicles) as avg_vehicles
-- FROM edge_data
-- GROUP BY hour, edge_id;

-- ============================================================
-- COMENTARIOS Y DOCUMENTACIÓN
-- ============================================================

COMMENT ON TABLE vehicle_trips IS 'Información de viajes completados por vehículos (tripinfo.xml)';
COMMENT ON TABLE edge_data IS 'Datos agregados por calle/arista en intervalos (edgeData.xml)';
COMMENT ON TABLE simulation_stats IS 'Estadísticas generales de la simulación por timestep (stats.xml)';
COMMENT ON TABLE pt_stops IS 'Información de paradas de transporte público (stopinfos.xml)';

-- ============================================================
PRINT 'Schema creado exitosamente! ✓';
