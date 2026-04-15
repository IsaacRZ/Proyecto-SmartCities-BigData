# Smart Cities Traffic Pipeline - Guía de Ejecución

## 🎯 Descripción General

Pipeline completo de 8 fases usando Apache Spark para análisis de tráfico en tiempo real:

```
FASE 1  →  Spark lee y procesa tus datos CSV existentes
              ↓
FASE 2  →  Spark Streaming simula ingesta en vivo
              ↓
FASE 3  →  Arquitectura Lambda (batch + streaming juntos)
              ↓
FASE 4  →  MLlib clasifica niveles de congestión
              ↓
FASE 5  →  MLlib predice incidentes
              ↓
FASE 6  →  Alertas automáticas
              ↓
FASE 7  →  Recomendaciones de rutas
              ↓
FASE 8  →  Dashboard Grafana completo
```

---

## 📋 Requisitos

### Software
- Python 3.11+
- Apache Spark 3.5.0+
- Docker & Docker Compose (para PostgreSQL + Grafana)
- Conda (recomendado)

### Hardware
- Mínimo: 4GB RAM disponible
- Recomendado: 8GB+ RAM

---

## 🚀 Inicio Rápido (5 minutos)

### Paso 1: Configurar Ambiente Conda
```bash
# Crear y activar ambiente
conda env create -f env.yaml
conda activate project_smart_cities
```

### Paso 2: Iniciar Docker (Opcional pero recomendado)
```bash
cd sumo_db_project
docker-compose up -d

# Verificar que esté ejecutándose
docker-compose ps
```

### Paso 3: Ejecutar Pipeline
```bash
# Abrir Jupyter Lab
jupyter lab

# Ir a: notebooks/03_smart_cities_pipeline.ipynb
# Ejecutar todas las celdas (Shift+Enter)
```

---

## 📊 Fases Detalladas

### FASE 1: Batch Processing ✓
**Archivo**: `notebooks/03_smart_cities_pipeline.ipynb` - Celdas 1-3

```python
# Inicializa SparkSession
# Carga CSVs históricos (2025-08 a 2026-01)
# Limpia y transforma datos
# Calcula estadísticas descriptivas

Output: 
- df_processed (Spark DataFrame)
- stats_df (Pandas DataFrame)
```

**Datos de entrada**:
- `data/raw/2025-08.csv` a `2026-01.csv`
- Columnas: `idTram`, `data`, `estatActual`, `estatPrevist`

**Métricas obtenidas**:
- Total de registros procesados
- Estadísticas por tramo
- Distribución por hora

---

### FASE 2: Streaming Simulado ✓
**Archivo**: `notebooks/03_smart_cities_pipeline.ipynb` - Celdas 4-5

```python
# Simula ingesta de datos en vivo
# Procesa minibatches de 5 iteraciones
# (Sin Kafka, usando RDD streaming simulado)

Output:
- df_streaming_combined (Spark DataFrame)
```

**Características**:
- Divide datos en minibatches
- Agrega timestamp de procesamiento
- Emula latencia de streaming

---

### FASE 3: Lambda Architecture ✓
**Archivo**: `notebooks/03_smart_cities_pipeline.ipynb` - Celdas 6-7

```python
# Batch Layer: histórico (λ_batch)
# Speed Layer: últimas 3600 segundos (λ_speed)
# Serving Layer: merge de ambas

Output:
- serving_layer (con rolling_avg y real_time_alert)
```

**Componentes**:
- `batch_layer`: Histórico sin límite temporal
- `speed_layer`: Ventanas móviles de 1 hora
- `serving_layer`: Vista unificada

---

### FASE 4: Clasificación MLlib ✓
**Archivo**: `notebooks/03_smart_cities_pipeline.ipynb` - Celdas 8-9

```python
# Modelo: Random Forest Classifier
# Features: [hour, idTram]
# Target: estatActual (0, 1, 2)

Metrics:
- Accuracy: ~XX%
- F1-Score: ~XX
- Precision/Recall

Output:
- classification_model (PipelineModel)
- predictions_class (Spark DataFrame)
```

---

### FASE 5: Predicción de Incidentes ✓
**Archivo**: `notebooks/03_smart_cities_pipeline.ipynb` - Celdas 10-11

```python
# Modelo: GBT Regressor
# Detecta: cambios bruscos (0→2)
# Predice: probabilidad de incidente

Output:
- incident_model (PipelineModel)
- predictions_incident (con column 'prediction')
```

**Definición de Incidente**:
- Cambio de estado: 0 → 2 en corto período
- Valor > 0.5 = incidente probable

---

### FASE 6: Alertas Automáticas ✓
**Archivo**: `notebooks/03_smart_cities_pipeline.ipynb` - Celdas 12-13

```python
# Genera alertas para:
# - estatActual > 1.5
# - Niveles: CRITICA (2), ALTA (1), MEDIA (0)

Output:
- alerts_df (Spark DataFrame)
- alerts_by_tram (Spark DataFrame)
```

**Umbrales**:
- CRITICA: estatActual == 2
- ALTA: estatActual == 1
- MEDIA: estatActual < 1.5

---

### FASE 7: Recomendaciones de Rutas ✓
**Archivo**: `notebooks/03_smart_cities_pipeline.ipynb` - Celdas 14-15

```python
# Analiza rutas menos congestionadas por hora
# Ranking: OPTIMA, ALTERNATIVA_1, ALTERNATIVA_2

Output:
- recommendations_df (Spark DataFrame)
```

**Ranking basado en**:
- Menor congestión promedio por hora
- Top 3 tramos para cada hora

