Aquí tienes la traducción al español del contexto del proyecto GEMINI:

---

# Contexto del Proyecto GEMINI: Simulación y Análisis de Tráfico en Ciudades Inteligentes

## 1. Resumen del Proyecto

Este es un proyecto de ingeniería de datos y simulación enfocado en el análisis de tráfico urbano ("Smart Cities"). El objetivo principal es simular patrones de tráfico, procesar los datos resultantes y analizarlos para obtener información valiosa. El proyecto integra varias tecnologías para lograr esto:

* **Simulación de Tráfico:** Utiliza **SUMO (Simulation of Urban MObility)** para modelar y simular el tráfico de vehículos. Las simulaciones están configuradas para la ciudad de San José, Costa Rica, pero están calibradas utilizando patrones de datos reales de Barcelona.
* **Backend de Datos:** Una infraestructura de datos robusta construida con **Docker** que incluye:
    * **PostgreSQL con TimescaleDB:** Una base de datos de series temporales optimizada para almacenar los resultados de la simulación, como viajes de vehículos, datos de tramos (edges) y estadísticas.
    * **Grafana:** Para la visualización de los datos de series temporales desde la base de datos.
    * **pgAdmin:** Una herramienta de administración web para la base de datos PostgreSQL.
* **Procesamiento y Análisis de Datos:**
    * **Python:** Se utiliza un script de Python personalizado (`sumo_importer.py`) para analizar la salida XML de SUMO y cargarla en la base de datos TimescaleDB.
    * **PySpark y Jupyter Notebooks:** El proyecto está preparado para el análisis de datos a gran escala utilizando PySpark, como se observa en el entorno Conda (`env.yaml`) y los cuadernos de análisis (`.ipynb`). La arquitectura sugiere una capa de procesamiento por lotes (batch layer) para datos históricos de Barcelona y una capa de velocidad (speed layer) para procesar datos simulados en tiempo real de San José.

## 2. Componentes Clave y Flujos de Trabajo

El proyecto se divide en componentes distintos, cada uno con su propio flujo de trabajo.

### Componente 1: Simulación de Tráfico SUMO

Este componente es responsable de generar los datos de tráfico en bruto.

* **Ubicación:** Directorio `Simulacion/`.
* **Configuración:** Utiliza archivos `.netccfg`, `.polycfg` y `.sumocfg` para definir la red de carreteras y los parámetros de simulación.
* **Cómo ejecutarlo:**
    * Ejecuta el script `run.bat` o `build_con_barcelona.bat` en el directorio `Simulacion/`.
    * Esto iniciará la interfaz gráfica (GUI) de SUMO y ejecutará la simulación definida en `osm.sumocfg`.
    * La simulación genera archivos de salida XML (por ejemplo, `tripinfos.xml`, `edgeData.xml`) que contienen los resultados.

```bash
# Navega al directorio de simulación y ejecuta la simulación
cd Simulacion
./run.bat
```

### Componente 2: Backend de Almacenamiento y Visualización

Este componente proporciona la infraestructura necesaria para almacenar y visualizar los datos.

* **Ubicación:** Directorio `sumo_db_project/`.
* **Tecnología:** Docker, Docker Compose, PostgreSQL/TimescaleDB, Grafana.
* **Cómo ejecutarlo:**
    1. Asegúrate de que Docker Desktop esté funcionando.
    2. Navega al directorio `sumo_db_project`.
    3. Inicia todos los servicios (Base de datos, Grafana, pgAdmin) usando Docker Compose.

    ```bash
    # Navega al directorio del proyecto de base de datos
    cd sumo_db_project

    # Inicia todos los servicios en modo segundo plano (detached)
    docker-compose up -d
    ```
* **Puntos de Acceso:**
    * **Base de datos PostgreSQL:** `localhost:5432` (Usuario: `postgres`, Contraseña: `sumo123`)
    * **Grafana:** `http://localhost:3000` (Usuario: `admin`, Contraseña: `admin123`)
    * **pgAdmin:** `http://localhost:5050` (Usuario: `admin@sumo.com`, Contraseña: `admin123`)

* **Para detener los servicios:**
    ```bash
    # Detiene los servicios y elimina los contenedores
    docker-compose down
    ```

### Componente 3: Importación de Datos (de SUMO a la Base de Datos)

Este flujo de trabajo conecta la salida de la simulación con el backend de datos.

* **Ubicación:** Directorio `sumo_db_project/`.
* **Script:** `sumo_importer.py`.
* **Cómo ejecutarlo:**
    1. Una vez finalizada la simulación en SUMO, ejecuta el script `sumo_importer.py`.
    2. Debes proporcionar la ruta al directorio que contiene los archivos XML de salida de SUMO y un nombre descriptivo para la ejecución de la simulación.

    ```bash
    # Ejemplo de ejecución del importador desde el directorio sumo_db_project
    python sumo_importer.py \
      --dir "C:\ruta\hacia\tus\archivos\xml\de\salida\sumo" \
      --run-name "Nombre_De_La_Simulacion"
    ```

### Componente 4: Análisis de Datos

Este componente sirve para explorar los datos procesados y encontrar hallazgos relevantes.

* **Ubicación:** Directorio `notebooks/`.
* **Entorno:** El proyecto utiliza un entorno Conda definido en `env.yaml`. Para configurarlo:
    ```bash
    conda env create -f env.yaml
    conda activate project_smart_cities
    ```
* **Herramientas:** Jupyter Notebooks (`.ipynb`) y PySpark.
* **Flujo de trabajo:**
    1. Activa el entorno Conda.
    2. Inicia Jupyter Lab o Jupyter Notebook.
    3. Abre y ejecuta los cuadernos en el directorio `notebooks/` (ej. `01_barcelona_eda.ipynb`) para realizar el análisis exploratorio de datos.

## 3. Convenciones de Desarrollo

* **Estándares de Codificación:** El proyecto sigue **PEP 8** y las convenciones internas documentadas en `docs/CODING_STANDARDS.md`.
    * **Nomenclatura:** `snake_case` para variables/funciones, `PascalCase` para clases, y el sufijo `_df` para Spark DataFrames.
    * **Commits:** Siguen el formato `<tipo>: <descripción>` (ej. `feat: Add new analysis notebook`).
* **Dependencias de Python:**
    * Las dependencias del script de importación de datos se encuentran en `sumo_db_project/requirements.txt`.
    * Las dependencias del entorno de análisis están en `env.yaml`.

---