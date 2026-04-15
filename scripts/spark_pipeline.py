"""
Smart Cities Traffic Pipeline - Módulos Spark compartidos
Contiene utilidades para procesamiento batch, streaming y ML
"""

from pyspark.sql import SparkSession, DataFrame, Window
from pyspark.sql.functions import col, when, to_timestamp, avg as spark_avg, stddev as spark_stddev, row_number, max as spark_max, min as spark_min, count as spark_count, lit, lag
from pyspark.ml import Pipeline, PipelineModel
from pyspark.ml.feature import VectorAssembler, StandardScaler, StringIndexer
from pyspark.ml.classification import RandomForestClassifier, LogisticRegression
from pyspark.ml.regression import GBTRegressor
from pyspark.ml.evaluation import MulticlassClassificationEvaluator, RegressionEvaluator
import pandas as pd
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SparkTrafficPipeline:
    """Pipeline base para procesamiento de tráfico"""
    
    def __init__(self, app_name="SmartCities", log_level="WARN"):
        self.spark = SparkSession.builder \
            .appName(app_name) \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.shuffle.partitions", "8") \
            .getOrCreate()
        self.spark.sparkContext.setLogLevel(log_level)
        logger.info(f"✓ SparkSession creada: {app_name}")
    
    def stop(self):
        """Detiene la sesión Spark"""
        self.spark.stop()
        logger.info("✓ SparkSession cerrada")
    
    # ============= FASE 1: LECTURA Y PROCESAMIENTO BATCH =============
    
    def load_csv(self, path: str) -> DataFrame:
        """Carga CSV y realiza parseado inicial"""
        df = self.spark.read.csv(path, header=True, inferSchema=True)
        logger.info(f"✓ Datos cargados: {df.count()} filas, esquema: {len(df.columns)} columnas")
        return df
    
    def load_multiple_csv(self, paths: list) -> DataFrame:
        """Carga y une múltiples CSVs con esquema normalizado"""
        dfs_normalized = []
        
        for path in paths:
            df = self.load_csv(path)
            cols = df.columns
            
            # Esquema 1: idTram, data, estatActual, estatPrevist (4 columnas)
            if len(cols) == 4 and 'idTram' in cols and 'data' in cols:
                df_norm = df.select("idTram", "data", "estatActual", "estatPrevist")
                dfs_normalized.append(df_norm)
                logger.info(f"  ✓ {path.split('/')[-1]} - esquema estándar (4 cols)")
            
            # Esquema 2: con columnas adicionales (8+ columnas)
            elif 'idTram' in cols and 'data' in cols and 'tempsActual' in cols:
                # Mapear columnas del nuevo esquema
                from pyspark.sql.functions import col as spark_col, round as spark_round
                df_norm = df.select(
                    "idTram",
                    "data",
                    spark_round(spark_col("tempsActual") / 300.0, 0).cast("int").alias("estatActual"),  # Mapear tiempo → estado
                    spark_round(spark_col("tempsPrevist") / 300.0, 0).cast("int").alias("estatPrevist")
                )
                dfs_normalized.append(df_norm)
                logger.info(f"  ✓ {path.split('/')[-1]} - esquema alternativo (8 cols), mapeado")
            else:
                logger.warning(f"  ⚠ {path.split('/')[-1]} - esquema desconocido, saltado")
        
        # Unir todos los DataFrames normalizados
        if not dfs_normalized:
            raise ValueError("No se pudieron cargar CSVs con esquema conocido")
        
        combined = dfs_normalized[0]
        for df in dfs_normalized[1:]:
            combined = combined.union(df)
        
        logger.info(f"✓ CSVs combinados: {combined.count()} filas totales")
        return combined
    
    def preprocess_traffic_data(self, df: DataFrame) -> DataFrame:
        """
        Preprocesamiento: timestamp, cleaning, bucketing
        Columnas esperadas: idTram, data, estatActual, estatPrevist
        """
        from pyspark.sql.functions import substring, lpad
        
        # Convertir data (numérico) a string y parsear timestamp
        df = df.withColumn(
            "timestamp", 
            to_timestamp(col("data").cast("string"), "yyyyMMddHHmmss")
        )
        
        # Extraer hora de la columna timestamp (0-23)
        from pyspark.sql.functions import hour as spark_hour
        df = df.withColumn("hour", spark_hour(col("timestamp")))
        
        df = df.fillna(0, subset=["estatActual", "estatPrevist"])
        
        # Validar rangos (0-2 son estados de congestión)
        df = df.filter((col("estatActual").between(0, 2)) | (col("estatActual").isNull()))
        logger.info("✓ Datos preprocesados")
        return df
    
    def compute_statistics(self, df: DataFrame) -> pd.DataFrame:
        """Calcula estadísticas por tramo - con límite de datos"""
        # Limitar datos para evitar Out of Memory
        stats = df.groupBy("idTram").agg(
            spark_avg("estatActual").alias("avg_congestion"),
            spark_stddev("estatActual").alias("std_congestion"),
            spark_max("estatActual").alias("max_congestion"),
            spark_min("estatActual").alias("min_congestion"),
            spark_count("*").alias("record_count")
        ).limit(500).toPandas()  # Limitar a 500 tramos
        logger.info("✓ Estadísticas calculadas")
        return stats
    
    # ============= FASE 2: STREAMING (Simulated) =============
    
    def simulate_streaming(self, df: DataFrame, batch_interval_ms: int = 1000):
        """
        Simula ingesta de datos en vivo usando RDD (sin Kafka)
        Retorna función generadora para batches - SIN COLLECT para evitar OOM
        """
        partitions = df.rdd.getNumPartitions()
        # NO colectar todo - usar particiones de Spark
        
        def batch_generator():
            # Usar sample para evitar OOM: ~1% de datos
            sampled_df = df.sample(fraction=0.01, seed=42)
            batch_list = sampled_df.collect()
            batch_size = max(1, len(batch_list) // 5)  # 5 minibatches
            logger.info(f"✓ Streaming simulado: {len(batch_list)} registros en batches")
            for i in range(0, len(batch_list), batch_size):
                batch = batch_list[i:i+batch_size]
                yield self.spark.createDataFrame(batch, df.schema)
        
        return batch_generator()
    
    def process_streaming_batch(self, batch_df: DataFrame) -> DataFrame:
        """Procesa batch de streaming en tiempo real"""
        return batch_df.withColumn(
            "processing_time",
            lit(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
    
    # ============= FASE 3: ARQUITECTURA LAMBDA =============
    
    def lambda_batch_layer(self, df_batch: DataFrame) -> DataFrame:
        """Capa batch: histórico acumulado"""
        return df_batch.select(
            "idTram", "timestamp", "estatActual", "estatPrevist", "hour"
        )
    
    def lambda_speed_layer(self, df_speed: DataFrame) -> DataFrame:
        """Capa speed: análisis en tiempo real - ventana de ~100 filas"""
        # Usar rowsBetween en lugar de rangeBetween porque timestamp no es numérico
        window = Window.partitionBy("idTram").orderBy("timestamp").rowsBetween(-100, 0)

        real_time = df_speed.withColumn(
            "rolling_avg", spark_avg("estatActual").over(window)
        ).withColumn(
            "real_time_alert",
            when(col("estatActual") > 1.5, True).otherwise(False)
        )

        return real_time
    
    def lambda_merge(self, batch_layer: DataFrame, speed_layer: DataFrame) -> DataFrame:
        """Combina capas batch y speed"""
        merged = batch_layer.join(
            speed_layer.select("idTram", "timestamp", "rolling_avg", "real_time_alert"),
            on=["idTram", "timestamp"],
            how="left"
        )
        logger.info("✓ Arquitectura Lambda procesada")
        return merged
    
    # ============= FASE 4: CLASIFICACIÓN CON MLlib =============
    
    def build_classification_model(self, df: DataFrame) -> Pipeline:
        """
        Modelo: Clasificar nivel de congestión (0=Normal, 1=Moderado, 2=Alto)
        Features: hour, idTram, previous_state
        """
        # Features
        feature_cols = ["hour", "idTram"]
        assembler = VectorAssembler(
            inputCols=feature_cols,
            outputCol="rawFeatures"
        )
        
        scaler = StandardScaler(
            inputCol="rawFeatures",
            outputCol="features",
            withMean=True,
            withStd=True
        )
        
        # Target: estatActual (0, 1, 2)
        indexer = StringIndexer(inputCol="estatActual", outputCol="label")
        
        # Modelo
        classifier = RandomForestClassifier(
            numTrees=50,
            maxDepth=10,
            seed=42,
            featuresCol="features",
            labelCol="label"
        )
        
        pipeline = Pipeline(stages=[assembler, scaler, indexer, classifier])
        
        logger.info("✓ Pipeline de clasificación creado")
        return pipeline
    
    def train_classification_model(self, df: DataFrame, split_ratio=0.8) -> tuple:
        """Entrena modelo de clasificación"""
        # Preparar datos
        df_prepared = df.filter((col("estatActual").isNotNull()) & (col("hour").isNotNull()))
        train_df, test_df = df_prepared.randomSplit([split_ratio, 1 - split_ratio], seed=42)
        
        # Entrenar
        pipeline = self.build_classification_model(df_prepared)
        model = pipeline.fit(train_df)
        
        # Evaluar
        predictions = model.transform(test_df)
        evaluator = MulticlassClassificationEvaluator(
            labelCol="label", predictionCol="prediction", metricName="accuracy"
        )
        accuracy = evaluator.evaluate(predictions)
        
        logger.info(f"✓ Modelo entrenado - Accuracy: {accuracy:.4f}")
        return model, accuracy, predictions
    
    # ============= FASE 5: PREDICCIÓN DE INCIDENTES =============
    
    def build_incident_prediction_model(self, df: DataFrame) -> tuple:
        """
        Modelo: Predecir incidentes (cambio brusco de congestión)
        Si estatActual aumenta de 0->2 en corto tiempo = incidente
        """
        # Crear target: ¿hay incidente?
        # Usar lag() para obtener el estado anterior
        window = Window.partitionBy("idTram").orderBy("timestamp")
        df_incidents = df.withColumn(
            "prev_state", lag("estatActual", 1).over(window)
        ).withColumn(
            "is_incident",
            when((col("estatActual") > col("prev_state")) & (col("estatActual") == 2), 1)
            .otherwise(0)
        )
        
        # Features
        feature_cols = ["hour", "idTram"]
        assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")
        
        # Modelo de regresión para predicción
        regressor = GBTRegressor(
            labelCol="is_incident",
            featuresCol="features",
            maxDepth=5,
            maxIter=50
        )
        
        pipeline = Pipeline(stages=[assembler, regressor])
        logger.info("✓ Pipeline de predicción de incidentes creado")
        return pipeline, df_incidents
    
    def train_incident_model(self, df: DataFrame, split_ratio=0.8) -> tuple:
        """Entrena modelo de predicción de incidentes"""
        pipeline, df_incidents = self.build_incident_prediction_model(df)
        
        df_incidents = df_incidents.fillna(0, subset=["is_incident"])
        train_df, test_df = df_incidents.randomSplit([split_ratio, 1 - split_ratio], seed=42)
        
        model = pipeline.fit(train_df)
        predictions = model.transform(test_df)
        
        evaluator = RegressionEvaluator(labelCol="is_incident", predictionCol="prediction")
        rmse = evaluator.setMetricName("rmse").evaluate(predictions)
        
        logger.info(f"✓ Modelo de incidentes entrenado - RMSE: {rmse:.4f}")
        return model, predictions
    
    # ============= FASE 6: ALERTAS AUTOMÁTICAS =============
    
    def generate_alerts(self, df: DataFrame, threshold_congestion=1.5) -> DataFrame:
        """
        Genera alertas basadas en:
        - Congestión > umbral
        - Cambio brusco de estado
        - Predicción de incidente
        """
        alerts = df.filter(col("estatActual") > threshold_congestion).select(
            "idTram", "timestamp", "estatActual",
            when(col("estatActual") == 2, "CRITICA")
            .when(col("estatActual") == 1, "ALTA")
            .otherwise("MEDIA").alias("severity")
        )
        
        logger.info(f"✓ {alerts.count()} alertas generadas")
        return alerts
    
    def alert_statistics(self, alerts: DataFrame) -> pd.DataFrame:
        """Estadísticas de alertas"""
        stats = alerts.groupBy("severity").count().toPandas()
        return stats
    
    # ============= FASE 7: RECOMENDACIONES DE RUTAS =============
    
    def generate_route_recommendations(self, df: DataFrame) -> DataFrame:
        """
        Recomienda rutas alternativas basadas en congestión actual
        Usa ventanas temporales para encontrar rutas menos congestionadas
        """
        window = Window.partitionBy("hour").orderBy(col("estatActual").asc())
        
        recommendations = df.select(
            "idTram", "hour", "estatActual",
            row_number().over(window).alias("rank")
        ).filter(col("rank") <= 3).select(
            "idTram", "hour",
            when(col("rank") == 1, "OPTIMA")
            .when(col("rank") == 2, "ALTERNATIVA_1")
            .otherwise("ALTERNATIVA_2").alias("recommendation")
        )
        
        logger.info("✓ Recomendaciones de rutas generadas")
        return recommendations
    
    # ============= UTILIDADES =============
    
    def save_to_parquet(self, df: DataFrame, path: str, mode="overwrite"):
        """Guarda DataFrame como Parquet"""
        df.write.mode(mode).parquet(path)
        logger.info(f"✓ Datos guardados en {path}")
    
    def save_to_csv(self, df: DataFrame, path: str, mode="overwrite"):
        """Guarda DataFrame como CSV"""
        pandas_df = df.toPandas()
        pandas_df.to_csv(path, index=False)
        logger.info(f"✓ Datos guardados en {path}")
    
    def show_summary(self, df: DataFrame, title: str = "", rows: int = 10):
        """Muestra resumen de DataFrame"""
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
        print(f"Total de registros: {df.count()}")
        print(f"Columnas: {len(df.columns)}")
        df.show(rows, truncate=False)
