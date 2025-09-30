#!/usr/bin/env python3
"""
Script d'export des données météo vers PostgreSQL.

Ce module exporte les données météo depuis HDFS vers PostgreSQL
pour permettre leur visualisation dans Grafana.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
import psycopg2
from datetime import datetime

class WeatherDataExporter:
    def __init__(self):
        self.spark = SparkSession.builder \
            .appName("WeatherDataExporter") \
            .config("spark.hadoop.fs.defaultFS", "hdfs://hdfs-namenode:8020") \
            .getOrCreate()
        
        self.spark.sparkContext.setLogLevel("WARN")
        
        # Configuration PostgreSQL
        self.pg_config = {
            'host': 'postgres',
            'port': 5432,
            'database': 'airflow',
            'user': 'airflow',
            'password': 'airflow'
        }
    
    def create_weather_tables(self):
        """Crée les tables PostgreSQL pour les données météo"""
        print("Création des tables PostgreSQL...")
        
        conn = psycopg2.connect(**self.pg_config)
        cursor = conn.cursor()
        
        # Table des données météo brutes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weather_data (
                id SERIAL PRIMARY KEY,
                city VARCHAR(50),
                date DATE,
                temp DECIMAL(5,2),
                tempmax DECIMAL(5,2),
                tempmin DECIMAL(5,2),
                humidity DECIMAL(5,2),
                precip DECIMAL(5,2),
                windspeed DECIMAL(5,2),
                pressure DECIMAL(7,2),
                cloudcover DECIMAL(5,2),
                visibility DECIMAL(5,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table des analyses agrégées
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weather_analysis (
                id SERIAL PRIMARY KEY,
                analysis_type VARCHAR(50),
                city VARCHAR(50),
                metric_name VARCHAR(100),
                metric_value DECIMAL(10,4),
                analysis_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("Tables créées avec succès")
    
    def export_raw_data(self, hdfs_path="hdfs://hdfs-namenode:8020/user/spark/weather/raw/20250925_133714"):
        """Exporte les données brutes vers PostgreSQL"""
        print(f"Export des données brutes depuis {hdfs_path}")
        
        # Charger les données depuis HDFS
        df = self.spark.read.parquet(hdfs_path)
        
        # Convertir en DataFrame pandas pour l'export
        pandas_df = df.toPandas()
        
        # Connexion PostgreSQL
        conn = psycopg2.connect(**self.pg_config)
        cursor = conn.cursor()
        
        # Insérer les données
        for _, row in pandas_df.iterrows():
            cursor.execute("""
                INSERT INTO weather_data (city, date, temp, tempmax, tempmin, humidity, 
                                       precip, windspeed, pressure, cloudcover, visibility)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                row['city'], row['date'], row['temp'], row['tempmax'], row['tempmin'],
                row['humidity'], row['precip'], row['windspeed'], row['pressure'],
                row['cloudcover'], row['visibility']
            ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"{len(pandas_df)} enregistrements exportés vers PostgreSQL")
    
    def export_analysis_results(self):
        """Exporte les résultats d'analyse vers PostgreSQL"""
        print("Export des résultats d'analyse...")
        
        # Charger les données pour les analyses
        hdfs_path = "hdfs://hdfs-namenode:8020/user/spark/weather/raw/20250925_133714"
        df = self.spark.read.parquet(hdfs_path)
        
        # Analyses par ville
        city_stats = df.groupBy("city") \
            .agg(
                avg("temp").alias("temp_moyenne"),
                max("tempmax").alias("temp_max"),
                min("tempmin").alias("temp_min"),
                avg("precip").alias("precip_moyenne"),
                avg("windspeed").alias("vent_moyen"),
                avg("humidity").alias("humidite_moyenne")
            ).collect()
        
        # Connexion PostgreSQL
        conn = psycopg2.connect(**self.pg_config)
        cursor = conn.cursor()
        
        # Insérer les analyses
        for row in city_stats:
            metrics = [
                ("temp_moyenne", row["temp_moyenne"]),
                ("temp_max", row["temp_max"]),
                ("temp_min", row["temp_min"]),
                ("precip_moyenne", row["precip_moyenne"]),
                ("vent_moyen", row["vent_moyen"]),
                ("humidite_moyenne", row["humidite_moyenne"])
            ]
            
            for metric_name, metric_value in metrics:
                cursor.execute("""
                    INSERT INTO weather_analysis (analysis_type, city, metric_name, metric_value, analysis_date)
                    VALUES (%s, %s, %s, %s, %s)
                """, ("city_stats", row["city"], metric_name, metric_value, datetime.now().date()))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("Analyses exportées vers PostgreSQL")
    
    def run_export(self):
        """Exécute l'export complet"""
        print("Démarrage de l'export vers PostgreSQL...")
        print("=" * 50)
        
        try:
            self.create_weather_tables()
            self.export_raw_data()
            self.export_analysis_results()
            
            print("\nExport terminé avec succès!")
            print("Données disponibles dans PostgreSQL")
            print("Grafana peut maintenant se connecter à ces données")
            
        except Exception as e:
            print(f"Erreur lors de l'export: {e}")
        
        finally:
            self.spark.stop()

def main():
    exporter = WeatherDataExporter()
    exporter.run_export()

if __name__ == "__main__":
    main()
