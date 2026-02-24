import os
import sys

# Decirle a Spark que use el Python de este entorno virtual
os.environ['PYSPARK_PYTHON'] = sys.executable
os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable

print(f"Python que vamos a usar: {sys.executable}")

from pyspark.sql import SparkSession

# Crear sesión Spark
spark = SparkSession.builder \
    .appName("TestSparkFixed") \
    .master("local[1]") \
    .config("spark.sql.execution.arrow.pyspark.enabled", "false") \
    .getOrCreate()

# Crear DataFrame de prueba
data = [("Sensor_001", 100), ("Sensor_002", 150), ("Sensor_003", 80)]
columns = ["sensor_id", "num_vehiculos"]

df = spark.createDataFrame(data, columns)

# Mostrar
print("✅ Spark funcionando correctamente!")
df.show()

# Detener Spark
spark.stop()