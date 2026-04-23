# 📊 Configuración de Grafana para Visualización de Datos SUMO

## Acceso Inicial

1. Abrir navegador: http://localhost:3000
2. Login:
   - Usuario: `admin`
   - Contraseña: `admin123`
3. (Opcional) Cambiar contraseña cuando lo pida

---

## Configurar Data Source (PostgreSQL)

### Paso 1: Agregar Data Source

1. En el menú lateral, ir a: **Configuration** (⚙️) → **Data Sources**
2. Click en **Add data source**
3. Buscar y seleccionar **PostgreSQL**

### Paso 2: Configuración

Llenar los siguientes campos:

**Básicos:**
- **Name:** `SUMO Traffic DB`
- **Host:** `timescaledb:5432` (usar nombre del contenedor, NO localhost)
- **Database:** `sumo_traffic`
- **User:** `postgres`
- **Password:** `sumo123`
- **TLS/SSL Mode:** `disable`

**TimescaleDB:**
- Marcar la casilla: ☑ **TimescaleDB**

**Avanzado (opcional):**
- **Max open:** `100`
- **Max idle:** `25`

### Paso 3: Probar y Guardar

1. Click en **Save & Test**
2. Debe aparecer: ✅ "Database Connection OK"

---

## Dashboards Sugeridos

### Dashboard 1: Resumen General

**Panel 1.1 - Vehículos Activos en Tiempo Real**
- **Tipo:** Time series (línea)
- **Query:**
```sql
SELECT 
  time_bucket('1 minute', time) as time,
  COUNT(*) as vehiculos
FROM vehicle_trips
WHERE $__timeFilter(time)
GROUP BY time_bucket('1 minute', time)
ORDER BY time_bucket('1 minute', time)
```

**Panel 1.2 - Velocidad Promedio**
- **Tipo:** Gauge (medidor)
- **Query:**
```sql
SELECT 
  AVG(avg_speed) * 3.6 as velocidad_kmh
FROM vehicle_trips
WHERE $__timeFilter(time)
```
- **Unit:** km/h
- **Min:** 0
- **Max:** 120

**Panel 1.3 - Vehículos por Tipo (Pie Chart)**
- **Tipo:** Pie chart
- **Query:**
```sql
SELECT 
  vehicle_type as metric,
  COUNT(*) as value
FROM vehicle_trips
WHERE $__timeFilter(time)
GROUP BY vehicle_type
```

**Panel 1.4 - Tiempo de Espera Promedio**
- **Tipo:** Stat (número grande)
- **Query:**
```sql
SELECT 
  AVG(waiting_time) as espera_segundos
FROM vehicle_trips
WHERE $__timeFilter(time)
```
- **Unit:** seconds

---

### Dashboard 2: Análisis por Franja Horaria

**Panel 2.1 - Tráfico por Hora del Día**
- **Tipo:** Bar chart (barras)
- **Query:**
```sql
SELECT 
  EXTRACT(HOUR FROM time) as hora,
  COUNT(*) as vehiculos
FROM vehicle_trips
WHERE $__timeFilter(time)
GROUP BY hora
ORDER BY hora
```

**Panel 2.2 - Comparación Pico AM vs PM**
- **Tipo:** Table
- **Query:**
```sql
SELECT 
  period as "Período",
  COUNT(*) as "Total Viajes",
  ROUND(AVG(duration), 2) as "Duración Promedio (s)",
  ROUND(AVG(waiting_time), 2) as "Espera Promedio (s)"
FROM vehicle_trips
WHERE period IN ('PICO_AM', 'PICO_PM')
  AND $__timeFilter(time)
GROUP BY period
```

---

### Dashboard 3: Calles Congestionadas

**Panel 3.1 - Top 10 Calles Más Lentas**
- **Tipo:** Bar gauge (barras horizontales)
- **Query:**
```sql
SELECT 
  edge_id as metric,
  AVG(avg_speed) as value
FROM edge_data
WHERE $__timeFilter(time)
  AND avg_speed > 0
GROUP BY edge_id
ORDER BY value ASC
LIMIT 10
```

