# Proyecto Ciudad Inteligente - Big Data

Simulación y análisis de tráfico urbano para San José, Costa Rica, calibrado con datos reales de Barcelona.

## Tecnologías

| Tecnología | Propósito |
|------------|-----------|
| **SUMO** | Simulación de tráfico urbano |
| **PySpark** | Procesamiento distribuido de datos |
| **PostgreSQL + TimescaleDB** | Base de datos time-series |
| **Grafana** | Visualización de métricas |
| **Docker** | Infraestructura de servicios |

## Inicio Rápido

```bash
# 1. Crear entorno Conda
conda env create -f env.yaml
conda activate project_smart_cities

# 2. Iniciar servicios Docker (DB, Grafana, pgAdmin)
make docker-all

# 3. Ejecutar simulación SUMO
make simulation

# 4. Importar datos a PostgreSQL
make import RUN_NAME=mi_simulacion

# 5. Análisis con Jupyter + PySpark
make analysis
```

## Estructura del Proyecto

```
.
├── Simulacion/          # Configuración y ejecución SUMO
├── sumo_db_project/     # Infraestructura Docker + importador
├── notebooks/           # Análisis PySpark (Jupyter)
├── data/                # Datos (excluidos de git)
│   ├── raw/             # Datos crudos (Barcelona, SUMO XML)
│   └── processed/       # Datos procesados (Parquet)
├── docs/                # Documentación
├── tests/               # Tests unitarios
├── scripts/             # Scripts utilitarios
└── entregables/         # Archivos de entrega académica
```

## Comandos Make

| Comando | Descripción |
|---------|-------------|
| `make setup` | Crear entorno Conda |
| `make docker-all` | Iniciar PostgreSQL, Grafana, pgAdmin |
| `make docker-down` | Detener servicios Docker |
| `make simulation` | Ejecutar simulación SUMO |
| `make import RUN_NAME=nombre` | Importar XML a PostgreSQL |
| `make analysis` | Iniciar Jupyter Lab |
| `make test` | Ejecutar tests |
| `make clean` | Limpiar archivos temporales |
| `make pipeline` | Ejecutar simulación + importar |

## Servicios

| Servicio | URL/Puerto | Credenciales |
|----------|------------|--------------|
| PostgreSQL | `localhost:5432` | postgres / sumo123 |
| pgAdmin | http://localhost:5050 | admin@sumo.com / admin123 |
| Grafana | http://localhost:3000 | admin / admin123 |

## Documentación Adicional

- [Arquitectura de Integración](ArquitecturadeIntegración.md)
- [Estándares de Código](docs/CODING_STANDARDS.md)
- [Descripción del Proyecto](docs/DescripcionProyecto.md)
- [Guía SUMO Database](sumo_db_project/README.md)

## Estándares de Código

Este proyecto sigue [PEP 8](https://pep8.org/) y [convenciones internas](docs/CODING_STANDARDS.md).

**Antes de hacer commit:**
- Revisar naming conventions
- Agregar docstrings a funciones nuevas
- Comentar decisiones de diseño no obvias
