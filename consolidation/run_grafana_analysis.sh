#!/bin/bash
echo "🌤️  ANALYSE MÉTÉO AVEC GRAFANA"
echo "==============================="

echo "📊 1. Exécution de l'analyse météo..."
docker exec -it spark-master spark-submit \
  --master spark://spark-master:7077 \
  //opt/spark/project/weather_analysis.py

echo ""
echo "📤 2. Export des données vers PostgreSQL..."
docker exec -it spark-master spark-submit \
  --master spark://spark-master:7077 \
  //opt/spark/project/export_to_postgres.py

echo ""
echo "🌐 3. Configuration de Grafana..."
# Installer requests dans le conteneur Grafana et exécuter le script
docker exec -it grafana bash -c "pip install requests && python -c \"
import requests
import json
import time

def wait_for_grafana():
    print('⏳ Attente de Grafana...')
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            response = requests.get('http://localhost:3000/api/health', timeout=5)
            if response.status_code == 200:
                print('✅ Grafana est disponible')
                return True
        except:
            pass
        time.sleep(2)
        print(f'   Tentative {attempt + 1}/{max_attempts}')
    print('❌ Grafana n\\'est pas disponible')
    return False

if wait_for_grafana():
    print('🎉 Grafana est prêt!')
    print('📊 Accédez à: http://localhost:3000')
    print('👤 Utilisateur: admin / Mot de passe: admin')
else:
    print('❌ Grafana n\\'est pas disponible')
\""

echo ""
echo "🎉 TERMINÉ!"
echo "📊 Grafana: http://localhost:3000 (admin/admin)"
echo "📈 Airflow: http://localhost:8080 (admin/admin)"
echo "🔍 HDFS: http://localhost:9871"
