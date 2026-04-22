# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Smart Cities traffic simulation and analysis project (Big Data). Simulates urban traffic patterns using SUMO for San José, Costa Rica, calibrated with real data from Barcelona. Processes simulation output using PySpark and stores time-series data in PostgreSQL/TimescaleDB for visualization in Grafana.

## Architecture

```
┌─────────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│  SUMO Simulation    │────▶│  sumo_importer.py    │────▶│  PostgreSQL/        │
│  (San José, CR)     │ XML │  (Python parser)     │ CSV │  TimescaleDB        │
│  Calibrated with    │     │                      │     │  (Docker)           │
│  Barcelona patterns │     │                      │     └──────────┬──────────┘
└─────────────────────┘     └──────────────────────┘                │
                                                                    ├────▶ pgAdmin (5050)
┌─────────────────────┐     ┌──────────────────────┐                ├────▶ Grafana (3000)
│  Barcelona Open     │────▶│  PySpark Batch       │                └────▶ SQL Queries
│  Data (Historical)  │     │  Processing/ML       │
└─────────────────────┘     └──────────────────────┘
```

## Key Directories

- `sumo_db_project/` - Docker infrastructure (PostgreSQL+TimescaleDB, pgAdmin, Grafana) and XML importer
- `Simulacion/` - SUMO simulation configuration files (`.sumocfg`, `.netccfg`)
- `notebooks/` - Jupyter notebooks for PySpark analysis
- `data/` - Raw and processed data (excluded from git, see `data/README.md`)
- `tests/` - Unit tests (run with `make test`)
- `docs/` - Project documentation
- `scripts/` - Utility scripts
- `entregables/` - Academic deliverables

## Commands

### Using Makefile (Recommended)

```bash
make setup              # Create conda environment
make docker-all         # Start all Docker services
make simulation         # Run SUMO simulation
make import RUN_NAME=x  # Import XML data to PostgreSQL
make analysis           # Start Jupyter Lab for PySpark
make spark-pipeline     # Run 8-phase Spark pipeline (all phases)
make spark-phase PHASE="1 2 3"  # Run specific phases
make spark-pipeline-nb  # 8-phase pipeline in Jupyter notebook
make test               # Run unit tests
make clean              # Clean build artifacts
make pipeline           # Full pipeline: simulate + import
```

### Manual Commands

```bash
# Create Conda environment for analysis
conda env create -f env.yaml
conda activate project_smart_cities

# Start infrastructure (Docker)
cd sumo_db_project && docker-compose up -d

# Run SUMO simulation
cd Simulacion && ./run.bat

# Import simulation data
cd sumo_db_project
pip install psycopg2-binary
python sumo_importer.py --dir "path/to/xml/output" --run-name "Simulation_Name"

# Run PySpark analysis
conda activate project_smart_cities && jupyter lab

# Run 8-Phase Spark Pipeline (headless)
python run_pipeline.py                    # All phases
python run_pipeline.py --phase 1 2 3      # Specific phases
python run_pipeline.py --skip-db          # Skip PostgreSQL connection
```

## Database Schema

Time-series tables (TimescaleDB hypertables):
- `vehicle_trips` - Completed vehicle journeys (from `tripinfos.xml`)
- `edge_data` - Street-level metrics (from `edgeData.xml`)
- `simulation_stats` - Global simulation statistics (from `stats.xml`)
- `pt_stops` - Public transport stop data (from `stopinfos.xml`)
- `traffic_metrics` - Spark pipeline output for Grafana

## 8-Phase Spark Pipeline

The project includes a comprehensive Spark pipeline (`run_pipeline.py`, `scripts/spark_pipeline.py`) with 8 phases:

| Phase | Description | Output |
|-------|-------------|--------|
| 1 | Batch Processing | `df_processed` (cleaned DataFrame) |
| 2 | Streaming Simulation | `df_streaming_combined` |
| 3 | Lambda Architecture | `serving_layer` (batch + speed) |
| 4 | MLlib Classification | Random Forest model (congestion levels 0,1,2) |
| 5 | Incident Prediction | GBT model (incident probability) |
| 6 | Automated Alerts | `alerts_df` (CRITICA/ALTA/MEDIA) |
| 7 | Route Recommendations | `recommendations_df` (OPTIMA, ALTERNATIVA) |
| 8 | Grafana Integration | PostgreSQL `traffic_metrics` table |

### Running the Pipeline on Ubuntu

```bash
# 1. Setup environment
make setup
conda activate project_smart_cities

# 2. Start Docker (optional, for Grafana)
make docker-all

# 3. Run pipeline
make spark-pipeline           # All 8 phases via Makefile
# OR
python run_pipeline.py        # All 8 phases directly
python run_pipeline.py --phase 1 4 5  # Specific phases
```

### Pipeline Files
- `run_pipeline.py` - CLI script for headless execution
- `scripts/spark_pipeline.py` - Main module with all 8 phases
- `notebooks/03_smart_cities_pipeline.ipynb` - Interactive Jupyter notebook
- `PIPELINE_README.md` - Complete user guide
- `PIPELINE_GUIDE.md` - Detailed phase documentation
- `sumo_db_project/queries_grafana.sql` - SQL queries for Grafana dashboards

### Output Directories
- `data/processed/metrics_grafana/` - Spark output (Parquet)
- `data/processed/metrics_csv/` - CSV metrics
- `data/processed/alerts_csv/` - Alert logs
- `data/processed/predictions_csv/` - ML predictions
- `data/processed/route_recommendations/` - Route suggestions

## Coding Standards

- Follow PEP 8 and conventions in `docs/CODING_STANDARDS.md`
- Naming: `snake_case` for variables/functions, `PascalCase` for classes
- Spark DataFrames: suffix with `_df` (e.g., `trafico_df`)
- Docstrings required for all functions (see `docs/CODING_STANDARDS.md`)
- Git commits: `<type>: <description>` (feat, fix, docs, refactor)

## Important Files

- `sumo_db_project/sumo_importer.py` - Main XML parser and database importer
- `sumo_db_project/docker-compose.yml` - Infrastructure definition
- `env.yaml` - Conda environment for PySpark analysis
- `run_pipeline.py` - 8-phase Spark pipeline CLI
- `scripts/spark_pipeline.py` - Spark pipeline module
- `docs/CODING_STANDARDS.md` - Internal coding conventions
- `docs/DescripcionProyecto.md` - Full project context (Spanish)
- `PIPELINE_README.md` - Pipeline quick start guide
- `PIPELINE_GUIDE.md` - Detailed pipeline documentation
