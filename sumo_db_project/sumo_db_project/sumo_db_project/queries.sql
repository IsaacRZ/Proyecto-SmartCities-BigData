-- ============================================================
-- CONSULTAS SQL ÚTILES PARA ANÁLISIS DE TRÁFICO
-- Sistema SUMO - San José, Costa Rica
-- ============================================================

-- ============================================================
-- 1. CONSULTAS BÁSICAS
-- ============================================================

-- Ver todas las simulaciones
SELECT * FROM simulation_runs ORDER BY start_time DESC;

-- Ver últimos 20 viajes
SELECT 
    vehicle_id,
    vehicle_type,
    period,
    ROUND(duration, 2) as duration_sec,
    ROUND(route_length, 2) as distance_m,
    ROUND(avg_speed, 2) as speed_ms
FROM vehicle_trips
ORDER BY time DESC
LIMIT 20;

-- Estadísticas generales de la última simulación
SELECT * FROM simulation_summary ORDER BY run_id DESC LIMIT 1;

-- ============================================================
-- 2. ANÁLISIS POR FRANJA HORARIA
-- ============================================================

-- Tráfico por franja horaria (usando vista)
SELECT 
    period_name,
    vclass,
    total_trips,
    ROUND(avg_duration, 2) as avg_duration_sec,
    ROUND(avg_distance, 2) as avg_distance_m,
    ROUND(avg_speed, 2) as avg_speed_ms
FROM traffic_by_period
ORDER BY 
    CASE period_name
        WHEN 'MADRUGADA' THEN 1
        WHEN 'MAÑANA' THEN 2
        WHEN 'PICO_AM' THEN 3
        WHEN 'DIA' THEN 4
        WHEN 'PICO_PM' THEN 5
        WHEN 'NOCHE' THEN 6
    END,
    vclass;

-- Comparar hora pico AM vs PM
SELECT 
    period,
    COUNT(*) as total_viajes,
    ROUND(AVG(duration), 2) as duracion_promedio,
    ROUND(AVG(waiting_time), 2) as espera_promedio,
    ROUND(AVG(time_loss), 2) as tiempo_perdido,
    ROUND(AVG(avg_speed), 2) as velocidad_promedio
FROM vehicle_trips
WHERE period IN ('PICO_AM', 'PICO_PM')
GROUP BY period;

-- Distribución de vehículos por hora
SELECT 
    EXTRACT(HOUR FROM time) as hora,
    COUNT(*) as total_vehiculos,
    ROUND(AVG(avg_speed), 2) as velocidad_promedio,
    ROUND(AVG(waiting_time), 2) as espera_promedio
FROM vehicle_trips
GROUP BY hora
ORDER BY hora;

-- ============================================================
-- 3. ANÁLISIS POR TIPO DE VEHÍCULO
-- ============================================================

-- Métricas por tipo de vehículo
SELECT 
    vt.vclass,
    COUNT(*) as total_viajes,
    ROUND(AVG(trip.duration), 2) as duracion_avg,
    ROUND(AVG(trip.route_length), 2) as distancia_avg,
    ROUND(AVG(trip.avg_speed), 2) as velocidad_avg,
    ROUND(AVG(trip.waiting_time), 2) as espera_avg
FROM vehicle_trips trip
JOIN vehicle_types vt ON trip.vehicle_type = vt.vtype_id
GROUP BY vt.vclass
ORDER BY total_viajes DESC;

-- Top 10 vehículos con mayor tiempo de espera
SELECT 
    vehicle_id,
    vehicle_type,
    period,
    ROUND(waiting_time, 2) as espera_segundos,
    ROUND(waiting_time/60, 2) as espera_minutos
FROM vehicle_trips
WHERE waiting_time > 0
ORDER BY waiting_time DESC
LIMIT 10;

