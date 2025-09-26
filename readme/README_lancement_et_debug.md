# Guide de Lancement et Débogage
# Couche Speed - Pipeline de Traitement de Données en Temps Réel

## Vue d'ensemble

Ce projet implémente la couche Speed d'une architecture Lambda pour le traitement de données météorologiques en temps réel. Le pipeline ingère les données météo via Kafka, les traite avec Spark Streaming et stocke les résultats dans Cassandra.

## Composants de l'architecture

- **Apache Kafka** : Plateforme de streaming pour l'ingestion des données
- **Apache Spark Streaming** : Moteur de traitement de données en temps réel
- **Apache Cassandra** : Base de données distribuée pour le stockage
- **Docker** : Plateforme de conteneurisation pour l'orchestration des services

## Structure du projet

```
speed_layer/
├── docker-compose.yml          # Configuration des services Docker
├── kafka_producer.py           # Producteur de données météo
├── spark_streaming.py          # Job de traitement Spark Streaming
├── requirements.txt            # Dépendances Python
├── scripts/                    # Scripts d'automatisation
│   ├── start_pipeline.bat      # Script de démarrage Windows
│   ├── test_pipeline.bat       # Script de test Windows
│   ├── stop_pipeline.bat       # Script d'arrêt Windows
│   └── setup_speed_layer.sh    # Script de configuration Linux/Mac
└── README.md                   # (Ce fichier a été déplacé)
```

## Prérequis

- Docker et Docker Compose installés
- Python 3.9 ou supérieur
- Git (pour cloner le dépôt)

## Démarrage rapide

### 1. Configuration de l'environnement

```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 2. Démarrer les services

```bash
docker-compose up -d
```
Attendre l'initialisation des services (2-3 minutes).

### 3. Configurer Spark Streaming

```bash
docker cp spark_streaming.py speed_layer-spark-master-1:/opt/bitnami/spark/
docker exec speed_layer-spark-master-1 pip install cassandra-driver
docker exec -d speed_layer-spark-master-1 spark-submit \
  --packages com.datastax.spark:spark-cassandra-connector_2.12:3.4.1,org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1 \
  /opt/bitnami/spark/spark_streaming.py
```

### 4. Tester le pipeline

```bash
python kafka_producer.py
# Puis vérifier :
docker exec cassandra cqlsh -e "SELECT COUNT(*) FROM spark_streams.weather_data;"
```

## Flux de données

1. Génération / récupération de données météo → topic Kafka `weather_data`
2. Spark Streaming lit et transforme
3. Écriture dans Cassandra table `weather_data`
4. Requête directe possible via CQLSH

## Schéma des données

Topic / Table colonnes : station_id, city, temperature, timestamp

## Monitoring

- Kafka Control Center: http://localhost:9021
- Spark Master: http://localhost:9090
- Cassandra CLI: `docker exec -it cassandra cqlsh`

## Commandes utiles

```bash
# Compter les enregistrements
docker exec cassandra cqlsh -e "SELECT COUNT(*) FROM spark_streams.weather_data;"
# Voir un échantillon
docker exec cassandra cqlsh -e "SELECT station_id, city, temperature, timestamp FROM spark_streams.weather_data LIMIT 10;"
```

## Dépannage (extraits)

Broker unhealthy:
```bash
docker-compose restart broker
```
Pas de données : attendre quelques micro-batches (2-3 min) puis revérifier.

Spark absent : relancer spark-submit (voir plus haut).

Erreur NoBrokersAvailable : vérifier que les topics listent correctement.

Cassandra-driver manquant : installer dans le conteneur Spark.

## Nettoyage

```bash
docker-compose down -v
```

---
Document conservé pour référence rapide de lancement et debug bas niveau.
