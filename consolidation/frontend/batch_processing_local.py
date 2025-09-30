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
def fetch_city_weather(city, start_date="2021-01-01", end_date="2025-09-24"):
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
    # Vérification de l'API key
    if API_KEY == "VOTRE_API_KEY":
        print("ERREUR: API key non configurée! Définissez la variable d'environnement VISUAL_CROSSING_API_KEY")
        return
    
    print(f"API Key configurée: {API_KEY[:8]}...")
    
    # Test local sans Spark
    cities = CITIES[:1]  # Une seule ville pour test
    
    print(f"Test avec {len(cities)} ville: {cities}")
    
    for city in cities:
        data = fetch_city_weather(city)
        if data:
            print(f"Données récupérées pour {city}: {len(data)} jours")
            print("Exemples de données:")
            for d in data[:3]:  # Afficher 3 premiers jours
                print(f"  {d}")
        else:
            print(f"Aucune donnée pour {city}")