-- Vehículos más rápidos y más lentos
(SELECT 'MÁS RÁPIDOS' as categoria, vehicle_id, vehicle_type, 
    ROUND(avg_speed * 3.6, 2) as velocidad_kmh,
    ROUND(route_length, 2) as distancia_m
FROM vehicle_trips
WHERE avg_speed > 0
ORDER BY avg_speed DESC
LIMIT 5)
UNION ALL
(SELECT 'MÁS LENTOS' as categoria, vehicle_id, vehicle_type,
    ROUND(avg_speed * 3.6, 2) as velocidad_kmh,
    ROUND(route_length, 2) as distancia_m
FROM vehicle_trips
WHERE avg_speed > 0
ORDER BY avg_speed ASC
LIMIT 5);

-- ============================================================
-- 4. ANÁLISIS DE CALLES Y RUTAS
-- ============================================================

-- Top 20 calles más congestionadas
SELECT * FROM congested_streets LIMIT 20;

-- Calles con mayor densidad promedio
SELECT 
    edge_id,
    COUNT(*) as mediciones,
    ROUND(AVG(avg_density), 2) as densidad_promedio,
    ROUND(AVG(avg_speed), 2) as velocidad_promedio,
    ROUND(AVG(avg_occupancy), 2) as ocupacion_promedio
FROM edge_data
GROUP BY edge_id
HAVING COUNT(*) > 10
ORDER BY densidad_promedio DESC
LIMIT 20;

-- Rutas más utilizadas (from -> to)
SELECT 
    from_edge,
    to_edge,
    COUNT(*) as total_viajes,
    ROUND(AVG(duration), 2) as duracion_promedio,
    ROUND(AVG(route_length), 2) as distancia_promedio
FROM vehicle_trips
WHERE from_edge IS NOT NULL AND to_edge IS NOT NULL
GROUP BY from_edge, to_edge
HAVING COUNT(*) > 5
ORDER BY total_viajes DESC
LIMIT 20;

-- Calles con mayor tiempo de espera
SELECT 
    edge_id,
    ROUND(AVG(avg_waiting_time), 2) as espera_promedio,
    ROUND(AVG(num_vehicles), 2) as vehiculos_promedio,
    ROUND(AVG(avg_speed), 2) as velocidad_promedio
FROM edge_data
WHERE avg_waiting_time > 0
GROUP BY edge_id
ORDER BY espera_promedio DESC
LIMIT 20;

-- ============================================================
-- 5. EVOLUCIÓN TEMPORAL
-- ============================================================

-- Tráfico por minuto (útil para gráficas)
SELECT 
    DATE_TRUNC('minute', time) as minuto,
    COUNT(*) as vehiculos,
    ROUND(AVG(avg_speed), 2) as velocidad_promedio
FROM vehicle_trips
GROUP BY minuto
ORDER BY minuto;

-- Progreso de la simulación (vehículos activos por intervalo)
SELECT 
    interval_begin / 3600 as hora,
    SUM(num_vehicles) as vehiculos_totales,
    ROUND(AVG(avg_speed), 2) as velocidad_promedio
FROM edge_data
GROUP BY hora
ORDER BY hora;

-- ============================================================
-- 6. TRANSPORTE PÚBLICO
-- ============================================================

-- Paradas más utilizadas
SELECT 
    stop_id,
    COUNT(*) as total_paradas,
    ROUND(AVG(delay), 2) as retraso_promedio,
    SUM(passengers_boarding) as pasajeros_subieron,
    SUM(passengers_loaded) as pasajeros_total
FROM pt_stops
GROUP BY stop_id
ORDER BY total_paradas DESC
LIMIT 20;

-- Buses con mayores retrasos
SELECT 
    vehicle_id,
    COUNT(*) as total_paradas,
    ROUND(AVG(delay), 2) as retraso_promedio,
    ROUND(MAX(delay), 2) as retraso_maximo
FROM pt_stops
WHERE delay > 0
GROUP BY vehicle_id
ORDER BY retraso_promedio DESC
LIMIT 10;

-- ============================================================
-- 7. SEGURIDAD Y INCIDENTES
-- ============================================================

-- Estadísticas de seguridad
SELECT 
    SUM(collisions) as colisiones_totales,
    SUM(emergency_stops) as paradas_emergencia,
    SUM(emergency_braking) as frenadas_emergencia,
    SUM(teleports_total) as teleports_totales
FROM simulation_stats;

