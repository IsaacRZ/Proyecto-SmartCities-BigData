-- Queries SQL para Grafana - Smart Cities Traffic Dashboard
-- Usar estas queries para crear paneles en Grafana

-- ============================================================
-- PANEL 1: Congestión por hora (Línea)
-- ============================================================
SELECT 
    hour as "Hora",
    ROUND(AVG(avg_congestion)::numeric, 2) as "Congestión Promedio",
    MAX(max_congestion) as "Congestión Máxima"
FROM traffic_metrics
GROUP BY hour
ORDER BY hour;

-- ============================================================
-- PANEL 2: Top 10 Tramos más congestionados
-- ============================================================
SELECT 
    idTram as "ID Tramo",
    ROUND(AVG(avg_congestion)::numeric, 2) as "Congestión Promedio",
    MAX(max_congestion) as "Máximo",
    SUM(observation_count) as "Observaciones"
FROM traffic_metrics
GROUP BY idTram
ORDER BY AVG(avg_congestion) DESC
LIMIT 10;

-- ============================================================
-- PANEL 3: Evolución de congestión por tramo (seleccionar tramo)
-- ============================================================
SELECT 
    timestamp,
    idTram,
    avg_congestion,
    max_congestion,
    min_congestion
FROM traffic_metrics
WHERE idTram = $TRAMO_ID  -- Variable de Grafana
ORDER BY timestamp DESC
LIMIT 1000;

-- ============================================================
-- PANEL 4: Matriz de congestión por hora x tramo
-- ============================================================
SELECT 
    hour,
    idTram,
    ROUND(AVG(avg_congestion)::numeric, 2) as congestion
FROM traffic_metrics
GROUP BY hour, idTram
ORDER BY hour, idTram;

-- ============================================================
-- PANEL 5: Alertas críticas (tabla)
-- ============================================================
SELECT 
    idTram,
    timestamp,
    estatActual as "Estado Actual",
    severity as "Severidad",
    COUNT(*) as "Ocurrencias"
FROM alerts
WHERE severity != 'MEDIA'
GROUP BY idTram, timestamp, estatActual, severity
ORDER BY timestamp DESC
LIMIT 25;

-- ============================================================
-- PANEL 6: Estadísticas agregadas (Gauge/Stat)
-- ============================================================
SELECT 
    ROUND(AVG(avg_congestion)::numeric, 2) as "Congestión Global",
    MAX(max_congestion) as "Pico de Congestión",
    COUNT(DISTINCT idTram) as "Tramos Activos",
    SUM(observation_count) as "Total Observaciones"
FROM traffic_metrics
WHERE timestamp > NOW() - INTERVAL '24 hours';

-- ============================================================
-- PANEL 7: Predicciones de incidentes (tabla)
-- ============================================================
SELECT 
    idTram,
    hour,
    estatActual as "Estado",
    ROUND(prediction::numeric, 3) as "Probabilidad Incidente"
FROM predictions
WHERE prediction > 0.3
ORDER BY prediction DESC, idTram
LIMIT 20;

-- ============================================================
-- PANEL 8: Recomendaciones de rutas por hora
-- ============================================================
SELECT 
    hour as "Hora",
    idTram as "Tramo",
    recommendation as "Tipo Ruta",
    COUNT(*) as "Frecuencia"
FROM route_recommendations
GROUP BY hour, idTram, recommendation
ORDER BY hour, frecuencia DESC;

-- ============================================================
-- PANEL 9: Heatmap - Congestión por hora y día
-- ============================================================
SELECT 
    EXTRACT(DOW FROM timestamp) as "Día Semana",
    hour as "Hora",
    ROUND(AVG(avg_congestion)::numeric, 2) as "Congestión"
FROM traffic_metrics
GROUP BY EXTRACT(DOW FROM timestamp), hour
ORDER BY "Día Semana", hour;

-- ============================================================
-- TABLA AUXILIAR: Crear tabla de alertas si no existe
-- ============================================================
-- CREATE TABLE IF NOT EXISTS alerts (
--     idTram INTEGER,
--     timestamp TIMESTAMP,
--     estatActual INTEGER,
--     severity VARCHAR(50),
--     PRIMARY KEY (idTram, timestamp)
-- );

-- ============================================================
-- TABLA AUXILIAR: Crear tabla de predicciones si no existe
-- ============================================================
-- CREATE TABLE IF NOT EXISTS predictions (
--     idTram INTEGER,
--     hour INTEGER,
--     estatActual INTEGER,
--     prediction FLOAT,
--     timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- ============================================================
-- TABLA AUXILIAR: Crear tabla de recomendaciones si no existe
-- ============================================================
-- CREATE TABLE IF NOT EXISTS route_recommendations (
--     idTram INTEGER,
--     hour INTEGER,
--     recommendation VARCHAR(50),
--     timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );
