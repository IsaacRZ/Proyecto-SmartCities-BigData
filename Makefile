# Smart Cities Project - Makefile
# Workflow orchestration for simulation, data import, and analysis

#========================================================================
# SETUP:
# POWERSHELL: wsl --install -d Ubuntu

# Docker Desktop → Settings (engranaje ⚙️) → Resources → WSL Integration
# ☑ Enable integration with my default WSL distro
#Additional distros:
#☑ Ubuntu   ← Activa esta (o la que uses)


# Open UBUNTU 
# 1. Ve a tu home de Linux
# 	cd ~
# 2. Descarga el instalador
# 	wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
# 3. Ejecuta el instalador
# 	bash Miniconda3-latest-Linux-x86_64.sh
# 4. Recarga el shell para activar conda
#	source ~/.bashrc

# 5. Verifica que funciona
#	conda --version
# 6. Luego vuelves a tu proyecto (que SÍ puede estar en /mnt/c/)
#	cd "/mnt/c/Users/LENOVO/Documents/Big Data/BigData/Proyecto~SmartCities"
# 7. Y corres el make normalmente
#		make setup
#		conda activate project_smart_cities
#		make docker-all
#		make simulation
#		make import RUN_NAME=nombre_simulacion
#		make analysis
#========================================================================
#
.PHONY: help setup simulation import analysis docker-all docker-down clean

# Default target
help:
	@echo "Smart Cities Traffic Analysis Project"
	@echo "======================================"
	@echo ""
	@echo "Available targets:"
	@echo "  setup        - Create and activate conda environment"
	@echo "  simulation   - Run SUMO simulation"
	@echo "  import       - Import SUMO XML data to PostgreSQL"
	@echo "  analysis     - Start Jupyter for PySpark analysis"
	@echo "  pipeline     - Full 8-phase Spark pipeline"
	@echo "  pipeline-nb  - 8-phase pipeline in Jupyter notebook"
	@echo "  docker-all   - Start all Docker services (DB, Grafana, pgAdmin)"
	@echo "  docker-down  - Stop all Docker services"
	@echo "  clean        - Clean Python cache and build artifacts"
	@echo ""
	@echo "Usage:"
	@echo "  make setup"
	@echo "  make docker-all"
	@echo "  make simulation"
	@echo "  make import RUN_NAME=my_simulation"
	@echo "  make pipeline            # Run 8-phase Spark pipeline"
	@echo "  make pipeline-nb         # Run pipeline in Jupyter"
	@echo ""

# Setup conda environment
setup:
	@echo "Creating conda environment..."
	conda env create -f env.yaml
	@echo "Environment created. Activate with: conda activate project_smart_cities"

# Start Docker services
docker-all:
	@echo "Starting Docker services (PostgreSQL, Grafana, pgAdmin)..."
	cd sumo_db_project && docker-compose up -d
	@echo ""
	@echo "Services started:"
	@echo "  - PostgreSQL/TimescaleDB: localhost:5432 (postgres/sumo123)"
	@echo "  - pgAdmin: http://localhost:5050 (admin@sumo.com/admin123)"
	@echo "  - Grafana: http://localhost:3000 (admin/admin123)"

# Stop Docker services
docker-down:
	@echo "Stopping Docker services..."
	cd sumo_db_project && docker-compose down

# Run SUMO simulation
simulation:
	@echo "Running SUMO simulation..."
	cd Simulacion && ./run.bat
	@echo ""
	@echo "Simulation complete. Output XML files are in Simulacion/"
	@echo "Run 'make import' to import data to PostgreSQL"

# Import SUMO data to PostgreSQL
# Usage: make import RUN_NAME=my_simulation
import:
ifndef RUN_NAME
	$(error RUN_NAME is required. Usage: make import RUN_NAME=simulation_name)
endif
	@echo "Importing SUMO data to PostgreSQL..."
	@echo "Run name: $(RUN_NAME)"
	pip install psycopg2-binary --quiet
	cd sumo_db_project && python sumo_importer.py --dir "../Simulacion" --run-name "$(RUN_NAME)"
	@echo ""
	@echo "Import complete! Connect to pgAdmin at http://localhost:5050"

# Start Jupyter for analysis
analysis:
	@echo "Starting Jupyter for PySpark analysis..."
	conda activate project_smart_cities && jupyter lab --notebook-dir=notebooks

# Install Python dependencies
install-deps:
	@echo "Installing Python dependencies..."
	pip install -r sumo_db_project/requirements.txt

# Run tests
test:
	@echo "Running tests..."
	python tests/test_simple.py

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name ".ipynb_checkpoints" -exec rm -rf {} + 2>/dev/null || true
	@echo "Clean complete"

# Full pipeline: simulation -> import -> (optional) analysis
pipeline: docker-all simulation
	@echo ""
	@echo "Simulation complete. Run 'make import RUN_NAME=your_name' to import data"

# 8-Phase Spark Pipeline (batch + streaming + ML + alerts + recommendations)
spark-pipeline:
	@echo "=========================================="
	@echo "  Smart Cities 8-Phase Spark Pipeline"
	@echo "=========================================="
	@echo ""
	@echo "FASE 1: Batch Processing"
	@echo "FASE 2: Streaming Simulado"
	@echo "FASE 3: Arquitectura Lambda"
	@echo "FASE 4: Clasificación MLlib"
	@echo "FASE 5: Predicción de Incidentes"
	@echo "FASE 6: Alertas Automáticas"
	@echo "FASE 7: Recomendaciones de Rutas"
	@echo "FASE 8: Grafana Dashboard"
	@echo ""
	python run_pipeline.py

# Run 8-phase pipeline with specific phases
spark-phase:
ifdef PHASE
	python run_pipeline.py --phase $(PHASE)
else
	@echo "Usage: make spark-phase PHASE='1 2 3' (run phases 1, 2, 3)"
endif

# Run 8-phase pipeline in Jupyter notebook
spark-pipeline-nb:
	@echo "Starting Jupyter with 8-phase Spark pipeline..."
	@echo "Open: notebooks/03_smart_cities_pipeline.ipynb"
	conda activate project_smart_cities && jupyter lab --notebook-dir=notebooks --ip=localhost --port=8888

# View Grafana dashboard
grafana:
	@echo "Opening Grafana dashboard..."
	@echo "URL: http://localhost:3000"
	@echo "Username: admin"
	@echo "Password: admin"
ifdef OS
	start http://localhost:3000
else
	open http://localhost:3000 || xdg-open http://localhost:3000 2>/dev/null || echo "Visit http://localhost:3000"
endif

# View pgAdmin
pgadmin:
	@echo "Opening pgAdmin..."
	@echo "URL: http://localhost:5050"
	@echo "Username: admin@sumo.com"
	@echo "Password: admin123"
ifdef OS
	start http://localhost:5050
else
	open http://localhost:5050 || xdg-open http://localhost:5050 2>/dev/null || echo "Visit http://localhost:5050"
endif