-- Momentos con más incidentes
SELECT 
    timestep / 3600 as hora,
    collisions,
    emergency_stops,
    emergency_braking,
    vehicles_running as vehiculos_activos
FROM simulation_stats
WHERE collisions > 0 OR emergency_stops > 0
ORDER BY timestep;

-- ============================================================
-- 8. COMPARACIONES ENTRE SIMULACIONES
-- ============================================================

-- Comparar múltiples simulaciones
SELECT 
    sr.run_name,
    COUNT(DISTINCT vt.vehicle_id) as total_vehiculos,
    ROUND(AVG(vt.duration), 2) as duracion_promedio,
    ROUND(AVG(vt.avg_speed), 2) as velocidad_promedio,
    ROUND(AVG(vt.waiting_time), 2) as espera_promedio
FROM simulation_runs sr
LEFT JOIN vehicle_trips vt ON sr.run_id = vt.run_id
GROUP BY sr.run_id, sr.run_name
ORDER BY sr.start_time DESC;

-- Comparar hora pico entre simulaciones
SELECT 
    sr.run_name,
    vt.period,
    COUNT(*) as total_viajes,
    ROUND(AVG(vt.waiting_time), 2) as espera_promedio
FROM vehicle_trips vt
JOIN simulation_runs sr ON vt.run_id = sr.run_id
WHERE vt.period IN ('PICO_AM', 'PICO_PM')
GROUP BY sr.run_name, vt.period
ORDER BY sr.run_name, vt.period;

-- ============================================================
-- 9. EMISIONES Y CONSUMO (si hay datos)
-- ============================================================

-- Emisiones totales por calle
SELECT 
    edge_id,
    ROUND(SUM(total_co2), 2) as co2_total_mg,
    ROUND(SUM(total_fuel), 2) as combustible_total_ml,
    ROUND(AVG(avg_speed), 2) as velocidad_promedio
FROM edge_data
WHERE total_co2 > 0
GROUP BY edge_id
ORDER BY co2_total_mg DESC
LIMIT 20;

-- ============================================================
-- 10. ANÁLISIS AVANZADO CON TIMESCALEDB
-- ============================================================

-- Resumen por hora usando time_bucket
SELECT 
    time_bucket('1 hour', time) as hora,
    COUNT(*) as total_viajes,
    ROUND(AVG(avg_speed), 2) as velocidad_promedio,
    ROUND(AVG(waiting_time), 2) as espera_promedio
FROM vehicle_trips
GROUP BY hora
ORDER BY hora;

-- Percentiles de velocidad
SELECT 
    percentile_cont(0.25) WITHIN GROUP (ORDER BY avg_speed) as p25,
    percentile_cont(0.50) WITHIN GROUP (ORDER BY avg_speed) as mediana,
    percentile_cont(0.75) WITHIN GROUP (ORDER BY avg_speed) as p75,
    percentile_cont(0.90) WITHIN GROUP (ORDER BY avg_speed) as p90,
    percentile_cont(0.95) WITHIN GROUP (ORDER BY avg_speed) as p95
FROM vehicle_trips;

-- ============================================================
-- 11. EXPORTAR DATOS PARA ANÁLISIS EXTERNO
-- ============================================================

-- Exportar resumen a CSV (desde psql)
-- \copy (SELECT * FROM traffic_by_period) TO 'C:/temp/traffic_summary.csv' CSV HEADER;

-- Exportar top calles congestionadas
-- \copy (SELECT * FROM congested_streets LIMIT 50) TO 'C:/temp/congested.csv' CSV HEADER;

-- ============================================================
-- 12. LIMPIEZA Y MANTENIMIENTO
-- ============================================================

-- Ver tamaño de las tablas
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Eliminar simulación específica
-- DELETE FROM vehicle_trips WHERE run_id = 1;
-- DELETE FROM edge_data WHERE run_id = 1;
-- DELETE FROM simulation_stats WHERE run_id = 1;
-- DELETE FROM pt_stops WHERE run_id = 1;
-- DELETE FROM simulation_runs WHERE run_id = 1;

-- Vacuum para recuperar espacio
-- VACUUM ANALYZE;

-- ============================================================
