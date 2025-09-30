#!/usr/bin/env python3
"""
Traitement batch des données météo avec Apache Spark.

Ce script récupère les données météo depuis l'API Visual Crossing
pour plusieurs villes françaises et les stocke dans HDFS au format Parquet.
Le traitement est distribué sur le cluster Spark.
"""

import requests
import time
from datetime import datetime
from pyspark.sql import SparkSession, Row
from pyspark.sql.functions import col

# Import config
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "config"))
from cities_config import CITIES, API_CONFIG, get_api_params

API_KEY = os.getenv("VISUAL_CROSSING_API_KEY", "VOTRE_API_KEY")
BASE_URL = API_CONFIG['base_url']

def fetch_city_weather(city, start_date="2021-01-01", end_date="2025-09-24"):
    """
    Récupère les données météo pour une ville donnée depuis l'API Visual Crossing.
    
    Args:
        city: Nom de la ville au format "Ville,Pays"
        start_date: Date de début au format YYYY-MM-DD
        end_date: Date de fin au format YYYY-MM-DD
    
    Returns:
        Liste de dictionnaires contenant les données météo
    """
    max_retries = 3
    base_delay = 5
    
    for attempt in range(max_retries):
        try:
            url = f"{BASE_URL}/{city}/{start_date}/{end_date}"
            params = get_api_params()
            params["key"] = API_KEY

            print(f"Récupération des données pour {city} (tentative {attempt + 1}/{max_retries})")
            
            # Délai progressif entre les tentatives
            if attempt > 0:
                delay = base_delay * (2 ** attempt)  # Backoff exponentiel
                print(f"Attente de {delay} secondes avant la tentative {attempt + 1}...")
                time.sleep(delay)
            else:
                time.sleep(2)  # Délai normal pour la première tentative
            
            response = requests.get(url, params=params, timeout=30)
            print(f"Status {response.status_code} pour {city}")

            if response.status_code == 429:
                if attempt < max_retries - 1:
                    print(f"Limite de taux atteinte pour {city}, nouvelle tentative dans {base_delay * (2 ** attempt)} secondes...")
                    continue
                else:
                    print(f"Limite de taux persistante pour {city} après {max_retries} tentatives")
                    return []

            response.raise_for_status()
            data = response.json()
            days = data.get("days", [])

            print(f"{city}: {len(days)} jours de données reçus")

            results = []
            for d in days:
                # Récupérer toutes les colonnes disponibles depuis l'API
                result = {
                    "city": city,
                    "date": d.get("datetime"),
                    "address": d.get("address"),
                    "latitude": d.get("latitude"),
                    "longitude": d.get("longitude"),
                    "temp": d.get("temp"),
                    "tempmax": d.get("tempmax"),
                    "tempmin": d.get("tempmin"),
                    "humidity": d.get("humidity"),
                    "dew": d.get("dew"),
                    "precip": d.get("precip"),
                    "preciptype": d.get("preciptype"),
                    "pressure": d.get("pressure"),
                    "windspeed": d.get("windspeed"),
                    "windgust": d.get("windgust"),
                    "winddir": d.get("winddir"),
                    "cloudcover": d.get("cloudcover"),
                    "visibility": d.get("visibility")
                }
                results.append(result)
            return results

        except Exception as e:
            print(f"Erreur pour {city} (tentative {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                return []
            continue
    
    return []


def main():
    """
    Fonction principale du traitement batch.
    """
    # Vérification de l'API key
    if API_KEY == "VOTRE_API_KEY":
        print("ERREUR: API key non configurée! Définissez la variable d'environnement VISUAL_CROSSING_API_KEY")
        return
    
    print(f"API Key configurée: {API_KEY[:8]}...")
    
    spark = SparkSession.builder \
        .appName("WeatherBatchProcessingFullSparkRaw") \
        .config("spark.hadoop.fs.defaultFS", "hdfs://hdfs-namenode:8020") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    # Liste des villes depuis config
    cities = CITIES

    # Distribution des appels API
    print(f"Traitement de {len(cities)} villes: {cities}")
    rdd = spark.sparkContext.parallelize(cities, len(cities))
    results_rdd = rdd.flatMap(lambda city: fetch_city_weather(city))
    
    # Compter les résultats avant création du DataFrame
    results_count = results_rdd.count()
    print(f"Nombre total de résultats récupérés: {results_count}")
    
    if results_count == 0:
        print("Aucune donnée récupérée! Vérifiez votre API key et la connectivité.")
        spark.stop()
        return
    
    # Collecter quelques exemples pour debug
    sample_results = results_rdd.take(3)
    print(f"Exemples de données: {sample_results}")

    # Définir le schéma explicitement pour éviter les erreurs d'inférence
    from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType
    
    schema = StructType([
        StructField("city", StringType(), True),
        StructField("date", StringType(), True),
        StructField("address", StringType(), True),
        StructField("latitude", DoubleType(), True),
        StructField("longitude", DoubleType(), True),
        StructField("temp", DoubleType(), True),
        StructField("tempmax", DoubleType(), True),
        StructField("tempmin", DoubleType(), True),
        StructField("humidity", DoubleType(), True),
        StructField("dew", DoubleType(), True),
        StructField("precip", DoubleType(), True),
        StructField("preciptype", StringType(), True),
        StructField("pressure", DoubleType(), True),
        StructField("windspeed", DoubleType(), True),
        StructField("windgust", DoubleType(), True),
        StructField("winddir", DoubleType(), True),
        StructField("cloudcover", DoubleType(), True),
        StructField("visibility", DoubleType(), True)
    ])
    
    weather_df = spark.createDataFrame(results_rdd.map(lambda x: Row(**x)), schema)

    # Convertir la colonne date en type date
    weather_df = weather_df.withColumn("date", col("date").cast("date"))

    # Sauvegarde uniquement des données brutes
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_output = f"hdfs://hdfs-namenode:8020/user/spark/weather/raw/{timestamp}"
    weather_df.write.mode("overwrite").parquet(raw_output)

    print(f"Données brutes sauvegardées dans {raw_output}")

    spark.stop()

if __name__ == "__main__":
    main()
