# Architecture Lambda - Pipeline de Données Météo

Ce projet implémente une architecture Lambda complète pour le traitement et l'analyse de données météorologiques en temps réel et par batch.

## Vue d'ensemble de l'architecture

L'architecture Lambda se compose de trois couches principales :

```
┌─────────────────────────────────────────────────────────────────┐
│                      ARCHITECTURE LAMBDA                         │
└─────────────────────────────────────────────────────────────────┘
                                │
                    ┌───────────┴────────────┐
                    │                        │
              ┌─────▼─────┐           ┌─────▼─────┐
              │   BATCH   │           │   SPEED   │
              │   LAYER   │           │   LAYER   │
              └─────┬─────┘           └─────┬─────┘
                    │                        │
                    └───────────┬────────────┘
                                │
                          ┌─────▼─────┐
                          │  SERVING  │
                          │   LAYER   │
                          └───────────┘
```

### Couche Batch (Batch Layer)
- **Collecte** : API Visual Crossing Weather
- **Traitement** : Apache Spark
- **Stockage** : HDFS (Hadoop Distributed File System)
- **Export** : PostgreSQL pour visualisation
- **Orchestration** : Apache Airflow

### Couche Speed (Speed Layer)
- **Ingestion** : Apache Kafka
- **Collection** : Telegraf
- **Traitement** : Spark Streaming (optionnel)
- **Stockage** : InfluxDB (time-series) + Cassandra
- **Streaming** : Kafka → Telegraf → InfluxDB

### Couche Serving (Serving Layer)
- **Visualisation** : Grafana (dashboards temps réel + batch)
- **API** : FastAPI (backend pour frontend React)
- **Frontend** : Interface React avec filtres et visualisations

## Prérequis

### Logiciels requis
- Docker Desktop (version 20.10+)
- Docker Compose (version 2.0+)
- Python 3.9+ (pour tests locaux)
- Git
- Au moins 8 GB de RAM disponible
- 20 GB d'espace disque

### Clé API
- Compte Visual Crossing Weather API  : https://www.visualcrossing.com/weather-api/

## Installation et déploiement

### 1. Préparer l'environnement

```bash
# Cloner le projet (si nécessaire)
cd consolidation

# Configurer la clé API
cp env.example .env
# Éditer .env et ajouter votre VISUAL_CROSSING_API_KEY
```

### 2. Démarrer l'architecture complète

```bash
# Démarrer tous les services
docker-compose up -d

# Vérifier le statut des services
docker-compose ps
```

Temps d'initialisation estimé : 3-5 minutes pour tous les services.

### 3. Vérifier les services

```bash
# Logs en temps réel
docker-compose logs -f

# Logs d'un service spécifique
docker logs airflow-webserver
docker logs grafana
docker logs spark-master
```

## Accès aux interfaces

Une fois tous les services démarrés :

| Service | URL | Credentials | Description |
|---------|-----|-------------|-------------|
| **Airflow** | http://localhost:8080 | admin/admin | Orchestration des workflows |
| **Grafana** | http://localhost:3000 | admin/admin12345 | Visualisation temps réel et batch |
| **Spark Master** | http://localhost:9090 | - | Interface Spark |
| **Kafka Control Center** | http://localhost:9021 | - | Monitoring Kafka |
| **HDFS NameNode** | http://localhost:9871 | - | Interface HDFS |
| **InfluxDB** | http://localhost:8086 | admin/admin12345 | Time-series database |
| **API FastAPI** | http://localhost:8000 | - | API REST backend |

## Utilisation

### Lancer le traitement batch

1. Accéder à Airflow : http://localhost:8080
2. Activer le DAG `weather_batch_processing`
3. Déclencher manuellement ou attendre l'exécution planifiée
4. Vérifier les logs dans l'interface Airflow

### Lancer le streaming temps réel

```bash
# Dans un terminal
cd consolidation
python scripts/kafka_producer.py --continuous --interval 60
```

Ou via Airflow :
1. Activer le DAG `kafka_weather_stream`
2. Le producteur Kafka enverra des données en continu

### Visualiser les données

#### Grafana - Dashboards
1. Accéder à http://localhost:3000
2. Login : admin/admin12345
3. Dashboards disponibles :
   - **Speed Layer Dashboard** : Données temps réel (InfluxDB)
   - **Batch Layer Dashboard** : Analyses historiques (PostgreSQL)

#### Données HDFS