**Panel 3.2 - Mapa de Calor - Densidad por Hora**
- **Tipo:** Heatmap
- **Query:**
```sql
SELECT 
  time_bucket('1 hour', time) as time,
  edge_id as metric,
  AVG(avg_density) as value
FROM edge_data
WHERE $__timeFilter(time)
GROUP BY time_bucket('1 hour', time), edge_id
ORDER BY time_bucket('1 hour', time)
```

---

### Dashboard 4: Transporte Público

**Panel 4.1 - Retrasos Promedio por Parada**
- **Tipo:** Table
- **Query:**
```sql
SELECT 
  stop_id as "Parada",
  COUNT(*) as "Total Paradas",
  ROUND(AVG(delay), 2) as "Retraso Promedio (s)",
  SUM(passengers_boarding) as "Pasajeros Subieron"
FROM pt_stops
WHERE $__timeFilter(time)
GROUP BY stop_id
ORDER BY AVG(delay) DESC
LIMIT 20
```

**Panel 4.2 - Evolución de Retrasos**
- **Tipo:** Time series
- **Query:**
```sql
SELECT 
  time_bucket('5 minutes', time) as time,
  AVG(delay) as retraso_promedio
FROM pt_stops
WHERE $__timeFilter(time)
  AND delay > 0
GROUP BY time_bucket('5 minutes', time)
ORDER BY time_bucket('5 minutes', time)
```

---

## Variables de Dashboard (opcional)

Para hacer dashboards dinámicos, agregar variables:

### Variable 1: Simulación
- **Name:** `run_id`
- **Type:** Query
- **Data source:** SUMO Traffic DB
- **Query:**
```sql
SELECT run_id as __value, run_name as __text
FROM simulation_runs
ORDER BY start_time DESC
```

### Variable 2: Tipo de Vehículo
- **Name:** `vehicle_type`
- **Type:** Query
- **Data source:** SUMO Traffic DB
- **Query:**
```sql
SELECT DISTINCT vtype_id as __value, vtype_id as __text
FROM vehicle_types
ORDER BY vtype_id
```

Luego usar en queries:
```sql
WHERE run_id = $run_id
  AND vehicle_type = '$vehicle_type'
```

---

## Tips y Trucos

### 1. Refresh automático
- En configuración del dashboard: **Refresh:** `5s` o `10s`

### 2. Time range útiles
- Últimos 5 minutos: `now-5m to now`
- Última hora: `now-1h to now`
- Día completo: `now/d to now`

### 3. Alertas (opcional)
Puedes crear alertas cuando:
- Velocidad promedio < 10 km/h (congestion)
- Más de 100 vehículos esperando
- Retrasos en buses > 120 segundos

---

## Exportar/Importar Dashboards

### Exportar
1. Dashboard → Settings (⚙️) → JSON Model
2. Copiar JSON
3. Guardar en archivo `.json`

### Importar
1. Home → Import
2. Pegar JSON o subir archivo
3. Seleccionar data source: `SUMO Traffic DB`
4. Import

---

## Dashboards Community (opcional)

Si quieres usar dashboards pre-hechos para PostgreSQL/TimescaleDB:
1. Ir a: https://grafana.com/grafana/dashboards
2. Buscar: "PostgreSQL" o "TimescaleDB"
3. Copiar el ID del dashboard
4. En Grafana: Home → Import → pegar ID

---

## Solución de Problemas

### No aparecen datos
- Verificar que el data source está bien configurado
- Verificar que hay datos en la BD: `SELECT COUNT(*) FROM vehicle_trips;`
- Ajustar el time range

### Error "could not connect"
- Usar `timescaledb` como host, NO `localhost`
- Verificar credenciales

### Gráficas muy lentas
- Agregar más filtros WHERE
- Usar `time_bucket` para agregaciones
- Limitar con LIMIT en queries

---

**¡Listo para visualizar tu tráfico! 📊**
