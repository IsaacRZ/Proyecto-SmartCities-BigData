# 🚦 Sistema de Base de Datos para Simulaciones SUMO
### San José, Costa Rica - Datos de Tráfico en Tiempo Real

---

## 📋 Tabla de Contenido
1. [Requisitos](#requisitos)
2. [Instalación en Windows](#instalación-en-windows)
3. [Configuración](#configuración)
4. [Uso Básico](#uso-básico)
5. [Estructura de la Base de Datos](#estructura-de-la-base-de-datos)
6. [Consultas SQL Útiles](#consultas-sql-útiles)
7. [Deployment en Cloud](#deployment-en-cloud)

---

## 🔧 Requisitos

### En tu PC Windows:
- **Docker Desktop** (descarga: https://www.docker.com/products/docker-desktop/)
- **Python 3.8+** (descarga: https://www.python.org/downloads/)
- Espacio en disco: ~5GB para Docker + datos

### Opcional:
- **DBeaver** o **pgAdmin** (interfaces gráficas para la BD)

---

## 💻 Instalación en Windows

### Paso 1: Instalar Docker Desktop

1. Descarga Docker Desktop desde: https://www.docker.com/products/docker-desktop/
2. Ejecuta el instalador
3. Reinicia tu computadora cuando te lo pida
4. Abre Docker Desktop y deja que termine de inicializar
5. Verifica que esté corriendo (icono en la barra de tareas)

### Paso 2: Descargar este Proyecto

Copia toda la carpeta `sumo_db_project` a tu PC. Estructura:

```
sumo_db_project/
├── docker-compose.yml          # Configuración de Docker
├── init-db/
│   └── 01_schema.sql          # Schema de la base de datos
├── sumo_importer.py           # Script de importación
├── requirements.txt           # Dependencias de Python
├── README.md                  # Este archivo
└── queries.sql                # Consultas de ejemplo
```

### Paso 3: Instalar Python y Dependencias

```bash
# Abrir PowerShell o CMD en la carpeta del proyecto
cd ruta\a\sumo_db_project

# Instalar librerías de Python
pip install psycopg2-binary
```

### Paso 4: Levantar la Base de Datos

```bash
# En PowerShell o CMD, dentro de sumo_db_project/
docker-compose up -d
```

Esto descargará las imágenes (primera vez ~1GB) y levantará:
- **PostgreSQL + TimescaleDB** en puerto 5432
- **pgAdmin** en http://localhost:5050
- **Grafana** en http://localhost:3000

**Verificar que funciona:**
```bash
docker ps
```
Deberías ver 3 contenedores corriendo: `sumo_traffic_db`, `sumo_pgadmin`, `sumo_grafana`

---

## ⚙️ Configuración

### Credenciales por Defecto:

| Servicio | Usuario | Contraseña | Puerto/URL |
|----------|---------|------------|------------|
| PostgreSQL | `postgres` | `sumo123` | `localhost:5432` |
| pgAdmin | `admin@sumo.com` | `admin123` | http://localhost:5050 |
| Grafana | `admin` | `admin123` | http://localhost:3000 |

### Cambiar Contraseñas (Opcional):

Edita `docker-compose.yml` ANTES del primer `docker-compose up`:
```yaml
environment:
  POSTGRES_PASSWORD: TU_NUEVA_CONTRASEÑA
```

---

## 🚀 Uso Básico

### 1. Importar Datos de SUMO

Después de correr tu simulación en SUMO, importa los XML:

```bash
python sumo_importer.py \
  --dir "C:\Users\TuUsuario\ruta\a\archivos\sumo" \
  --run-name "Simulacion_SanJose_2024_01"
```

**Parámetros:**
- `--dir`: Carpeta con los archivos XML (`tripinfos.xml`, `stats.xml`, etc.)
- `--run-name`: Nombre descriptivo de la simulación
- Opcionales: `--host`, `--port`, `--database`, `--user`, `--password`

**Ejemplo real con tus archivos:**
```bash
python sumo_importer.py ^
  --dir "C:\Users\sebas\2026-02-15-18-21-36\2026-02-15-18-31-42" ^
  --run-name "Barcelona_San_Jose_Primera_Prueba"
```

### 2. Consultar Datos

**Opción A: pgAdmin (Interfaz Gráfica)**
1. Abre http://localhost:5050
2. Login: `admin@sumo.com` / `admin123`
3. Add New Server:
   - Name: `SUMO Traffic`
   - Host: `timescaledb` (nombre del contenedor)
   - Port: `5432`
   - Database: `sumo_traffic`
   - Username: `postgres`
   - Password: `sumo123`

**Opción B: Línea de Comandos**
```bash
# Windows PowerShell
docker exec -it sumo_traffic_db psql -U postgres -d sumo_traffic

# Ahora estás dentro de PostgreSQL
sumo_traffic=# SELECT * FROM simulation_runs;
```

### 3. Detener/Reiniciar

```bash
# Detener (datos se mantienen)
docker-compose down

# Reiniciar
docker-compose up -d

# Ver logs
docker-compose logs -f

# BORRAR TODO (incluyendo datos)
docker-compose down -v
```

---

## 🗄️ Estructura de la Base de Datos

### Tablas Principales

#### 1. `vehicle_trips` (Time-Series)
Información de cada viaje completado:
```sql
SELECT vehicle_id, vehicle_type, duration, avg_speed, period
FROM vehicle_trips
LIMIT 10;
```

**Campos importantes:**
- `vehicle_id`: ID único del vehículo
- `vehicle_type`: passenger, bus, motorcycle, truck
- `depart_time`, `arrival_time`: Tiempos en segundos
- `route_length`: Distancia recorrida (metros)
- `avg_speed`: Velocidad promedio (m/s)
- `waiting_time`: Tiempo esperando (segundos)
- `period`: MADRUGADA, MAÑANA, PICO_AM, DIA, PICO_PM, NOCHE

#### 2. `edge_data` (Time-Series)
Métricas por calle/arista:
```sql
SELECT edge_id, avg_speed, num_vehicles, avg_density
FROM edge_data
WHERE avg_speed < 5  -- Calles congestionadas
ORDER BY num_vehicles DESC;
```

#### 3. `simulation_stats` (Time-Series)
Estadísticas globales por timestep:
```sql
SELECT timestep, vehicles_running, collisions, avg_speed
FROM simulation_stats
ORDER BY timestep;
```

#### 4. `pt_stops`
Paradas de transporte público:
```sql
SELECT stop_id, COUNT(*) as total_stops, AVG(delay) as avg_delay
FROM pt_stops
GROUP BY stop_id;
```

### Vistas Útiles

#### `traffic_by_period`
Tráfico agregado por franja horaria:
```sql
SELECT * FROM traffic_by_period
ORDER BY period_name;
```

#### `congested_streets`
Top 50 calles más congestionadas:
```sql
SELECT * FROM congested_streets
LIMIT 20;
```

#### `simulation_summary`
Resumen de todas las simulaciones:
```sql
SELECT * FROM simulation_summary;
```

---

## 📊 Consultas SQL Útiles

### Análisis por Franja Horaria

```sql
-- Vehículos por hora del día
SELECT 
    EXTRACT(HOUR FROM time) as hora,
    COUNT(*) as total_vehiculos,
    AVG(avg_speed) as velocidad_promedio
FROM vehicle_trips
WHERE run_id = 1
GROUP BY hora
ORDER BY hora;
```

### Top Rutas Más Lentas

```sql
SELECT 
    from_edge,
    to_edge,
    COUNT(*) as viajes,
    AVG(duration) as duracion_promedio,
    AVG(avg_speed) as velocidad_promedio
FROM vehicle_trips
WHERE route_length > 1000  -- Solo rutas > 1km
GROUP BY from_edge, to_edge
HAVING COUNT(*) > 10
ORDER BY duracion_promedio DESC
LIMIT 20;
```

### Comparar Hora Pico AM vs PM

```sql
SELECT 
    period,
    vehicle_type,
    COUNT(*) as total_viajes,
    AVG(waiting_time) as tiempo_espera_promedio,
    AVG(time_loss) as tiempo_perdido_promedio
FROM vehicle_trips
WHERE period IN ('PICO_AM', 'PICO_PM')
GROUP BY period, vehicle_type
ORDER BY period, vehicle_type;
```

### Evolución de Tráfico en Tiempo Real

```sql
SELECT 
    DATE_TRUNC('minute', time) as minuto,
    COUNT(*) as vehiculos_activos
FROM vehicle_trips
WHERE completed = false
GROUP BY minuto
ORDER BY minuto;
```

### Calles con Más Colisiones (si hay datos)

```sql
SELECT 
    edge_id,
    SUM(collisions) as total_colisiones
FROM simulation_stats ss
JOIN edge_data ed ON ss.run_id = ed.run_id
WHERE collisions > 0
GROUP BY edge_id
ORDER BY total_colisiones DESC;
```

---

## ☁️ Deployment en Cloud (Gratis)

### Opción 1: Oracle Cloud (Recomendada)

1. **Crear cuenta gratuita:** https://cloud.oracle.com/free
   - 2 VMs gratis PARA SIEMPRE
   - 200GB almacenamiento

2. **Crear VM Ubuntu:**
   - Shape: VM.Standard.E2.1.Micro
   - OS: Ubuntu 22.04
   - Abrir puerto 5432 en Security List

3. **Instalar PostgreSQL + TimescaleDB:**
```bash
# Conectarse por SSH
ssh ubuntu@tu-ip-publica

# Instalar PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib -y

# Instalar TimescaleDB
sudo sh -c "echo 'deb https://packagecloud.io/timescale/timescaledb/ubuntu/ $(lsb_release -c -s) main' > /etc/apt/sources.list.d/timescaledb.list"
wget --quiet -O - https://packagecloud.io/timescale/timescaledb/gpgkey | sudo apt-key add -
sudo apt update
sudo apt install timescaledb-2-postgresql-14 -y
sudo timescaledb-tune

# Configurar acceso remoto
sudo nano /etc/postgresql/14/main/postgresql.conf
# Cambiar: listen_addresses = '*'

sudo nano /etc/postgresql/14/main/pg_hba.conf
# Agregar: host all all 0.0.0.0/0 md5

sudo systemctl restart postgresql

# Crear base de datos
sudo -u postgres psql
CREATE DATABASE sumo_traffic;
\q

# Subir schema
scp init-db/01_schema.sql ubuntu@tu-ip:/tmp/
sudo -u postgres psql -d sumo_traffic -f /tmp/01_schema.sql
```

4. **Conectar desde tu PC:**
```bash
python sumo_importer.py \
  --host TU-IP-PUBLICA \
  --dir "C:\ruta\a\archivos" \
  --run-name "Simulacion_Cloud_01"
```

### Opción 2: AWS Free Tier

Similar pero con límite de 12 meses. Usar RDS PostgreSQL.

### Opción 3: Google Cloud Free Tier

- e2-micro gratis (límite de uso)
- 30GB disco

---

## 🔍 Troubleshooting

### Docker no inicia
```bash
# Windows: Asegurarte que WSL2 está habilitado
wsl --update
```

### No puedo conectarme a la BD
```bash
# Verificar que el contenedor corre
docker ps

# Ver logs
docker logs sumo_traffic_db

# Reiniciar contenedor
docker restart sumo_traffic_db
```

### Error "psycopg2 not found"
```bash
pip install psycopg2-binary
```

### Datos no aparecen en pgAdmin
- Verificar que usaste el host correcto: `timescaledb` (no `localhost`)
- Refrescar el schema en pgAdmin (click derecho → Refresh)

---

## 📝 Notas Adicionales

### Archivos XML que se procesan:
- ✅ `tripinfos.xml` → `vehicle_trips`
- ✅ `edgeData.xml` → `edge_data`
- ✅ `stats.xml` → `simulation_stats`
- ✅ `stopinfos.xml` → `pt_stops`

### Archivos que NO se procesan (aún):
- ❌ `osm.*.trips.xml` (se usa para generar la simulación)
- ❌ `vehroutes.xml` (rutas completas - futuro)

### Rendimiento:
- ~10,000 viajes/segundo en insert
- Consultas < 100ms con índices
- Compresión automática de TimescaleDB

---

## 📧 Soporte

Para un proyecto académico, documenta:
1. Capturas de pantalla de pgAdmin con datos
2. Consultas SQL que usaste
3. Gráficas de Grafana (opcional)

---

## 🎓 Para tu Proyecto Académico

### Reporte sugerido:
1. **Introducción**: Problema de tráfico en San José
2. **Metodología**: SUMO + PostgreSQL/TimescaleDB
3. **Resultados**: Consultas SQL con gráficas
4. **Conclusiones**: Insights de las franjas horarias

### Visualizaciones en Grafana:
- Panel 1: Vehículos activos por minuto
- Panel 2: Velocidad promedio por hora
- Panel 3: Top 10 calles congestionadas
- Panel 4: Comparación hora pico AM vs PM

---

**¡Éxito con tu proyecto! 🚀**