```bash
# Lister les fichiers HDFS
docker exec hdfs-namenode hdfs dfs -ls /user/spark/weather/raw

# Compter les enregistrements
docker exec spark-master python /opt/spark/scripts/count_data.py
```

#### Données PostgreSQL

```bash
# Se connecter à PostgreSQL
docker exec -it postgres-batch psql -U weather -d weather_db

# Requête exemple
SELECT city, AVG(temp) as avg_temp 
FROM weather_data 
GROUP BY city;
```

#### Données InfluxDB

```bash
# Query exemple via CLI
docker exec influxdb influx query 'from(bucket:"speed_bucket") |> range(start:-1h)'
```

## Architecture des données

### Flux Batch

```
API Visual Crossing → Spark → HDFS → Export PostgreSQL → Grafana
                         ↓
                    Analyses Spark
                         ↓
                    Résultats HDFS
```

### Flux Speed

```
API Visual Crossing → Kafka Producer → Kafka Topic → Telegraf → InfluxDB → Grafana
                                           ↓
                                    Spark Streaming
                                           ↓
                                       Cassandra
```

### Schéma des données

#### Topic Kafka : `weather_data_v2`
```json
{
  "station_id": "station_Paris_FR",
  "timestamp": "2025-09-30T12:00:00Z",
  "location": {
    "city": "Paris",
    "country": "FR",
    "latitude": 48.8566,
    "longitude": 2.3522
  },
  "temperature": 18.5,
  "humidity": 65,
  "pressure": 1013.2,
  "wind_speed": 12.3,
  "wind_direction": "NW",
  "precipitation": 0.0,
  "weather_condition": "Partly Cloudy",
  "is_rain": 0,
  "is_storm": 0,
  "next_hour_temp": 18.2,
  "next_hour_precip": 0.0,
  "data_origin": "api"
}
```

## Commandes utiles

### Docker

```bash
# Arrêter tous les services
docker-compose down

# Arrêter et supprimer les volumes (ATTENTION: perte de données)
docker-compose down -v

# Redémarrer un service
docker-compose restart spark-master

# Voir les ressources utilisées
docker stats
```

### Airflow

```bash
# Lister les DAGs
docker exec airflow-webserver airflow dags list

# Déclencher un DAG manuellement
docker exec airflow-webserver airflow dags trigger weather_batch_processing

# Voir les logs d'une tâche
docker exec airflow-webserver airflow tasks logs weather_batch_processing process_batch_data 2025-09-30
```

### Kafka

```bash
# Lister les topics
docker exec broker kafka-topics --bootstrap-server localhost:9092 --list

# Consommer des messages
docker exec broker kafka-console-consumer --bootstrap-server localhost:9092 --topic weather_data_v2 --from-beginning --max-messages 10

# Créer un topic
docker exec broker kafka-topics --bootstrap-server localhost:9092 --create --topic test_topic --partitions 1 --replication-factor 1
```

### HDFS

```bash
# Lister le contenu
docker exec hdfs-namenode hdfs dfs -ls /user/spark/weather

# Copier un fichier vers HDFS
docker exec hdfs-namenode hdfs dfs -put /local/path /hdfs/path

# Récupérer un fichier depuis HDFS
docker exec hdfs-namenode hdfs dfs -get /hdfs/path /local/path

# Voir l'espace disque
docker exec hdfs-namenode hdfs dfsadmin -report
```

### Cassandra

```bash
# Se connecter à CQLSH
docker exec -it cassandra cqlsh

# Requêtes CQL
SELECT COUNT(*) FROM spark_streams.weather_data;
SELECT * FROM spark_streams.weather_data LIMIT 10;
```

## Dépannage

### Services ne démarrent pas

```bash
# Vérifier les logs
docker-compose logs [nom_du_service]

# Vérifier les ressources
docker stats

# Nettoyer et redémarrer
docker-compose down -v
docker system prune -a
docker-compose up -d
```

### Problèmes Kafka

```bash
# Vérifier la santé du broker
docker exec broker kafka-broker-api-versions --bootstrap-server localhost:9092

# Redémarrer Kafka
docker-compose restart zookeeper broker
```

### Problèmes HDFS

```bash
# Vérifier le statut
docker exec hdfs-namenode hdfs dfsadmin -report

# Mode sans échec
docker exec hdfs-namenode hdfs dfsadmin -safemode leave
```

### Problèmes Airflow

