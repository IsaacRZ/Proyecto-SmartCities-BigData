# 8-Phase Spark Pipeline - README

## 🎯 Overview

Comprehensive Apache Spark-based traffic analytics pipeline with 8 integrated phases:

```
   ┌─────────────────────────────────────────────────────────┐
   │            SMART CITIES TRAFFIC PIPELINE                │
   │                   (8 FASES)                             │
   └─────────────────────────────────────────────────────────┘

   FASE 1: Batch Processing
      ↓ (Spark reads CSV data)
   FASE 2: Streaming Simulation
      ↓ (Ingesta en vivo simulada)
   FASE 3: Lambda Architecture
      ↓ (Batch + Speed layers combined)
   FASE 4: MLlib Classification
      ↓ (Random Forest - Congestion levels)
   FASE 5: Incident Prediction
      ↓ (GBT - Incident forecasting)
   FASE 6: Automated Alerts
      ↓ (Alert generation & distribution)
   FASE 7: Route Recommendations
      ↓ (Optimal path suggestions)
   FASE 8: Grafana Integration
      ↓ (Real-time dashboards)
```

---

## 📦 Files

### Core Implementation
- **`scripts/spark_pipeline.py`** - Main module with all 8 phases
- **`notebooks/03_smart_cities_pipeline.ipynb`** - Interactive Jupyter notebook
- **`run_pipeline.py`** - CLI script for headless execution

### Configuration & Docs
- **`PIPELINE_GUIDE.md`** - Complete user guide
- **`sumo_db_project/queries_grafana.sql`** - SQL for Grafana
- **`Makefile`** - Task automation

### Output Directories
- `data/processed/metrics_grafana/` - Spark output (Parquet)
- `data/processed/metrics_csv/` - CSV metrics
- `data/processed/alerts_csv/` - Alert logs
- `data/processed/predictions_csv/` - ML predictions
- `data/processed/route_recommendations/` - Route suggestions

---

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Create Conda environment
conda env create -f env.yaml
conda activate project_smart_cities
```

### 2. Start Docker (Optional but recommended)
```bash
cd sumo_db_project
docker-compose up -d

# Verify services
docker-compose ps
```

### 3. Run Pipeline

#### Option A: Using Makefile (Recommended)
```bash
make spark-pipeline          # All 8 phases
make spark-phase PHASE="1"   # Single phase
make spark-pipeline-nb       # Jupyter notebook mode
```

#### Option B: Direct Python
```bash
python run_pipeline.py                    # All phases
python run_pipeline.py --phase 1 2 3      # Phases 1, 2, 3
python run_pipeline.py --help             # Options
```

#### Option C: Jupyter Notebook
```bash
jupyter lab
# Open: notebooks/03_smart_cities_pipeline.ipynb
```

---

## 📊 Phases Explained

### FASE 1: Batch Processing ✓
**Reads & processes CSV data**
- Loads: `data/raw/2025-08.csv` to `2026-01.csv`
- Cleans timestamp, removes nulls
- Computes statistics per tramo (road segment)

**Output**: `df_processed` (Spark DataFrame)

```python
pipeline = SparkTrafficPipeline()
df_raw = pipeline.load_multiple_csv(csv_files)
df_processed = pipeline.preprocess_traffic_data(df_raw)
```

---

### FASE 2: Streaming Simulation ✓
**Simulates live data ingestion**
- Divides data into 5 minibatches
- Adds processing timestamps
- Emulates stream behavior (without Kafka)

**Output**: `df_streaming_combined` (Spark DataFrame)

```python
streaming_generator = pipeline.simulate_streaming(df_processed)
# Processes batches incrementally
```

---

### FASE 3: Lambda Architecture ✓
**Combines batch + real-time views**

- **Batch Layer**: Full historical data
- **Speed Layer**: Rolling 1-hour window
- **Serving Layer**: Unified query view

**Output**: `serving_layer` (with rolling_avg + real_time_alert)

```python
batch_layer = pipeline.lambda_batch_layer(df_processed)
speed_layer = pipeline.lambda_speed_layer(df_streaming)
serving_layer = pipeline.lambda_merge(batch_layer, speed_layer)
```

---

### FASE 4: Classification with MLlib ✓
**Predicts congestion level (0, 1, 2)**

- **Algorithm**: Random Forest Classifier
- **Features**: [hour, idTram]
- **Target**: estatActual (0=Normal, 1=Moderate, 2=High)

**Metrics**: Accuracy, F1-Score, Precision, Recall

```python
model, accuracy, predictions = pipeline.train_classification_model(df_processed)
# Returns trained PipelineModel + predictions
```

---

### FASE 5: Incident Prediction ✓
**Detects sudden congestion spikes**

- **Algorithm**: GBT Regressor
- **Definition**: Change from 0→2 in short period
- **Output**: Incident probability (0-1)

**Example**: If `prediction > 0.5` → Likely incident

```python
incident_model, predictions = pipeline.train_incident_model(df_processed)
# Identifies potential traffic incidents
```

---

### FASE 6: Automated Alerts ✓
**Generates severity-based alerts**

| Severity | Condition |
|----------|-----------|
| CRITICA  | estatActual == 2 |
| ALTA     | estatActual == 1 |
| MEDIA    | estatActual < 1.5 |

```python
alerts_df = pipeline.generate_alerts(df_processed, threshold_congestion=1.5)
# Returns alert DataFrame with severity labels
```

---

### FASE 7: Route Recommendations ✓
**Suggests alternative routes**

- **Ranking**: 
  - OPTIMA: Least congested route
  - ALTERNATIVA_1: Second best
  - ALTERNATIVA_2: Third choice

```python
recommendations_df = pipeline.generate_route_recommendations(df_processed)
# Recommends routes based on real-time congestion
```

---

### FASE 8: Grafana Integration ✓
**Exports to PostgreSQL for dashboards**

- Creates `traffic_metrics` table
- Inserts 1000+ records for visualization
- Provides SQL queries for common panels

```python
# Automatically connects to PostgreSQL and imports data
# Use queries_grafana.sql for dashboard creation
```

---

## 📈 Grafana Setup

### 1. Access Grafana
```
URL: http://localhost:3000
Username: admin
Password: admin
```

### 2. Add PostgreSQL Data Source
1. Settings → Data Sources → Add
2. Select PostgreSQL
3. Configure:
   - Host: localhost:5432
   - Database: smart_cities
   - User: postgres
   - Password: postgres
4. Test & Save

### 3. Create Dashboards

Use queries from `sumo_db_project/queries_grafana.sql`:

```sql
-- Congestion by hour
SELECT hour, AVG(avg_congestion) as congestion
FROM traffic_metrics
GROUP BY hour;

