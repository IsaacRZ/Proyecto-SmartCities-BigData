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
```

## Database Schema

Time-series tables (TimescaleDB hypertables):
- `vehicle_trips` - Completed vehicle journeys (from `tripinfos.xml`)
- `edge_data` - Street-level metrics (from `edgeData.xml`)
- `simulation_stats` - Global simulation statistics (from `stats.xml`)
- `pt_stops` - Public transport stop data (from `stopinfos.xml`)

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
- `docs/CODING_STANDARDS.md` - Internal coding conventions
- `docs/DescripcionProyecto.md` - Full project context (Spanish)
