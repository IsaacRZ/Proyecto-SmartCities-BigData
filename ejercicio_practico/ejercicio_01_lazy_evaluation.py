"""
Ejercicio: Comprendiendo Lazy evaluation
Objetivo: Observar cuando Spark ejecuta el código
"""
import os
import sys

# Configuracion para Windows
os.environ['PYSPARK_PYTHON'] = sys.executable
os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable

from pyspark.sql import SparkSession
from pyspark.sql.functions import col

#Crear sesión Spark
print("=" * 60)
print("PASO 1: Creando sesión Spark...")
print("=" * 60)

spark = SparkSession.builder \
    .appName("Ejercicio_LazyEvaluation") \
    .master("local[*]") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")  # Silenciar logs para ver mejor
print("✅ Sesión creada\n")

# Crear datos de ejemplo: sensores de tráfico
print("=" * 60)
print("PASO 2: Creando DataFrame con datos de sensores...")
print("=" * 60)

data = [
    ("SENSOR_001", "2026-01-28 08:00", 45, 65),
    ("SENSOR_001", "2026-01-28 08:10", 78, 55),
    ("SENSOR_001", "2026-01-28 08:20", 120, 35),
    ("SENSOR_002", "2026-01-28 08:00", 30, 70),
    ("SENSOR_002", "2026-01-28 08:10", 50, 60),
    ("SENSOR_002", "2026-01-28 08:20", 95, 40),
    ("SENSOR_003", "2026-01-28 08:00", 60, 55),
    ("SENSOR_003", "2026-01-28 08:10", 110, 30),
    ("SENSOR_003", "2026-01-28 08:20", 140, 25),
]

columns = ["sensor_id", "timestamp", "num_vehiculos", "velocidad_kmh"]

df_original = spark.createDataFrame(data, columns)
print("✅ DataFrame creado (pero Spark NO ha procesado los datos todavía)")
print(f"   Tipo de objeto: {type(df_original)}")
print()

# TRANSFORMACIÓN 1: Filtrar solo alta congestión
print("=" * 60)
print("PASO 3: TRANSFORMACIÓN - Filtrar vehículos > 80...")
print("=" * 60)

df_congestion = df_original.filter(col("num_vehiculos") > 80)
print("✅ Filtro aplicado (SOLO ANOTADO, no ejecutado)")
print(f"   Tipo de objeto: {type(df_congestion)}")
print("   ⚠️  Spark todavía NO ha leído ni una sola fila de datos")
print()

# TRANSFORMACIÓN 2: Seleccionar solo algunas columnas
print("=" * 60)
print("PASO 4: TRANSFORMACIÓN - Seleccionar columnas específicas...")
print("=" * 60)

df_seleccionado = df_congestion.select("sensor_id", "num_vehiculos")
print("✅ Selección aplicada (SOLO ANOTADA, no ejecutada)")
print("   ⚠️  Spark sigue sin haber procesado nada")
print()

# Aquí viene lo importante: ¿Cuándo se ejecuta?
print("=" * 60)
print("PASO 5: ACCIÓN - Ahora SÍ pedimos un resultado...")
print("=" * 60)
print("Ejecutando df_seleccionado.show()...")
print()

df_seleccionado.show()

print()
print("👆 ¡RECIÉN AHORA Spark ejecutó TODOS los pasos!")
print("   1. Leyó los datos originales")
print("   2. Aplicó el filtro (num_vehiculos > 80)")
print("   3. Seleccionó las columnas")
print("   4. Mostró el resultado")
print()

# Demostración adicional
print("=" * 60)
print("EXTRA: Ejecutando otra acción sobre el MISMO DataFrame...")
print("=" * 60)

cantidad = df_seleccionado.count()
print(f"✅ Número de filas con alta congestión: {cantidad}")
print()
print("   Nota: Spark tuvo que VOLVER a ejecutar todo el plan")
print("   porque no guardó los resultados intermedios")
print()

# Cerrar sesión
spark.stop()
print("=" * 60)
print("🎓 Fin del ejercicio")
print("=" * 60)