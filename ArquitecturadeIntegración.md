## 🏗️ Arquitectura de Integración

### **Batch Layer → Barcelona Open Data (Datos Históricos Reales)**
URL del dataset: https://opendata-ajuntament.barcelona.cat/data/es/dataset/trams
Fecha de descarga: 18 de Febrero 2026
Tamaño: 264M

```
Barcelona Sensors (Real)
    ↓
6 meses de datos históricos
    ↓
PySpark Batch Processing
    ↓
Genera:
- Baselines estadísticos (promedio vehículos por hora/día)
- Patrones de congestión (distribuciones reales)
- Modelos ML entrenados con datos REALES
- Vistas materializadas en BigQuery
```

### **Speed Layer → SUMO San José (Simulación Calibrada)**

```
SUMO Simulator (San José, CR)
    ↓
Calibrado con patrones de Barcelona
    ↓
Genera eventos streaming cada 10 seg
    ↓
PySpark Streaming consume eventos
    ↓
Aplica modelos entrenados con Barcelona
    ↓
Predicciones en tiempo real → BigQuery
```

# SPARK
### /notebooks/03_smart_cities_pipeline

Instancia un nuevo objeto (crea objeto de una clase) de la clase SparkTrafficPipeline
Atributo de la sesión actual de spark pipeline.spark almacenada en variable spark.

# Fase 1: Inicializar pipeline Spark
Instaciar objeto de la clase
Definir atributo-propiedad .spark ->Sesion
```
pipeline = SparkTrafficPipeline(app_name="SmartCities_Pipeline")  #Instaciar objeto de la clase
spark = pipeline.spark                                            #Definir atributo-propiedad .spark ->Sesion
```

Filtro archivos csv en Python. Recorre los archivos si "Tramos" no esta contenida en el archivo csv. (List comprehension)
```
csv_files = [f for f in csv_files if "Tramos" not in f]
```

Carga y Preprocesamiento
```
df_raw = pipeline.load_multiple_csv(csv_files) # Carga y combinación de CSVs en un DataFrame de Spark

# Preprocesar datos
df_processed = pipeline.preprocess_traffic_data(df_raw) # Limpieza, transformación  de datos
```

# Fase 2: Simular ingesta de datos en tiempo real
print("🔄 FASE 2: Iniciando simulación de streaming...\n")

# Crear generador de batches
streaming_generator = pipeline.simulate_streaming(df_processed, batch_interval_ms=1000)


```
```