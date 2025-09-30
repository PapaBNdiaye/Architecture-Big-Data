#!/usr/bin/env python3
"""
Spark Streaming Consumer - Couche Speed
Consomme les données Kafka et les écrit dans Cassandra en temps réel
"""

import logging
from cassandra.cluster import Cluster
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    FloatType,
    IntegerType,
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_keyspace(session):
    """Crée le keyspace Cassandra"""
    session.execute(
        """
        CREATE KEYSPACE IF NOT EXISTS spark_streams
        WITH replication = {'class': 'SimpleStrategy', 'replication_factor': '1'};
    """
    )
    print("Keyspace created successfully!")

def create_table(session):
    """Crée la table weather_data dans Cassandra"""
    session.execute(
        """
    CREATE TABLE IF NOT EXISTS spark_streams.weather_data (
        station_id TEXT PRIMARY KEY,
        timestamp TEXT,
        city TEXT,
        country TEXT,
        latitude FLOAT,
        longitude FLOAT,
        temperature FLOAT,
        humidity INT,
        pressure FLOAT,
        wind_speed FLOAT,
        wind_direction TEXT,
        precipitation FLOAT,
        weather_condition TEXT);
    """
    )
    print("Weather data table created successfully!")

def create_spark_connection():
    """Crée une session Spark avec les connecteurs nécessaires"""
    s_conn = None
    try:
        s_conn = (
            SparkSession.builder.appName("SpeedLayerStreaming")
            .config(
                "spark.jars.packages",
                "com.datastax.spark:spark-cassandra-connector_2.12:3.4.1,"
                "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1",
            )
            .config("spark.cassandra.connection.host", "cassandra")
            .getOrCreate()
        )
        s_conn.sparkContext.setLogLevel("ERROR")
        logger.info("Spark connection created successfully!")
    except Exception as e:
        logger.error(f"Couldn't create the spark session due to exception {e}")

    return s_conn

def connect_to_kafka(spark_conn):
    """Se connecte à Kafka et crée un DataFrame streaming"""
    spark_df = None
    try:
        spark_df = (
            spark_conn.readStream.format("kafka")
            .option("kafka.bootstrap.servers", "broker:29092")
            .option("subscribe", "weather_data")
            .option("startingOffsets", "earliest")
            .load()
        )
        spark_df.printSchema()
        logger.info("Kafka DataFrame created successfully")
    except Exception as e:
        logger.warning(f"Kafka DataFrame could not be created because: {e}")

    return spark_df

def create_cassandra_connection():
    """Crée une connexion à Cassandra"""
    cas_session = None
    try:
        cluster = Cluster(["cassandra"])
        cas_session = cluster.connect()
        logger.info("Cassandra connection created successfully!")
        return cas_session
    except Exception as e:
        logger.error(f"Could not create Cassandra connection due to {e}")
        return None

def create_selection_df_from_kafka(spark_df):
    """Transforme les données Kafka en DataFrame structuré"""
    # Schéma pour les données météo imbriquées
    schema = StructType(
        [
            StructField("station_id", StringType(), False),
            StructField("timestamp", StringType(), False),
            StructField(
                "location",
                StructType(
                    [
                        StructField("city", StringType(), False),
                        StructField("country", StringType(), False),
                        StructField("latitude", FloatType(), False),
                        StructField("longitude", FloatType(), False),
                    ]
                ),
            ),
            StructField("temperature", FloatType(), False),
            StructField("humidity", IntegerType(), False),
            StructField("pressure", FloatType(), False),
            StructField("wind_speed", FloatType(), False),
            StructField("wind_direction", StringType(), False),
            StructField("precipitation", FloatType(), False),
            StructField("weather_condition", StringType(), False),
        ]
    )

    # Parse le JSON Kafka selon le schéma
    parsed_df = spark_df.selectExpr("CAST(value AS STRING)").select(
        from_json(col("value"), schema).alias("data")
    )

    # Aplatit les champs imbriqués "location"
    flattened_df = parsed_df.select(
        col("data.station_id"),
        col("data.timestamp"),
        col("data.location.city").alias("city"),
        col("data.location.country").alias("country"),
        col("data.location.latitude").alias("latitude"),
        col("data.location.longitude").alias("longitude"),
        col("data.temperature"),
        col("data.humidity"),
        col("data.pressure"),
        col("data.wind_speed"),
        col("data.wind_direction"),
        col("data.precipitation"),
        col("data.weather_condition"),
    )

    return flattened_df

def start_spark_stream():
    """Lance le streaming Spark"""
    print("Spark Streaming - Couche Speed")
    print("=" * 40)
    
    # Création de la session Spark
    spark_conn = create_spark_connection()

    if spark_conn is not None:
        # Connexion à Kafka
        spark_df = connect_to_kafka(spark_conn)
        selection_df = create_selection_df_from_kafka(spark_df)
        
        # Connexion à Cassandra
        session = create_cassandra_connection()

        if session is not None:
            create_keyspace(session)
            create_table(session)

            print("Streaming is being started...")

            try:
                streaming_query = (
                    selection_df.writeStream.format("org.apache.spark.sql.cassandra")
                    .option("checkpointLocation", "/tmp/checkpoint")
                    .option("keyspace", "spark_streams")
                    .option("table", "weather_data")
                    .start()
                )
                logger.info("Streaming query started successfully!")
                print("Pipeline Speed Layer actif ! Données météo traitées en temps réel.")
                print("Consultez Cassandra pour voir les données : docker exec -it cassandra cqlsh")
                
                streaming_query.awaitTermination()
                
            except Exception as e:
                logger.error(f"Streaming query failed due to: {e}")

if __name__ == "__main__":
    start_spark_stream()
