#!/usr/bin/env python3
"""
Version avec données de test pour éviter la limite de taux API
"""

import random
from datetime import datetime, timedelta
from pyspark.sql import SparkSession, Row
from pyspark.sql.functions import col

# Import config
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "config"))
from cities_config import CITIES

def generate_test_weather_data(city, start_date="2025-01-01", end_date="2025-01-10"):
    """Génère des données météo simulées pour une ville"""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    results = []
    current_date = start
    
    while current_date <= end:
        # Génération de données réalistes selon la saison
        base_temp = random.uniform(-5, 25)  # Température de base
        temp_variation = random.uniform(-3, 3)
        temp = round(base_temp + temp_variation, 1)
        
        humidity = round(random.uniform(30, 95), 1)
        pressure = round(random.uniform(990, 1030), 1)
        windspeed = round(random.uniform(0, 30), 1)
        precip = round(random.uniform(0, 15), 3)
        
        results.append({
            "city": city,
            "date": current_date.strftime("%Y-%m-%d"),
            "temp": temp,
            "humidity": humidity,
            "pressure": pressure,
            "windspeed": windspeed,
            "precip": precip
        })
        
        current_date += timedelta(days=1)
    
    return results

def main():
    spark = SparkSession.builder \
        .appName("WeatherBatchProcessingTestData") \
        .config("spark.hadoop.fs.defaultFS", "hdfs://hdfs-namenode:8020") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    # === Liste des villes depuis config ===
    cities = CITIES

    # === Génération des données de test ===
    print(f"🏙️  Génération de données de test pour {len(cities)} villes: {cities}")
    
    all_results = []
    for city in cities:
        print(f"📊 Génération des données pour {city}...")
        city_data = generate_test_weather_data(city)
        all_results.extend(city_data)
    
    print(f"📊 Nombre total de résultats générés: {len(all_results)}")
    
    if len(all_results) == 0:
        print("❌ Aucune donnée générée!")
        spark.stop()
        return
    
    # Collecter quelques exemples pour debug
    sample_results = all_results[:3]
    print(f"🔍 Exemples de données: {sample_results}")

    # === Création du DataFrame Spark ===
    rdd = spark.sparkContext.parallelize(all_results)
    weather_df = spark.createDataFrame(rdd.map(lambda x: Row(**x)))

    # Cast des colonnes (seulement celles qui existent dans les données)
    weather_df = weather_df.withColumn("date", col("date").cast("date")) \
                           .withColumn("temp", col("temp").cast("double")) \
                           .withColumn("humidity", col("humidity").cast("double")) \
                           .withColumn("pressure", col("pressure").cast("double")) \
                           .withColumn("windspeed", col("windspeed").cast("double")) \
                           .withColumn("precip", col("precip").cast("double"))

    # === Sauvegarde des données brutes ===
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_output = f"hdfs://hdfs-namenode:8020/user/spark/weather/raw/test_data_{timestamp}"
    weather_df.write.mode("overwrite").parquet(raw_output)

    print(f"✅ Données de test sauvegardées dans {raw_output}")
    print(f"📊 {weather_df.count()} enregistrements sauvegardés")

    spark.stop()

if __name__ == "__main__":
    main()