---

### FASE 8: Grafana Dashboard ✓
**Archivo**: `notebooks/03_smart_cities_pipeline.ipynb` - Celdas 16-19

```python
# 1. Prepara tabla de métricas
# 2. Guarda en Parquet y CSV
# 3. Conecta a PostgreSQL
# 4. Inserta datos para Grafana

Output:
- PostgreSQL: tabla 'traffic_metrics'
- CSV: data/processed/metrics_csv/
- Parquet: data/processed/metrics_grafana/
```

---

## 🎨 Configurar Grafana

### Paso 1: Acceder a Grafana
```
URL: http://localhost:3000
Usuario: admin
Contraseña: admin
```

### Paso 2: Agregar Data Source PostgreSQL
1. Ir a: **Settings → Data Sources**
2. Click en **Add data source**
3. Seleccionar **PostgreSQL**
4. Configurar:
   - Name: `smart_cities_db`
   - Host: `localhost:5432`
   - Database: `smart_cities`
   - User: `postgres`
   - Password: `postgres`
   - SSL Mode: `disable`
5. Click **Test** y luego **Save**

### Paso 3: Crear Dashboard
1. Click en **+** → **Dashboard**
2. Click en **Add panel**
3. Seleccionar Data Source: `smart_cities_db`
4. Usar queries en `sumo_db_project/queries_grafana.sql`

### Paso 4: Paneles Sugeridos

#### Panel 1: Congestión por Hora (Line Chart)
```sql
SELECT hour, AVG(avg_congestion) as congestion
FROM traffic_metrics
GROUP BY hour
ORDER BY hour;
```

#### Panel 2: Top 10 Tramos (Bar Chart)
```sql
SELECT idTram, AVG(avg_congestion) as congestion
FROM traffic_metrics
GROUP BY idTram
ORDER BY congestion DESC
LIMIT 10;
```

#### Panel 3: Alertas Críticas (Table)
```sql
SELECT idTram, timestamp, severity
FROM alerts
WHERE severity IN ('CRITICA', 'ALTA')
ORDER BY timestamp DESC
LIMIT 25;
```

#### Panel 4: Predicciones (Gauge)
```sql
SELECT AVG(prediction) as incidentes
FROM predictions
WHERE prediction > 0.5;
```

---

## 📁 Estructura de Archivos

```
Proyecto~SmartCities/
├── notebooks/
│   ├── 01_barcelona_eda.ipynb
│   ├── 02_ml_traffic_analysis.ipynb
│   └── 03_smart_cities_pipeline.ipynb          ← ESTE
├── scripts/
│   ├── commands_linux.sh
│   └── spark_pipeline.py                       ← MÓDULO PRINCIPAL
├── data/
│   ├── raw/
│   │   ├── 2025-08.csv
│   │   ├── 2025-09.csv
│   │   └── ...
│   └── processed/
│       ├── metrics_grafana/                    ← Salida Spark
│       ├── metrics_csv/
│       ├── alerts_csv/
│       ├── predictions_csv/
│       └── route_recommendations/
├── sumo_db_project/
│   ├── docker-compose.yml
│   ├── queries_grafana.sql                     ← SQL para Grafana
│   ├── sumo_importer.py
│   └── README.md
└── env.yaml
```

---

## 🔧 Troubleshooting

### Error: "SparkSession no available"
```bash
# Asegúrate de tener Spark instalado
pip install pyspark==3.5.0
```

### Error: "No module named spark_pipeline"
```bash
# Asegúrate que estás en el directorio correcto
cd /path/to/Proyecto~SmartCities
```

### Error: "Connection refused" en PostgreSQL
```bash
# Verificar que Docker está ejecutándose
docker-compose ps

# Iniciar si no está corriendo
cd sumo_db_project
docker-compose up -d
```

### Error: "psycopg2 not found"
```bash
pip install psycopg2-binary
```

---

## 📈 Monitoreo del Pipeline

### Ver progreso en tiempo real
```bash
# Terminal 1: Monitor de Spark
watch -n 1 'docker ps | grep postgres'

# Terminal 2: Logs de Docker
docker-compose logs -f postgres
```

### Verificar datos en PostgreSQL
```bash
docker-compose exec postgres psql -U postgres -d smart_cities -c \
  "SELECT COUNT(*) FROM traffic_metrics; SELECT * FROM traffic_metrics LIMIT 10;"
```

---

## 🎯 Casos de Uso

### 1. Monitoreo en Tiempo Real
- Dashboard con congestión actual
- Alertas automáticas por correo/SMS
- Predicciones de incidentes

### 2. Análisis Histórico
- Tendencias por hora/día
- Patrones estacionales
- Identificación de cuello de botella

### 3. Optimización de Rutas
- Recomendaciones inteligentes
- Predicción de congestión futura
- Planificación urbana

---

## 📞 Soporte

Para problemas o preguntas:
1. Revisar logs: `docker-compose logs`
2. Verificar SQL: `sumo_db_project/queries_grafana.sql`
3. Consultar documentación: `docs/CODING_STANDARDS.md`

---

## 📝 Notas Importantes

- ⚠️ Data Science: Modelos son para demo. Ajustar hyperparámetros según requerimientos
- ⚠️ Producción: Implementar validación de datos, manejo de errores robusto
- ⚠️ BaseL Datos: Usar TimescaleDB para optimizar queries muy largas
- ⚠️ Escalabilidad: Distribuir Spark en clúster para datasets > 10GB

---

**Última actualización**: April 2026  
**Versión Pipeline**: 1.0 (8 Fases Completas)
