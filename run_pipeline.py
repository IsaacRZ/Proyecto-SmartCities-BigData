#!/usr/bin/env python3
"""
Smart Cities Traffic Pipeline - Script de ejecución completa
Ejecuta las 8 fases sin necesidad de Jupyter

Uso:
    python run_pipeline.py                    # Ejecuta todas las fases
    python run_pipeline.py --phase 1          # Ejecuta solo fase 1
    python run_pipeline.py --help             # Muestra opciones
"""

import sys
import os
import argparse
from pathlib import Path

# Configurar HADOOP_HOME para Windows ANTES de importar Spark
if sys.platform == "win32" and not os.environ.get("HADOOP_HOME"):
    hadoop_home = Path(os.environ.get("USERPROFILE", "C:\\Users\\Default")) / ".hadoop" / "hadoop-3.2.2"
    os.environ["HADOOP_HOME"] = str(hadoop_home)
    os.environ["hadoop.home.dir"] = str(hadoop_home)
    bin_dir = hadoop_home / "bin"
    if str(bin_dir) not in os.environ.get("PATH", ""):
        os.environ["PATH"] = str(bin_dir) + ";" + os.environ.get("PATH", "")

# Agregar scripts al path
scripts_dir = Path(__file__).parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from spark_pipeline import SparkTrafficPipeline
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_phase_1(pipeline):
    """FASE 1: Lectura y procesamiento batch"""
    logger.info("="*70)
    logger.info(" FASE 1: Lectura y Procesamiento Batch de CSVs")
    logger.info("="*70)
    
    import glob
    csv_files = sorted([f for f in glob.glob("data/raw/*.csv") if "Tramos" not in f])
    
    logger.info(f"CSVs encontrados: {len(csv_files)}")
    
    df_raw = pipeline.load_multiple_csv(csv_files)
    df_processed = pipeline.preprocess_traffic_data(df_raw)
    stats_df = pipeline.compute_statistics(df_processed)
    
    pipeline.show_summary(df_processed, "FASE 1: Datos Procesados")
    
    return df_processed


def run_phase_2(pipeline, df_processed):
    """FASE 2: Streaming simulado"""
    logger.info("="*70)
    logger.info(" FASE 2: Spark Streaming - Simulación de Ingesta en Vivo")
    logger.info("="*70)
    
    streaming_generator = pipeline.simulate_streaming(df_processed)
    
    streaming_batches = []
    for i, batch in enumerate(streaming_generator):
        if i >= 5:
            break
        batch_processed = pipeline.process_streaming_batch(batch)
        streaming_batches.append(batch_processed)
        logger.info(f"  Batch {i+1}: {batch_processed.count()} registros")
    
    df_streaming_combined = streaming_batches[0]
    for batch in streaming_batches[1:]:
        df_streaming_combined = df_streaming_combined.union(batch)
    
    logger.info(f"✓ Total registros streaming: {df_streaming_combined.count()}")
    
    return df_streaming_combined


def run_phase_3(pipeline, df_processed, df_streaming_combined):
    """FASE 3: Arquitectura Lambda"""
    logger.info("="*70)
    logger.info(" FASE 3: Arquitectura Lambda")
    logger.info("="*70)
    
    batch_layer = pipeline.lambda_batch_layer(df_processed)
    speed_layer = pipeline.lambda_speed_layer(df_streaming_combined)
    serving_layer = pipeline.lambda_merge(batch_layer, speed_layer)
    
    logger.info(f"✓ Serving Layer creada: {serving_layer.count()} registros")
    
    return serving_layer


