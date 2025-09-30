#!/usr/bin/env python3
"""
Configuration des villes et paramètres API pour le traitement batch météo.

Ce module définit les villes à traiter et les paramètres de l'API Visual Crossing
pour la récupération des données météo.
"""

# Villes françaises principales
CITIES = [
    "Paris,FR",
    "Lyon,FR",
    "Marseille,FR"
]

# Paramètres de traitement
MAX_WORKERS = 3  # Nombre de villes traitées en parallèle

# Configuration API Visual Crossing
API_CONFIG = {
    'base_url': 'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline',
    'include': 'days',
    'contentType': 'json',
    # Variables météo récupérées
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
