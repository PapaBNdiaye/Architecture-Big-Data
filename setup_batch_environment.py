#!/usr/bin/env python3
"""
Script de configuration pour l'environnement de traitement batch
Configure les variables d'environnement et vérifie les dépendances
"""

import os
import subprocess
import sys
import requests
import time
from typing import Dict, List

class BatchEnvironmentSetup:
    def __init__(self):
        self.services = {
            'hdfs-namenode': 'http://localhost:9870',
            'spark-master': 'http://localhost:9090',
            'airflow': 'http://localhost:8080',
            'kafka': 'localhost:9092'
        }
        
    def check_docker_compose(self) -> bool:
        """Vérifie que Docker Compose est disponible"""
        try:
            result = subprocess.run(['docker-compose', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✓ Docker Compose disponible: {result.stdout.strip()}")
                return True
            else:
                print("✗ Docker Compose non disponible")
                return False
        except FileNotFoundError:
            print("✗ Docker Compose non installé")
            return False
    
    def setup_environment_variables(self):
        """Configure les variables d'environnement nécessaires"""
        env_vars = {
            'VISUAL_CROSSING_API_KEY': 'VOTRE_API_KEY',
            'SPARK_HOME': '/opt/spark',
            'HADOOP_HOME': '/opt/hadoop',
            'JAVA_HOME': '/usr/lib/jvm/java-8-openjdk-amd64'
        }
        
        print("Configuration des variables d'environnement...")
        for key, default_value in env_vars.items():
            current_value = os.getenv(key, default_value)
            if current_value == default_value:
                print(f"⚠️  {key} = {default_value} (à configurer)")
            else:
                print(f"✓ {key} = {current_value}")
    
    def wait_for_service(self, service_name: str, url: str, timeout: int = 60) -> bool:
        """Attend qu'un service soit disponible"""
        print(f"Attente de {service_name}...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"✓ {service_name} est disponible")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(5)
        
        print(f"✗ {service_name} non disponible après {timeout}s")
        return False
    
    def check_services(self) -> Dict[str, bool]:
        """Vérifie la disponibilité de tous les services"""
        results = {}
        
        print("\n=== Vérification des services ===")
        
        for service, url in self.services.items():
            try:
                response = requests.get(url, timeout=10)
                results[service] = response.status_code == 200
                status = "✓" if results[service] else "✗"
                print(f"{status} {service}: {url}")
            except requests.exceptions.RequestException:
                results[service] = False
                print(f"✗ {service}: {url} (non accessible)")
        
        return results
    
    def create_hdfs_directories(self):
        """Crée les répertoires HDFS nécessaires"""
        print("\n=== Création des répertoires HDFS ===")
        
        directories = [
            '/weather_data',
            '/weather_data/raw',
            '/weather_data/batch',
            '/weather_data/processed'
        ]
        
        for directory in directories:
            try:
                # Commande pour créer le répertoire HDFS
                cmd = f"docker exec hdfs-namenode hdfs dfs -mkdir -p {directory}"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"✓ Répertoire créé: {directory}")
                else:
                    print(f"✗ Erreur création {directory}: {result.stderr}")
                    
            except Exception as e:
                print(f"✗ Erreur lors de la création de {directory}: {e}")
    
    def setup_airflow_variables(self):
        """Configure les variables Airflow"""
        print("\n=== Configuration des variables Airflow ===")
        
        variables = {
            'VISUAL_CROSSING_API_KEY': 'VOTRE_API_KEY',
            'HDFS_URL': 'hdfs://hdfs-namenode:9000',
            'SPARK_MASTER_URL': 'spark://spark-master:7077',
            'KAFKA_BOOTSTRAP_SERVERS': 'localhost:9092'
        }
        
        for key, value in variables.items():
            print(f"Variable Airflow: {key} = {value}")
            print("  (À configurer via l'interface Airflow ou CLI)")
    
    def run_health_checks(self):
        """Exécute les vérifications de santé du système"""
        print("\n=== Vérifications de santé ===")
        
        # Vérification HDFS
        try:
            cmd = "docker exec hdfs-namenode hdfs dfsadmin -report"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print("✓ HDFS cluster en bonne santé")
            else:
                print("✗ Problème avec le cluster HDFS")
        except Exception as e:
            print(f"✗ Erreur vérification HDFS: {e}")
        
        # Vérification Spark
        try:
            response = requests.get('http://localhost:9090', timeout=10)
            if response.status_code == 200:
                print("✓ Spark Master disponible")
            else:
                print("✗ Spark Master non accessible")
        except Exception as e:
            print(f"✗ Erreur vérification Spark: {e}")
    
    def generate_sample_config(self):
        """Génère un fichier de configuration d'exemple"""
        config_content = """# Configuration pour l'architecture Lambda - Traitement Batch
# Copiez ce fichier vers .env et modifiez les valeurs selon votre environnement

# API Visual Crossing
VISUAL_CROSSING_API_KEY=VOTRE_API_KEY_ICI

# Configuration HDFS
HDFS_NAMENODE_URL=hdfs://hdfs-namenode:9000
HDFS_WEB_URL=http://localhost:9870

# Configuration Spark
SPARK_MASTER_URL=spark://spark-master:7077
SPARK_WEB_URL=http://localhost:9090

# Configuration Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Configuration Airflow
AIRFLOW_HOME=/opt/airflow
AIRFLOW_DB_URL=postgresql+psycopg2://airflow:airflow@postgres:5432/airflow

# Répertoires HDFS pour les données météo
WEATHER_RAW_PATH=/weather_data/raw
WEATHER_BATCH_PATH=/weather_data/batch
WEATHER_PROCESSED_PATH=/weather_data/processed
"""
        
        with open('.env.example', 'w') as f:
            f.write(config_content)
        
        print("✓ Fichier de configuration d'exemple créé: .env.example")
    
    def run_setup(self):
        """Exécute la configuration complète"""
        print("=== Configuration de l'environnement de traitement batch ===\n")
        
        # Vérifications préliminaires
        if not self.check_docker_compose():
            print("Docker Compose requis pour continuer")
            return False
        
        # Configuration des variables d'environnement
        self.setup_environment_variables()
        
        # Génération du fichier de configuration
        self.generate_sample_config()
        
        # Instructions pour l'utilisateur
        print("\n=== Instructions de déploiement ===")
        print("1. Configurez votre clé API Visual Crossing:")
        print("   export VISUAL_CROSSING_API_KEY='votre_clé_api'")
        print("2. Démarrez les services:")
        print("   docker-compose up -d")
        print("3. Attendez que tous les services soient prêts (2-3 minutes)")
        print("4. Vérifiez les services:")
        print("   python setup_batch_environment.py --check-services")
        print("5. Créez les répertoires HDFS:")
        print("   python setup_batch_environment.py --setup-hdfs")
        print("6. Testez le traitement batch:")
        print("   python batch_processing.py")
        
        return True

def main():
    """Fonction principale"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Configuration de l\'environnement batch')
    parser.add_argument('--check-services', action='store_true', 
                       help='Vérifier la disponibilité des services')
    parser.add_argument('--setup-hdfs', action='store_true',
                       help='Configurer les répertoires HDFS')
    parser.add_argument('--health-check', action='store_true',
                       help='Exécuter les vérifications de santé')
    parser.add_argument('--full-setup', action='store_true',
                       help='Configuration complète')
    
    args = parser.parse_args()
    
    setup = BatchEnvironmentSetup()
    
    if args.check_services:
        setup.check_services()
    elif args.setup_hdfs:
        setup.create_hdfs_directories()
    elif args.health_check:
        setup.run_health_checks()
    elif args.full_setup:
        setup.run_setup()
    else:
        # Par défaut, exécuter la configuration complète
        setup.run_setup()

if __name__ == "__main__":
    main()