def run_phase_4(pipeline, df_processed):
    """FASE 4: Clasificación con MLlib"""
    logger.info("="*70)
    logger.info(" FASE 4: Clasificación de Congestión con MLlib")
    logger.info("="*70)
    
    classification_model, accuracy, predictions_class = pipeline.train_classification_model(df_processed)
    
    logger.info(f"📈 Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
    
    return classification_model, predictions_class


def run_phase_5(pipeline, df_processed):
    """FASE 5: Predicción de incidentes"""
    logger.info("="*70)
    logger.info(" FASE 5: Predicción de Incidentes de Tráfico")
    logger.info("="*70)
    
    incident_model, predictions_incident = pipeline.train_incident_model(df_processed)
    
    incidents_detected = predictions_incident.filter(
        (predictions_incident.is_incident == 1) | 
        (predictions_incident.prediction > 0.5)
    )
    
    logger.info(f"⚠️ Incidentes detectados: {incidents_detected.count()}")
    
    return incident_model, predictions_incident


def run_phase_6(pipeline, df_processed):
    """FASE 6: Alertas automáticas"""
    logger.info("="*70)
    logger.info(" FASE 6: Sistema de Alertas Automáticas")
    logger.info("="*70)
    
    alerts_df = pipeline.generate_alerts(df_processed)
    alert_stats = pipeline.alert_statistics(alerts_df)
    
    logger.info(f"🔔 Total alertas: {alerts_df.count()}")
    logger.info("\nDistribución por severidad:")
    logger.info(alert_stats.to_string(index=False))
    
    return alerts_df


def run_phase_7(pipeline, df_processed):
    """FASE 7: Recomendaciones de rutas"""
    logger.info("="*70)
    logger.info(" FASE 7: Motor de Recomendación de Rutas")
    logger.info("="*70)
    
    recommendations_df = pipeline.generate_route_recommendations(df_processed)
    
    logger.info(f"✓ Recomendaciones generadas: {recommendations_df.count()}")
    
    # Guardar
    recommendations_df.coalesce(1).write.mode("overwrite").option("header", "true").csv(
        "data/processed/route_recommendations"
    )
    logger.info("✓ Guardado en data/processed/route_recommendations")
    
    return recommendations_df


def run_phase_8(pipeline, df_processed, predictions_class, alerts_df, recommendations_df):
    """FASE 8: Grafana"""
    logger.info("="*70)
    logger.info(" FASE 8: Dashboard Grafana y Exportación")
    logger.info("="*70)
    
    from pyspark.sql.functions import avg as spark_avg, max as spark_max, min as spark_min, count as spark_count
    
    # Preparar métricas
    metrics_for_grafana = df_processed.groupBy("idTram", "hour").agg(
        spark_avg("estatActual").alias("avg_congestion"),
        spark_max("estatActual").alias("max_congestion"),
        spark_min("estatActual").alias("min_congestion"),
        spark_count("*").alias("observation_count")
    )
    
    logger.info(f"✓ Tabla de métricas: {metrics_for_grafana.count()} registros")
    
    # Guardar
    pipeline.save_to_parquet(metrics_for_grafana, "data/processed/metrics_grafana")
    metrics_for_grafana.coalesce(1).write.mode("overwrite").option("header", "true").csv(
        "data/processed/metrics_csv"
    )
    alerts_df.coalesce(1).write.mode("overwrite").option("header", "true").csv(
        "data/processed/alerts_csv"
    )
    predictions_class.select("idTram", "hour", "estatActual", "prediction").coalesce(1).write.mode("overwrite").option("header", "true").csv(
        "data/processed/predictions_csv"
    )
    
    logger.info("✓ Métricas guardadas → data/processed/metrics_grafana")
    logger.info("✓ Alertas guardadas → data/processed/alerts_csv")
    logger.info("✓ Predicciones guardadas → data/processed/predictions_csv")
    
    # Intentar conexión a PostgreSQL
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="smart_cities",
            user="postgres",
            password="postgres"
        )
        cur = conn.cursor()
        
        logger.info("✓ Conexión exitosa a PostgreSQL")
        
        # Crear tabla
        cur.execute("""
            CREATE TABLE IF NOT EXISTS traffic_metrics (
                idTram INTEGER,
                hour INTEGER,
                avg_congestion FLOAT,
                max_congestion FLOAT,
                min_congestion FLOAT,
                observation_count INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        
        # Insertar datos
        metrics_pd = metrics_for_grafana.limit(1000).toPandas()
        for idx, row in metrics_pd.iterrows():
            cur.execute("""
                INSERT INTO traffic_metrics 
                (idTram, hour, avg_congestion, max_congestion, min_congestion, observation_count)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (int(row['idTram']), int(row['hour']), float(row['avg_congestion']),
                  float(row['max_congestion']), float(row['min_congestion']), int(row['observation_count'])))
        
        conn.commit()
        logger.info(f"✓ {len(metrics_pd)} registros insertados en PostgreSQL")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        logger.warning(f"⚠️ No se pudo conectar a PostgreSQL: {str(e)}")
        logger.info("   Los datos están guardados en CSV y Parquet")


