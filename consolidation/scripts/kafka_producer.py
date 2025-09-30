#!/usr/bin/env python3
"""
Producteur Kafka pour données météo - Couche Speed
Génère et envoie des données météo vers Kafka en temps réel
"""

import time
import random
import json
import os
import argparse
import signal
import sys
import requests
from datetime import datetime, timezone
from kafka import KafkaProducer
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

"""
Points clés de la mise à jour:
1. Passage à l'API réelle Visual Crossing (clé lue via variable d'environnement VISUAL_CROSSING_API_KEY ou fallback)
2. Restriction aux 5 villes françaises demandées
3. Timestamp en format RFC3339 avec suffixe Z (UTC)
4. Champs enrichis: is_rain, is_storm, next_hour_temp, next_hour_precip
5. Fallback simulation conserve les mêmes champs pour homogénéité du schéma
"""

# Configuration API Visual Crossing Weather
VISUAL_CROSSING_API_KEY = os.getenv("VISUAL_CROSSING_API_KEY", "RZT2CJT5TFDCTJV3PWM4NAWGP")  # Peut être surchargé par variable d'env
VISUAL_CROSSING_BASE_URL = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"

# Configuration Kafka
KAFKA_HOSTS = ["localhost:9092"]
KAFKA_TOPIC = "weather_data_v2"  # Nouveau topic (évite anciens messages)

# Villes françaises sélectionnées
CITIES = [
    "Paris,FR",
    "Lyon,FR",
    "Marseille,FR",
    "Toulouse,FR",
    "Bordeaux,FR"
]

def _rfc3339_utc_now():
    """Retourne un timestamp RFC3339 UTC sans microsecondes (compatibilité Telegraf)."""
    return datetime.utcnow().replace(microsecond=0, tzinfo=timezone.utc).isoformat().replace('+00:00', 'Z')