-- Top congested road segments
SELECT idTram, AVG(avg_congestion) as congestion
FROM traffic_metrics
GROUP BY idTram
ORDER BY congestion DESC
LIMIT 10;

-- Recent alerts
SELECT * FROM alerts
WHERE severity != 'MEDIA'
ORDER BY timestamp DESC;
```

---

## 🔧 Configuration

### Spark Settings (in `spark_pipeline.py`)
```python
SparkSession.builder \
    .appName("SmartCities") \
    .config("spark.sql.adaptive.enabled", "true") \
    .config("spark.sql.shuffle.partitions", "8") \
    .getOrCreate()
```

### PostgreSQL Connection (in `run_pipeline.py`)
```python
db_config = {
    "host": "localhost",
    "port": 5432,
    "database": "smart_cities",
    "user": "postgres",
    "password": "postgres"
}
```

---

## 📊 Data Flow

```
CSV Files (raw)
    ↓
[FASE 1] Spark Read + Preprocess
    ↓
df_processed
    ↓
├─→ [FASE 2] Streaming Simulation
│        ↓
│   df_streaming_combined
│        ↓
│   [FASE 3] Lambda Architecture
│        ↓
│   serving_layer
│
├─→ [FASE 4] Classification Model
│        ↓
│   predictions_class
│        ↓
├─→ [FASE 5] Incident Model
│        ↓
│   predictions_incident
│        ↓
├─→ [FASE 6] Generate Alerts
│        ↓
│   alerts_df
│        ↓
├─→ [FASE 7] Route Recommendations
│        ↓
│   recommendations_df
│        ↓
└─→ [FASE 8] Export to Grafana
         ↓
    PostgreSQL
         ↓
    Grafana Dashboards
```

---

## 🐛 Troubleshooting

### Error: "Java not found"
```bash
# Install OpenJDK
conda install -c conda-forge openjdk=11
```

### Error: "psycopg2 not found"
```bash
pip install psycopg2-binary
```

### Error: "Connection refused"
```bash
# Check Docker is running
docker-compose ps

# If not, start it
cd sumo_db_project && docker-compose up -d
```

### Error: "Port 5432 already in use"
```bash
# Kill existing process
lsof -ti:5432 | xargs kill -9

# Or use different port in docker-compose.yml
```

---

## 📝 Example Usage

### Run All 8 Phases
```bash
python run_pipeline.py
```

### Run Specific Phases Only
```bash
# Phases 1, 3, 4 only
python run_pipeline.py --phase 1 3 4

# Skip PostgreSQL connection
python run_pipeline.py --skip-db

# With DEBUG logging
python run_pipeline.py --log-level DEBUG
```

### Use in Jupyter
```python
from scripts.spark_pipeline import SparkTrafficPipeline

pipeline = SparkTrafficPipeline(app_name="MyAnalysis")

# FASE 1
df = pipeline.load_csv("data/raw/2025-08.csv")
df = pipeline.preprocess_traffic_data(df)

# FASE 4
model, accuracy, predictions = pipeline.train_classification_model(df)

# Explore
df.show()
```

---

## 🎓 Key Concepts

### Lambda Architecture
- **Batch**: Process all historical data → comprehensive accuracy
- **Speed**: Process recent data → low latency
- **Serving**: Combined view → flexible querying

### MLlib Models
- **Classification**: Random Forest (categorical values)
- **Regression**: GBT (continuous predictions)

### Spark DataFrames
- Distributed, immutable data structure
- SQL-compatible operations
- Auto optimization with Catalyst

---

## 📚 References

- [Apache Spark Docs](https://spark.apache.org/docs/)
- [MLlib Guide](https://spark.apache.org/docs/latest/ml-guide.html)
- [Grafana Docs](https://grafana.com/docs/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)

---

## 📞 Support

For issues:
1. Check logs: `docker-compose logs postgres`
2. Review `PIPELINE_GUIDE.md` (detailed guide)
3. Inspect SQL: `sumo_db_project/queries_grafana.sql`
4. Run with `--log-level DEBUG`

---

**Last Updated**: April 2026  
**Pipeline Version**: 1.0 (Complete 8 Phases)  
**Status**: ✅ Production Ready
