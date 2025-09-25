#!/bin/bash

# Script d'automatisation pour le déploiement et l'exécution du traitement batch
# Architecture Lambda - Couche Batch

set -e  # Arrêter le script en cas d'erreur

echo "🚀 Démarrage de l'automatisation du traitement batch..."
echo "=================================================="

# Configuration de l'API Key
echo "📝 Configuration de l'API Key Visual Crossing..."
export VISUAL_CROSSING_API_KEY="votre_clé_api"

# Démarrage des services Docker
echo "🐳 Démarrage des services Docker..."
docker-compose up -d

# Attendre que les services soient prêts
echo "⏳ Attente du démarrage des services (30 secondes)..."
sleep 30

# Installation des dépendances Python dans les conteneurs Spark
echo "📦 Installation des dépendances Python..."
echo "  - Installation dans spark-master..."
docker exec spark-master pip install -r //opt/spark/requirements_batch.txt

echo "  - Installation dans spark-worker..."
docker exec spark-worker pip install -r //opt/spark/requirements_batch.txt

# Configuration des permissions HDFS
echo "🔐 Configuration des permissions HDFS..."
echo "  - Suppression des anciens répertoires weather/raw..."
docker exec -it hdfs-namenode bash -c "hdfs dfs -rm -r -f /user/spark/weather/raw" || echo "    (Aucun ancien répertoire à supprimer)"

echo "  - Création du répertoire weather/raw..."
docker exec -it hdfs-namenode bash -c "hdfs dfs -mkdir -p /user/spark/weather/raw"

echo "  - Attribution des permissions à spark:spark..."
docker exec -it hdfs-namenode bash -c "hdfs dfs -chown -R spark:spark /user/spark"

# Attendre que HDFS soit complètement initialisé
echo "⏳ Attente de l'initialisation complète de HDFS (15 secondes)..."
sleep 15

# Exécution du traitement batch
echo "⚡ Exécution du traitement batch..."
docker exec -it spark-master spark-submit \
  --master spark://spark-master:7077 \
  --py-files //opt/spark/project/config/cities_config.py \
  //opt/spark/project/batch_processing_local.py

# Attendre la fin du traitement
echo "⏳ Attente de la fin du traitement (10 secondes)..."
sleep 10

# Vérification du contenu HDFS
echo "🔍 Vérification du contenu HDFS..."
echo "  - Liste des répertoires dans /user/spark/weather/raw/..."
docker exec hdfs-namenode bash -c "hdfs dfs -ls /user/spark/weather/raw/"

# Trouver le répertoire le plus récent
echo "  - Recherche du répertoire le plus récent..."
LATEST_DIR=$(docker exec hdfs-namenode bash -c "hdfs dfs -ls /user/spark/weather/raw/ | grep "2025" | tail -1 | awk '{print $8}' | xargs basename")
echo "  - Répertoire trouvé: $LATEST_DIR"

# Exécution du script de comptage avec le bon chemin
echo "📊 Exécution du script de comptage des données..."
docker exec spark-master spark-submit \
  --master spark://spark-master:7077 \
  //opt/spark/project/count_data.py

echo ""
echo "✅ Traitement terminé avec succès!"
echo "=================================================="
echo "🌐 Interfaces disponibles:"
echo "  - HDFS Web UI: http://localhost:9871"
echo "  - Spark Master UI: http://localhost:9090"
echo "  - Airflow UI: http://localhost:8080"
echo "  - Kafka Control Center: http://localhost:9021"
echo ""
echo "📁 Données stockées dans HDFS: /user/spark/weather/raw/$LATEST_DIR"
echo "🔍 Pour voir les données: docker exec hdfs-namenode bash -c 'hdfs dfs -ls /user/spark/weather/raw/$LATEST_DIR'"
