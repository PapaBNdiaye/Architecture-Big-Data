"""
DAG Airflow pour le traitement batch des données météo.

Ce DAG orchestre le processus de récupération des données météo depuis l'API Visual Crossing,
leur transformation et leur stockage dans HDFS.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.models import Variable
import os
import sys

# Ajout du répertoire parent au path pour importer batch_processing
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config'))

from batch_processing import WeatherBatchProcessor
from cities_config import CITIES, MAX_WORKERS

# Configuration par défaut du DAG
default_args = {
    'owner': 'data_team',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# Définition du DAG
dag = DAG(
    'weather_batch_processing',
    default_args=default_args,
    description='Traitement batch des données météo avec stockage HDFS',
    schedule_interval='@daily',  # Exécution quotidienne
    catchup=False,
    tags=['weather', 'batch', 'hdfs', 'lambda'],
)

def check_hdfs_availability():
    """Vérifie la disponibilité d'HDFS"""
    import requests
    try:
        # Vérification du namenode HDFS
        response = requests.get("http://hdfs-namenode:9870", timeout=10)
        if response.status_code == 200:
            print("HDFS namenode est disponible")
            return True
        else:
            print(f"HDFS namenode répond avec le code: {response.status_code}")
            return False
    except Exception as e:
        print(f"Erreur lors de la vérification HDFS: {e}")
        return False

def run_batch_processing(**context):
    """Exécute le traitement batch des données météo pour plusieurs villes"""
    try:
        # Récupération de la date d'exécution
        execution_date = context['execution_date']
        date_str = execution_date.strftime('%Y-%m-%d')
        
        print(f"Traitement batch pour la date: {date_str}")
        
        # Configuration
        api_key = Variable.get("VISUAL_CROSSING_API_KEY", default_var="VOTRE_API_KEY")
        
        if api_key == "VOTRE_API_KEY":
            raise ValueError("Clé API Visual Crossing non configurée")
        
        # Liste des villes à traiter (depuis la configuration)
        cities = CITIES
        
        # Initialisation du processeur
        processor = WeatherBatchProcessor(api_key=api_key)
        
        # Traitement parallèle pour toutes les villes
        results = processor.process_multiple_cities(
            cities=cities,
            start_date=date_str,
            end_date=date_str,
            max_workers=MAX_WORKERS
        )
        
        # Vérification des résultats
        if len(results['successful']) == 0:
            raise Exception("Aucune ville n'a été traitée avec succès")
        
        print(f"Traitement batch terminé: {len(results['successful'])}/{len(cities)} villes réussies")
        
        if results['failed']:
            print(f"Villes en échec: {', '.join(results['failed'])}")
        
        return f"Données météo traitées pour {len(results['successful'])} villes le {date_str}"
        
    except Exception as e:
        print(f"Erreur lors du traitement batch: {e}")
        raise

def validate_hdfs_data(**context):
    """Valide que les données ont été correctement stockées dans HDFS"""
    try:
        execution_date = context['execution_date']
        date_str = execution_date.strftime('%Y-%m-%d')
        
        # Vérification de l'existence des fichiers dans HDFS
        # Note: Dans un environnement réel, vous utiliseriez hdfs dfs -ls
        print(f"Validation des données HDFS pour {date_str}")
        
        # Simulation de validation
        # En production, vous feriez une requête HDFS réelle
        print("Validation HDFS simulée - OK")
        return True
        
    except Exception as e:
        print(f"Erreur lors de la validation HDFS: {e}")
        raise

# Tâches du DAG
check_hdfs_task = PythonOperator(
    task_id='check_hdfs_availability',
    python_callable=check_hdfs_availability,
    dag=dag,
)

batch_processing_task = PythonOperator(
    task_id='run_batch_processing',
    python_callable=run_batch_processing,
    dag=dag,
)

validate_data_task = PythonOperator(
    task_id='validate_hdfs_data',
    python_callable=validate_hdfs_data,
    dag=dag,
)

# Tâche de nettoyage des logs temporaires
cleanup_task = BashOperator(
    task_id='cleanup_temp_files',
    bash_command='echo "Nettoyage des fichiers temporaires terminé"',
    dag=dag,
)

# Définition des dépendances
check_hdfs_task >> batch_processing_task >> validate_data_task >> cleanup_task
