#!/usr/bin/env python3
"""
Traitement batch FULL SPARK (version simplifiée) :
- Spark distribue les appels à l'API Visual Crossing
- Chaque worker télécharge les données pour une ville
- Les données brutes sont sauvegardées dans HDFS
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

# === Fonction exécutée par chaque worker ===
def fetch_city_weather(city, start_date="2025-01-01", end_date="2025-01-10"):
    max_retries = 3
    base_delay = 5
    
    for attempt in range(max_retries):
        try:
            url = f"{BASE_URL}/{city}/{start_date}/{end_date}"
            params = get_api_params()
            params["key"] = API_KEY

            print(f"📡 Fetching {city} → {url} (tentative {attempt + 1}/{max_retries})")  # Debug
            
            # Délai progressif entre les tentatives
            if attempt > 0:
                delay = base_delay * (2 ** attempt)  # Backoff exponentiel
                print(f"⏳ Attente de {delay} secondes avant la tentative {attempt + 1}...")
                time.sleep(delay)
            else:
                time.sleep(2)  # Délai normal pour la première tentative
            
            response = requests.get(url, params=params, timeout=30)
            print(f"🔑 Status {response.status_code} for {city}")  # Debug

            if response.status_code == 429:
                if attempt < max_retries - 1:
                    print(f"⚠️  Limite de taux atteinte pour {city}, nouvelle tentative dans {base_delay * (2 ** attempt)} secondes...")
                    continue
                else:
                    print(f"❌ Limite de taux persistante pour {city} après {max_retries} tentatives")
                    return []

            response.raise_for_status()
            data = response.json()
            days = data.get("days", [])

            print(f"📊 {city} → {len(days)} jours reçus")  # Debug

            results = []
            for d in days:
                results.append({
                    "city": city,
                    "date": d.get("datetime"),
                    "temp": d.get("temp"),
                    "humidity": d.get("humidity"),
                    "pressure": d.get("pressure"),
                    "windspeed": d.get("windspeed"),
                    "precip": d.get("precip")
                })
            return results

        except Exception as e:
            print(f"❌ Erreur pour {city} (tentative {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                return []
            continue
    
    return []


def main():
    # Vérification de l'API key
    if API_KEY == "VOTRE_API_KEY":
        print("❌ ERREUR: API key non configurée! Définissez la variable d'environnement VISUAL_CROSSING_API_KEY")
        return
    
    print(f"🔑 API Key configurée: {API_KEY[:8]}...")
    
    spark = SparkSession.builder \
        .appName("WeatherBatchProcessingFullSparkRaw") \
        .config("spark.hadoop.fs.defaultFS", "hdfs://hdfs-namenode:8020") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    # === Liste des villes depuis config ===
    cities = CITIES

    # === Distribution des appels API ===
    print(f"🏙️  Traitement de {len(cities)} villes: {cities}")
    rdd = spark.sparkContext.parallelize(cities, len(cities))
    results_rdd = rdd.flatMap(lambda city: fetch_city_weather(city))
    
    # Debug: compter les résultats avant création du DataFrame
    results_count = results_rdd.count()
    print(f"📊 Nombre total de résultats récupérés: {results_count}")
    
    if results_count == 0:
        print("❌ Aucune donnée récupérée! Vérifiez votre API key et la connectivité.")
        spark.stop()
        return
    
    # Collecter quelques exemples pour debug
    sample_results = results_rdd.take(3)
    print(f"🔍 Exemples de données: {sample_results}")

    weather_df = spark.createDataFrame(results_rdd.map(lambda x: Row(**x)))

    # Cast des colonnes (seulement celles qui existent dans les données)
    weather_df = weather_df.withColumn("date", col("date").cast("date")) \
                           .withColumn("temp", col("temp").cast("double")) \
                           .withColumn("humidity", col("humidity").cast("double")) \
                           .withColumn("pressure", col("pressure").cast("double")) \
                           .withColumn("windspeed", col("windspeed").cast("double")) \
                           .withColumn("precip", col("precip").cast("double"))

    # === Sauvegarde uniquement des données brutes ===
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_output = f"hdfs://hdfs-namenode:8020/user/spark/weather/raw/{timestamp}"
    weather_df.write.mode("overwrite").parquet(raw_output)

    print(f"✅ Données brutes sauvegardées dans {raw_output}")

    spark.stop()

if __name__ == "__main__":
    main()
