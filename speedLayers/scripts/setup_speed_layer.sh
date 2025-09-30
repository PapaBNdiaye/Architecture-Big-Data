#!/bin/bash
# Setup automatique de la Couche Speed - Pipeline Lambda

echo "Setup Couche Speed - Pipeline Lambda"
echo "=========================================="

# Fonction pour vérifier le succès
check_success() {
    if [ $? -eq 0 ]; then
    echo "OK: $1"
    else
    echo "ERREUR: $1"
        exit 1
    fi
}

# 1. Démarrer les services Docker
echo "Demarrage des services..."
docker-compose up -d
check_success "Services démarrés"

# 2. Attendre que les services soient prêts
echo "Attente des services (60 secondes)..."
sleep 60

# 3. Configurer Spark Streaming
echo "Configuration de Spark Streaming..."
docker cp spark_streaming.py spark-master:/opt/bitnami/spark/
check_success "Script Spark copié"

docker exec spark-master pip install cassandra-driver > /dev/null 2>&1
check_success "Dépendances Spark installées"

# 4. Lancer Spark Streaming
echo "Lancement de Spark Streaming..."
docker exec -d spark-master spark-submit \
  --packages com.datastax.spark:spark-cassandra-connector_2.12:3.4.1,org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1 \
  /opt/bitnami/spark/spark_streaming.py
check_success "Spark Streaming lancé"

# 5. Setup environnement Python
if [ ! -d "venv" ]; then
    echo "Creation environnement virtuel..."
    python3 -m venv venv
    check_success "Environnement virtuel créé"
fi

echo "Installation dependances..."
source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1
check_success "Dépendances installées"

# 6. Test du pipeline
echo "Test de la Couche Speed..."
sleep 30
python kafka_producer.py

# 7. Vérification
echo "Verification des donnees..."
sleep 10
docker exec cassandra cqlsh -e "SELECT COUNT(*) FROM spark_streams.weather_data;"

echo ""
echo "COUCHE SPEED OPERATIONNELLE"
echo "=========================================="
echo "Interfaces :"
echo "• Kafka Control Center: http://localhost:9021"
echo "• Spark Master UI: http://localhost:9090"
echo "• Cassandra CLI: docker exec -it cassandra cqlsh"
