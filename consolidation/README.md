# Architecture Lambda - Big Data

Ce projet implémente une architecture Lambda complète pour le traitement des données météo en temps réel et en batch.

## 🚀 Démarrage Rapide

### Option 1: Déploiement Automatisé (Recommandé)

```bash
# Exécuter le script d'automatisation complet
./deploy_and_run.sh
```

Ce script automatise tout le processus :
- ✅ Configuration de l'API Key Visual Crossing
- ✅ Démarrage des services Docker
- ✅ Installation des dépendances Python
- ✅ Configuration des permissions HDFS
- ✅ Exécution du traitement batch
- ✅ Vérification des données

### Option 2: Déploiement Manuel

```bash
# 1. Configuration de l'API Key
export VISUAL_CROSSING_API_KEY=BYYWRZR3C5BF2TQ3UER8KPTYJ

# 2. Démarrage des services
docker-compose up -d

# 3. Installation des dépendances
docker exec spark-master pip install -r /opt/spark/requirements_batch.txt
docker exec spark-worker pip install -r /opt/spark/requirements_batch.txt

# 4. Configuration HDFS
docker exec -it hdfs-namenode bash -c "hdfs dfs -mkdir -p /user/spark/weather/raw"
docker exec -it hdfs-namenode bash -c "hdfs dfs -chown -R spark:spark /user/spark"

# 5. Exécution du traitement batch
docker exec -it spark-master spark-submit \
  --master spark://spark-master:7077 \
  --py-files /opt/spark/project/config/cities_config.py \
  /opt/spark/project/batch_processing_local.py

# 6. Vérification des données
docker exec spark-master spark-submit \
  --master spark://spark-master:7077 \
  /opt/spark/project/count_data.py
```

## 🌐 Interfaces Web

Une fois les services démarrés, vous pouvez accéder aux interfaces suivantes :

- **HDFS Web UI**: http://localhost:9871
- **Spark Master UI**: http://localhost:9090  
- **Airflow UI**: http://localhost:8080
- **Kafka Control Center**: http://localhost:9021

## 📊 Visualisation des Données HDFS

### Via l'Interface Web
1. Ouvrez http://localhost:9871
2. Naviguez vers `/user/spark/weather/raw/`
3. Explorez les répertoires par timestamp

### Via les Commandes
```bash
# Lister les répertoires
docker exec hdfs-namenode hdfs dfs -ls /user/spark/weather/raw/

# Voir le contenu d'un répertoire spécifique
docker exec hdfs-namenode hdfs dfs -ls /user/spark/weather/raw/20250925_101201/

# Compter les données avec le script Python
docker exec spark-master spark-submit \
  --master spark://spark-master:7077 \
  /opt/spark/project/count_data.py
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Visual    │───▶│  Batch Processor │───▶│      HDFS      │
│   Crossing      │    │   (Spark)       │    │   (Stockage)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │     Airflow     │
                       │  (Orchestration) │
                       └─────────────────┘
```

## 📁 Structure des Données

Les données sont organisées dans HDFS comme suit :
```
/user/spark/weather/
├── raw/                    # Données brutes de l'API
│   ├── 20250925_101201/   # Timestamp d'exécution
│   │   ├── Paris_FR.parquet
│   │   ├── Lyon_FR.parquet
│   │   └── ...
└── batch/                  # Données agrégées (futur)
```

## 🔧 Dépannage

### Services non démarrés
```bash
# Vérifier le statut des conteneurs
docker-compose ps

# Redémarrer un service spécifique
docker-compose restart hdfs-namenode
```

### Problèmes de permissions HDFS
```bash
# Réinitialiser les permissions
docker exec -it hdfs-namenode bash -c "hdfs dfs -chown -R spark:spark /user/spark"
```

### Logs des services
```bash
# Voir les logs d'un service
docker logs hdfs-namenode
docker logs spark-master
```

## 📋 Prérequis

- Docker et Docker Compose
- Python 3.8+
- Clé API Visual Crossing (déjà configurée dans le script)

## 🎯 Fonctionnalités

- **Traitement Batch**: Récupération et traitement des données météo
- **Stockage Distribué**: HDFS pour la persistance des données
- **Orchestration**: Airflow pour la planification des tâches
- **Streaming**: Kafka pour le traitement en temps réel
- **Monitoring**: Interfaces web pour le suivi des services