def fetch_weather_data_from_api(city: str):
    """Récupère et enrichit les données météo depuis l'API Visual Crossing.

    Logiciel:
      - Récupère le jour courant (include=hours) en unités métriques
      - Sélectionne l'heure la plus récente disponible comme "courante"
      - Tente d'extraire l'heure suivante pour prévision (next_hour_*)
      - Calcule les booléens is_rain / is_storm
    Retourne None en cas d'erreur pour permettre un fallback simulé cohérent.
    """
    if not VISUAL_CROSSING_API_KEY or VISUAL_CROSSING_API_KEY == "YOUR_API_KEY_HERE":
        return None

    try:
        url = f"{VISUAL_CROSSING_BASE_URL}/{city}/today"
        params = {
            "unitGroup": "metric",
            "contentType": "json",
            "key": VISUAL_CROSSING_API_KEY,
            "include": "hours"
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get('days'):
            return None

        day_data = data['days'][0]
        hours = day_data.get('hours', []) or []
        if not hours:
            return None

        # Heures ordonnées; on prend la dernière comme "courante"
        current_hour = hours[-1]
        # Heures triées par datetime (HH:MM:SS) pour trouver l'heure suivante s'il y en a une
        try:
            # Construire une liste triée et trouver index de current_hour
            sorted_hours = sorted(hours, key=lambda h: h.get('datetime'))
            idx = sorted_hours.index(current_hour)
            next_hour = sorted_hours[idx + 1] if idx + 1 < len(sorted_hours) else None
        except Exception:
            next_hour = None

        temp = float(current_hour.get('temp', 0))
        precip = float(current_hour.get('precip', 0) or 0)
        conditions = (current_hour.get('conditions') or 'Unknown')
        cond_lower = conditions.lower()
        is_rain = precip > 0 or any(k in cond_lower for k in ["rain", "drizzle", "shower"])
        is_storm = any(k in cond_lower for k in ["storm", "thunder", "lightning"])

        next_hour_temp = float(next_hour.get('temp', temp)) if next_hour else temp
        next_hour_precip = float(next_hour.get('precip', precip)) if next_hour else precip

        return {
            "station_id": f"station_{city.replace(',', '_').replace(' ', '_')}",
            # Utilisation timestamp UTC actuel (plus fiable pour alignement temps réel)
            "timestamp": _rfc3339_utc_now(),
            "location": {
                "city": data['address'].split(',')[0] if ',' in data['address'] else data['address'],
                "country": data['address'].split(',')[-1].strip() if ',' in data['address'] else "FR",
                "latitude": float(data.get('latitude', 0.0)),
                "longitude": float(data.get('longitude', 0.0)),
            },
            "temperature": temp,
            "humidity": int(current_hour.get('humidity', 0) or 0),
            "pressure": float(current_hour.get('pressure', 1013) or 1013),
            "wind_speed": float(current_hour.get('windspeed', 0) or 0),
            "wind_direction": current_hour.get('winddir', 'N'),
            "precipitation": precip,
            "weather_condition": conditions,
            "is_rain": int(is_rain),  # 0/1 pour stockage time-series
            "is_storm": int(is_storm),
            "next_hour_temp": next_hour_temp,
            "next_hour_precip": next_hour_precip,
            "data_origin": "api"
        }
    except Exception as e:
        logger.error(f"Erreur API pour {city}: {e}")
        return None

def generate_weather_data():
    """Génère des données météo (priorité API, sinon simulation enrichie)."""
    city = random.choice(CITIES)

    # Tentative avec l'API
    weather_data = fetch_weather_data_from_api(city)
    if weather_data is not None:
        return weather_data

    # Fallback simulation enrichie
    logger.warning(f"Utilisation de données simulées pour {city}")
    temp = round(random.uniform(-5, 35), 1)
    precip = round(random.uniform(0, 15), 2)
    conditions = random.choice(["Sunny", "Cloudy", "Rain", "Showers", "Storm", "Fog", "Drizzle"])
    cond_lower = conditions.lower()
    is_rain = precip > 0 and any(k in cond_lower for k in ["rain", "drizzle", "shower"])
    is_storm = any(k in cond_lower for k in ["storm", "thunder"])
    next_hour_temp = round(temp + random.uniform(-1.5, 1.5), 1)
    next_hour_precip = max(0.0, round(precip + random.uniform(-2, 2), 2))

    return {
        "station_id": f"station_{city.replace(',', '_').replace(' ', '_')}",
        "timestamp": _rfc3339_utc_now(),
        "location": {
            "city": city.split(',')[0],
            "country": "FR",
            "latitude": round(random.uniform(42.0, 50.0), 4),  # Bornes approx France
            "longitude": round(random.uniform(-5.0, 8.0), 4),
        },
        "temperature": temp,
        "humidity": random.randint(30, 95),
        "pressure": round(random.uniform(980, 1040), 1),
        "wind_speed": round(random.uniform(0, 40), 1),
        "wind_direction": random.choice(["N", "NE", "E", "SE", "S", "SW", "W", "NW"]),
        "precipitation": precip,
        "weather_condition": conditions,
        "is_rain": int(is_rain),
        "is_storm": int(is_storm),
        "next_hour_temp": next_hour_temp,
        "next_hour_precip": next_hour_precip,
        "data_origin": "simulated"
    }

def create_kafka_producer():
    """Crée un producteur Kafka"""
    return KafkaProducer(
        bootstrap_servers=KAFKA_HOSTS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        max_block_ms=5000,
        linger_ms=100,
        retries=5,
        acks="all",
    )

def stream_weather_data(num_messages=10, delay_seconds=2, continuous=False):
    """Envoie des données météo vers Kafka.

    continuous = True permet de boucler indéfiniment (ignorer num_messages) jusqu'à Ctrl+C.
    """
    producer = create_kafka_producer()
    stop_flag = False

    def _handle_sig(signum, frame):
        nonlocal stop_flag
        logger.info("Signal reçu, arrêt gracieux...")
        stop_flag = True

    signal.signal(signal.SIGINT, _handle_sig)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, _handle_sig)

    sent = 0
    try:
        if continuous:
            logger.info(f"Mode continu: envoi sans fin vers '{KAFKA_TOPIC}' (intervalle {delay_seconds}s). Ctrl+C pour arrêter.")
            while not stop_flag:
                weather_data = generate_weather_data()
                future = producer.send(KAFKA_TOPIC, value=weather_data)
                future.get(timeout=10)
                sent += 1
                logger.info(
                    f"Message #{sent} envoyé - {weather_data['location']['city']} temp={weather_data['temperature']}°C origin={weather_data['data_origin']}"
                )
                # sommeil interrompu si signal
                for _ in range(int(delay_seconds * 10)):
                    if stop_flag:
                        break
                    time.sleep(0.1)
        else:
            logger.info(f"Envoi ponctuel de {num_messages} messages vers '{KAFKA_TOPIC}' (intervalle {delay_seconds}s)")
            for i in range(num_messages):
                if stop_flag:
                    break
                weather_data = generate_weather_data()
                future = producer.send(KAFKA_TOPIC, value=weather_data)
                future.get(timeout=10)
                logger.info(
                    f"Message {i+1}/{num_messages} envoyé - Station: {weather_data['station_id']}, Ville: {weather_data['location']['city']}, Temp: {weather_data['temperature']}°C, Origin: {weather_data.get('data_origin')}"
                )
                if i < num_messages - 1:
                    time.sleep(delay_seconds)
        logger.info("Fin d'envoi")
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi: {e}")
        raise
    finally:
        try:
            producer.flush()
            producer.close()
        except Exception:
            pass
        logger.info("Producteur Kafka fermé")

def parse_args():
    p = argparse.ArgumentParser(description="Producteur Kafka météo (API + simulation)")
    p.add_argument("--num", type=int, default=10, help="Nombre de messages (mode non continu)")
    p.add_argument("--interval", type=float, default=2.0, help="Intervalle secondes entre messages")
    p.add_argument("--continuous", action="store_true", help="Boucle infinie jusqu'à interruption")
    return p.parse_args()


if __name__ == "__main__":
    print("Producteur Kafka - Couche Speed")
    print("=" * 40)

    if not VISUAL_CROSSING_API_KEY or VISUAL_CROSSING_API_KEY == "YOUR_API_KEY_HERE":
        print("Clé API non configurée - utilisation de données simulées")
    else:
        print("Clé API configurée (clé chargée)")

    args = parse_args()
    stream_weather_data(num_messages=args.num, delay_seconds=args.interval, continuous=args.continuous)
