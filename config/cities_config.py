#!/usr/bin/env python3
"""
Configuration simple des villes pour le traitement batch météo
"""

# Villes françaises principales (2 villes pour rester dans le quota de 1000 requêtes/jour)
CITIES = [
    "Paris,FR",
    "Lyon,FR"
]

# Paramètres de traitement
MAX_WORKERS = 3  # Nombre de villes traitées en parallèle

# Configuration API Visual Crossing - Variables essentielles pour analyses météo
API_CONFIG = {
    'base_url': 'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline',
    'include': 'days',  # Simplifié pour éviter les problèmes
    'contentType': 'json',  # Changé de 'csv' à 'json' pour correspondre au parsing
    # Variables essentielles pour analyses météo
    'elements': [
        'datetime',           # Date et heure
        'address',            # Adresse
        'latitude',           # Latitude
        'longitude',          # Longitude
        'temp',              # Température actuelle
        'tempmax',           # Température maximale
        'tempmin',           # Température minimale
        'humidity',          # Humidité relative
        'dew',               # Point de rosée
        'precip',            # Précipitations
        'preciptype',        # Type de précipitations
        'pressure',          # Pression atmosphérique
        'windspeed',         # Vitesse du vent
        'windgust',          # Rafales de vent
        'winddir',           # Direction du vent
        'cloudcover',        # Couverture nuageuse
        'visibility'         # Visibilité
    ]
}

def get_api_elements():
    """Retourne la liste des éléments API sous forme de string"""
    return ','.join(API_CONFIG['elements'])

def get_api_params():
    """Retourne les paramètres API complets"""
    return {
        'include': API_CONFIG['include'],
        'elements': get_api_elements(),
        'contentType': API_CONFIG['contentType']
    }
