from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
import time
import os
from datetime import datetime, timedelta
import subprocess
import json
import requests
import sys
from collections import defaultdict

# Import config
sys.path.append(os.path.join(os.path.dirname(__file__), "config"))
from cities_config import API_CONFIG, get_api_params

API_KEY = os.getenv("VISUAL_CROSSING_API_KEY", "VOTRE_API_KEY")
BASE_URL = API_CONFIG['base_url']

app = FastAPI(title="Weather Batch API", version="1.0.0")

# Configuration CORS pour le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
AIRFLOW_BASE_URL = os.getenv("AIRFLOW_BASE_URL", "http://localhost:8080")
HDFS_BASE_URL = os.getenv("HDFS_BASE_URL", "http://localhost:9870")

# Stockage temporaire des tâches (en production, utiliser Redis ou DB)
tasks = {}

class RunPayload(BaseModel):
    locations: List[str]
    startDate: str
    endDate: str
    granularity: str = "days"
    metrics: List[str]
    agg: str = "avg_by_month"

class TaskStatus(BaseModel):
    state: str  # PENDING, RUNNING, SUCCESS, FAILURE

class DataRow(BaseModel):
    metric_date: str
    location: str
    metric_name: str
    metric_value: float
    source: str = "visualcrossing"

# Fonction pour récupérer les données météo
def fetch_city_weather(city, start_date="2025-01-01", end_date="2025-01-10"):
    max_retries = 3
    base_delay = 5
    
    for attempt in range(max_retries):
        try:
            url = f"{BASE_URL}/{city}/{start_date}/{end_date}"
            params = get_api_params()
            params["key"] = API_KEY

            print(f"Récupération des données pour {city} (tentative {attempt + 1}/{max_retries})")
            
            # Délai progressif entre les tentatives
            if attempt > 0:
                delay = base_delay * (2 ** attempt)
                print(f"Attente de {delay} secondes avant la tentative {attempt + 1}...")
                time.sleep(delay)
            else:
                time.sleep(2)
            
            response = requests.get(url, params=params, timeout=30)
            print(f"Status {response.status_code} pour {city}")

            if response.status_code == 429:
                if attempt < max_retries - 1:
                    print(f"Limite de taux atteinte pour {city}, nouvelle tentative dans {base_delay * (2 ** attempt)} secondes...")
                    continue
                else:
                    print(f"Limite de taux persistante pour {city} après {max_retries} tentatives")
                    return []

            response.raise_for_status()
            data = response.json()
            days = data.get("days", [])

            print(f"{city}: {len(days)} jours de données reçus")

            results = []
            for d in days:
                results.append({
                    "city": city,
                    "date": d.get("datetime"),
                    "temp": d.get("temp"),
                    "humidity": d.get("humidity"),
                    "pressure": d.get("pressure"),
                    "windspeed": d.get("windspeed"),
                    "precip": d.get("precip")
                })
            return results

        except Exception as e:
            print(f"Erreur pour {city} (tentative {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                return []
            continue
    
    return []

@app.get("/")
async def root():
    return {"message": "Weather Batch API", "version": "1.0.0"}

@app.post("/run")
async def run_query(payload: RunPayload, background_tasks: BackgroundTasks):
    """Lance une requête de traitement batch"""
    task_id = str(uuid.uuid4())

    # Stocker la tâche
    tasks[task_id] = {
        "status": "PENDING",
        "payload": payload.dict(),
        "created_at": datetime.now(),
        "result": None
    }

    # Lancer le traitement en arrière-plan
    background_tasks.add_task(process_batch_request, task_id, payload)

    return {"task_id": task_id}

@app.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """Récupère le statut d'une tâche"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = tasks[task_id]

    # Si la tâche est terminée, retourner le statut
    if task["status"] in ["SUCCESS", "FAILURE"]:
        return TaskStatus(state=task["status"])

    # Vérifier si la tâche Airflow associée est terminée
    try:
        # Ici on simule la vérification du statut Airflow
        # En production, interroger l'API Airflow
        if task["status"] == "PENDING":
            task["status"] = "RUNNING"

        # Simuler un traitement réussi après quelques secondes
        if (datetime.now() - task["created_at"]).seconds > 30:
            task["status"] = "SUCCESS"
            # Générer des données de test (temporaire)
            task["result"] = []

    except Exception as e:
        task["status"] = "FAILURE"
        print(f"Error checking task status: {e}")

    return TaskStatus(state=task["status"])

@app.get("/fetch/{task_id}")
async def fetch_results(task_id: str):
    """Récupère les résultats d'une tâche terminée"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = tasks[task_id]

    if task["status"] != "SUCCESS":
        raise HTTPException(status_code=400, detail="Task not completed")

    if not task["result"]:
        raise HTTPException(status_code=404, detail="No results available")

    return {"data": task["result"]}

def process_batch_request(task_id: str, payload: RunPayload):
    """Traite la requête batch en arrière-plan"""
    try:
        print(f"Traitement de la requête batch {task_id}")
        print(f"Payload: {payload}")

        # Ici, en production, on déclencherait le DAG Airflow
        # Pour l'instant, on récupère les données réelles

        # Attendre un peu pour simuler le traitement
        time.sleep(3)

        # Générer des résultats réels
        results = generate_real_results(payload.dict())

        # Mettre à jour la tâche
        tasks[task_id]["status"] = "SUCCESS"
        tasks[task_id]["result"] = results

        print(f"Traitement batch terminé pour la tâche {task_id}")

    except Exception as e:
        print(f"Erreur lors du traitement de la requête batch {task_id}: {e}")
        tasks[task_id]["status"] = "FAILURE"

def generate_real_results(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Génère des données réelles depuis l'API Visual Crossing"""
    results = []
    locations = payload.get("locations", ["Paris,FR"])
    metrics = payload.get("metrics", ["temp", "precip"])
    start_date = payload.get("startDate", "2025-01-01")
    end_date = payload.get("endDate", "2025-01-10")

    # Mapping des métriques
    metric_mapping = {
        "temp": {"name": "avg_temp_c", "field": "temp"},
        "precip": {"name": "sum_precip_mm", "field": "precip"},
        "windspeed": {"name": "avg_windspeed", "field": "windspeed"},
        "humidity": {"name": "avg_humidity", "field": "humidity"},
    }

    for location in locations:
        # Récupérer les données brutes pour la ville
        data = fetch_city_weather(location, start_date, end_date)
        if not data:
            continue

        # Grouper par mois
        monthly_data = defaultdict(lambda: defaultdict(list))
        for day in data:
            date = day['date']
            month = date[:7]  # YYYY-MM
            for metric in metrics:
                if metric in metric_mapping:
                    field = metric_mapping[metric]["field"]
                    if field in day:
                        monthly_data[month][metric].append(day[field])

        # Agréger les données
        for month, metric_dict in monthly_data.items():
            for metric, values in metric_dict.items():
                if values:
                    metric_info = metric_mapping[metric]
                    metric_name = metric_info["name"]
                    if "avg" in metric_name:
                        value = sum(values) / len(values)
                    elif "sum" in metric_name:
                        value = sum(values)
                    else:
                        value = sum(values) / len(values)  # Moyenne par défaut

                    results.append({
                        "metric_date": month,
                        "location": location,
                        "metric_name": metric_name,
                        "metric_value": round(value, 2),
                        "source": "visualcrossing"
                    })

    return results

def trigger_airflow_dag(dag_id: str, conf: Dict[str, Any]):
    """Déclenche un DAG Airflow (à implémenter)"""
    try:
        # URL de l'API Airflow pour déclencher un DAG
        url = f"{AIRFLOW_BASE_URL}/api/v1/dags/{dag_id}/dagRuns"

        headers = {
            "Content-Type": "application/json",
            # En production, ajouter l'authentification
        }

        data = {
            "conf": conf,
            "dag_run_id": f"manual__{int(time.time())}"
        }

        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

        return response.json()

    except Exception as e:
        print(f"Erreur lors du déclenchement du DAG Airflow: {e}")
        raise

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)