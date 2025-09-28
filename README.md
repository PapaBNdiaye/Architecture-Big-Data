
# Architecture Big Data - Dashboard Météo

Ce projet est une démonstration complète d'une architecture Lambda pour l'analyse de données météorologiques en batch, avec un dashboard React moderne.

## Sommaire
- [Fonctionnalités](#fonctionnalités)
- [Architecture](#architecture)
- [Installation](#installation)
- [Utilisation](#utilisation)
- [Tests](#tests)
- [Structure du projet](#structure-du-projet)
- [Technologies](#technologies)
- [Auteurs](#auteurs)

---

## Fonctionnalités
- **Dashboard interactif** : Visualisation des données météo (température, précipitations, humidité, vent) pour plusieurs villes
- **Filtres avancés** : Sélection des villes, métriques, période, granularité, agrégation
- **Graphiques dynamiques** : 4 graphiques (Température, Précipitations, Humidité, Vent) filtrables
- **Tableau paginé** : Résultats détaillés, pagination 5 par page
- **Carte interactive** : Visualisation géographique des villes
- **Backend FastAPI** : API batch, intégration Visual Crossing, simulation Spark/HDFS
- **Docker Compose** : Orchestration complète (API, Spark, HDFS, Airflow, etc.)
- **Tests automatisés** : Scripts pour valider l'API et le frontend

---

## Architecture
- **Frontend** : React + Ant Design + Recharts + Leaflet
- **Backend** : FastAPI (Python), intégration API Visual Crossing
- **Batch** : Simulation Spark/HDFS via API
- **Orchestration** : Docker Compose (Kafka, Spark, HDFS, Airflow, Postgres, etc.)

Schéma :
```
[React Dashboard] <-> [FastAPI] <-> [Visual Crossing API]
																 |
																 +--[Spark, HDFS, Airflow, Kafka, etc.]
```

---

## Installation

### 1. Prérequis
- Docker & Docker Compose
- Node.js & npm
- Python 3.10+
- Clé API Visual Crossing (gratuite sur https://www.visualcrossing.com/)

### 2. Cloner le projet
```
git clone https://github.com/PapaBNdiaye/Architecture-Big-Data.git
cd Architecture-Big-Data
```

### 3. Configurer l'environnement
- Copier `.env.example` vers `.env` dans `frontend-filter/` et renseigner la clé API
- Vérifier les variables dans `docker-compose.yml` et `config/`

### 4. Lancer les services
```
docker-compose up --build
```

### 5. Lancer le frontend
```
cd frontend-filter
npm install
npm run dev
```

---

## Utilisation
- Accéder au dashboard : [http://localhost:5173](http://localhost:5173)
- Configurer les filtres (villes, dates, métriques)
- Lancer la requête : les données sont traitées et affichées
- Utiliser les filtres graphiques pour personnaliser l'affichage
- Naviguer dans le tableau paginé et la carte interactive

---

## Tests
- **API** :
	- `python test_api.py` (ou `./test_api.ps1` sous Windows)
- **Frontend** :
	- `./test_frontend.ps1` (Windows)
- **Lint/Build** :
	- `npm run lint` / `npm run build` dans `frontend-filter/`

---

## Structure du projet
```
api_server.py                # Backend FastAPI principal
frontend-filter/             # Frontend React
	└─ src/components/         # Composants UI et graphiques
	└─ src/pages/              # Pages principales
	└─ src/types.ts            # Types TypeScript
	└─ package.json            # Dépendances frontend
config/                      # Config API, villes, etc.
docker-compose.yml           # Orchestration multi-services
requirements.txt             # Dépendances Python
README.md                    # Ce fichier
```

---

## Technologies
- **React, TypeScript, Ant Design, Recharts, Leaflet**
- **FastAPI, Python, requests**
- **Docker, Docker Compose**
- **Spark, HDFS, Airflow, Kafka, Postgres**

---

## Auteurs
- PapaBNdiaye
- Alexa (utilisateur)
- GitHub Copilot (assistant IA)

---

## Licence
MIT

---

## Liens utiles
- [Visual Crossing API](https://www.visualcrossing.com/)
- [Ant Design](https://ant.design/)
- [Recharts](https://recharts.org/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Docker](https://www.docker.com/)