def main():
    parser = argparse.ArgumentParser(
        description="Smart Cities Traffic Pipeline - Todas las 8 fases",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python run_pipeline.py                    # Ejecuta todas las fases
  python run_pipeline.py --phase 1          # Solo fase 1
  python run_pipeline.py --phase 1 2 3      # Fases 1, 2 y 3
  python run_pipeline.py --skip-db           # Sin conexión PostgreSQL
        """
    )
    
    parser.add_argument(
        "--phase",
        type=int,
        nargs="+",
        choices=range(1, 9),
        help="Fases a ejecutar (1-8)"
    )
    parser.add_argument(
        "--skip-db",
        action="store_true",
        help="Saltar conexión a PostgreSQL en fase 8"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Nivel de logging"
    )
    
    args = parser.parse_args()
    
    # Configurar logging
    logging.getLogger().setLevel(args.log_level)
    
    # Cambiar al directorio del proyecto
    os.chdir(Path(__file__).parent)
    
    # Inicializar pipeline
    logger.info("🚀 Iniciando Smart Cities Traffic Pipeline\n")
    pipeline = SparkTrafficPipeline(log_level=args.log_level)
    
    phases = args.phase if args.phase else list(range(1, 9))
    
    try:
        # FASE 1
        if 1 in phases:
            df_processed = run_phase_1(pipeline)
        else:
            logger.warning("Fase 1 requerida para continuar")
            return
        
        # FASE 2
        if 2 in phases:
            df_streaming_combined = run_phase_2(pipeline, df_processed)
        else:
            logger.info("Saltando fase 2")
            df_streaming_combined = df_processed
        
        # FASE 3
        if 3 in phases:
            serving_layer = run_phase_3(pipeline, df_processed, df_streaming_combined)
        
        # FASE 4
        if 4 in phases:
            classification_model, predictions_class = run_phase_4(pipeline, df_processed)
        else:
            predictions_class = None
        
        # FASE 5
        if 5 in phases:
            incident_model, predictions_incident = run_phase_5(pipeline, df_processed)
        
        # FASE 6
        if 6 in phases:
            alerts_df = run_phase_6(pipeline, df_processed)
        else:
            alerts_df = None
        
        # FASE 7
        if 7 in phases:
            recommendations_df = run_phase_7(pipeline, df_processed)
        else:
            recommendations_df = None
        
        # FASE 8
        if 8 in phases and not args.skip_db:
            run_phase_8(pipeline, df_processed, predictions_class, alerts_df, recommendations_df)
        
        logger.info("\n" + "="*70)
        logger.info(" ✓ ¡PIPELINE COMPLETADO EXITOSAMENTE!")
        logger.info("="*70)
        logger.info("\n📊 Próximos pasos:")
        logger.info("  1. Iniciar Docker: cd sumo_db_project && docker-compose up -d")
        logger.info("  2. Acceder a Grafana: http://localhost:3000")
        logger.info("  3. Configurar Data Source con PostgreSQL")
        logger.info("  4. Crear dashboards con queries_grafana.sql")
        
    except Exception as e:
        logger.error(f"\n❌ Error en pipeline: {str(e)}", exc_info=True)
        return 1
    
    finally:
        # pipeline.stop()  # Descomentar si no necesitas explorar datos
        pass
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