```bash
# Réinitialiser la base de données
docker exec airflow-webserver airflow db reset

# Vérifier la configuration
docker exec airflow-webserver airflow config list
```

## Monitoring et métriques

### Métriques disponibles dans Grafana

#### Speed Layer (InfluxDB)
- Température en temps réel par ville
- Humidité et pression atmosphérique
- Vitesse et direction du vent
- Précipitations
- Indicateurs pluie/orage
- Heartbeat du pipeline
- Fraîcheur des données

#### Batch Layer (PostgreSQL)
- Moyennes mensuelles de température
- Totaux de précipitations
- Analyses de tendances
- Comparaisons entre villes
- Amplitude thermique
- Statistiques agrégées

## Structure du projet

```
consolidation/
├── docker-compose.yml           # Orchestration complète
├── requirements.txt             # Dépendances Python
├── env.example                  # Template configuration
│
├── dags/                        # DAGs Airflow
│   ├── weather_batch_dag.py     # Traitement batch
│   └── kafka_stream.py          # Streaming Kafka
│
├── scripts/                     # Scripts Python
│   ├── batch_processing_local.py    # Collecte API + HDFS
│   ├── weather_analysis.py          # Analyses météo
│   ├── export_to_postgres.py        # Export vers PostgreSQL
│   ├── count_data.py                # Utilitaire comptage
│   ├── kafka_producer.py            # Producteur Kafka
│   └── spark_streaming.py           # Spark Streaming
│
├── configs/                     # Configurations
│   └── cities_config.py         # Liste des villes
│
├── telegraf/                    # Configuration Telegraf
│   └── telegraf.conf
│
├── grafana-provisioning/        # Grafana auto-config
│   ├── datasources/             # Sources de données
│   └── dashboards/              # Dashboards JSON
│
├── frontend/                    # API et Frontend
│   ├── api_server.py            # FastAPI backend
│   ├── Dockerfile.api           # Image Docker
│   └── batch_processing_local.py
│
└── README.md                    # Ce fichier
```

## Technologies utilisées

### Batch Layer
- **Apache Spark 3.4** : Traitement distribué
- **HDFS** : Stockage distribué
- **Apache Airflow 2.6** : Orchestration
- **PostgreSQL 14** : Export pour visualisation

### Speed Layer
- **Apache Kafka** : Streaming de données
- **Telegraf 1.30** : Collection de métriques
- **InfluxDB 2.7** : Base de données time-series
- **Apache Cassandra** : Stockage distribué (optionnel)

### Serving Layer
- **Grafana 10.4** : Visualisation
- **FastAPI** : API REST
- **React** : Interface utilisateur

### Infrastructure
- **Docker & Docker Compose** : Conteneurisation
- **Python 3.9** : Scripts et DAGs

## Sécurité

### Recommandations pour la production
- Changer tous les mots de passe par défaut
- Utiliser des secrets Docker pour les credentials
- Activer SSL/TLS pour les communications
- Mettre en place un pare-feu
- Configurer l'authentification Kafka
- Utiliser des tokens rotatifs pour InfluxDB
- Restreindre les accès réseau

## Performance

### Optimisations possibles
- Augmenter les workers Spark
- Ajuster la mémoire des services
- Configurer le partitionnement Kafka
- Optimiser les requêtes Spark
- Mettre en place du caching
- Utiliser un LoadBalancer

## Maintenance

### Sauvegarde des données

```bash
# Sauvegarder les volumes Docker
docker run --rm --volumes-from postgres-batch -v $(pwd)/backup:/backup ubuntu tar cvf /backup/postgres.tar /var/lib/postgresql/data

# Sauvegarder HDFS
docker exec hdfs-namenode hdfs dfs -get /user/spark/weather /backup/hdfs
```

### Nettoyage régulier

```bash
# Nettoyer les logs Docker
docker system prune -a

# Nettoyer les données anciennes InfluxDB
# Via l'interface InfluxDB ou tâches de rétention automatique
```

## Support et documentation

- **Airflow** : https://airflow.apache.org/docs/
- **Spark** : https://spark.apache.org/docs/latest/
- **Kafka** : https://kafka.apache.org/documentation/
- **Grafana** : https://grafana.com/docs/
- **InfluxDB** : https://docs.influxdata.com/
- **Docker** : https://docs.docker.com/

## Licence

Projet académique - Architecture Lambda pour le traitement de données météorologiques.
