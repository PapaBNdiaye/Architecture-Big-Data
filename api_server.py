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

app = FastAPI(title="Weather Batch API", version="1.0.0")

# Configuration CORS pour le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
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
        if (datetime.now() - task["created_at"]).seconds > 5:
            task["status"] = "SUCCESS"
            # Générer des données de test
            task["result"] = generate_mock_results(task["payload"])

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
        print(f"Processing batch request {task_id}")
        print(f"Payload: {payload}")

        # Ici, en production, on déclencherait le DAG Airflow
        # Pour l'instant, on simule le traitement

        # Attendre un peu pour simuler le traitement
        time.sleep(3)

        # Générer des résultats mockés
        results = generate_mock_results(payload.dict())

        # Mettre à jour la tâche
        tasks[task_id]["status"] = "SUCCESS"
        tasks[task_id]["result"] = results

        print(f"Batch processing completed for task {task_id}")

    except Exception as e:
        print(f"Error processing batch request {task_id}: {e}")
        tasks[task_id]["status"] = "FAILURE"

def generate_mock_results(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Génère des données mockées pour les tests"""
    results = []
    locations = payload.get("locations", ["Paris,FR"])
    metrics = payload.get("metrics", ["avg_temp_c"])
    start_date = payload.get("startDate", "2025-01-01")
    end_date = payload.get("endDate", "2025-01-31")

    # Générer des données pour chaque combinaison
    for location in locations:
        for metric in metrics:
            # Générer quelques points de données
            for month in range(1, 4):  # Janvier à Mars 2025
                metric_date = f"2025-{month:02d}"
                # Valeurs mockées selon la métrique
                if "temp" in metric:
                    value = 15 + month * 2 + (hash(location) % 10)  # Température variable
                elif "precip" in metric:
                    value = 50 + (hash(location) % 30)  # Précipitations
                elif "rainy" in metric:
                    value = 12 + (hash(location) % 8)  # Jours de pluie
                else:
                    value = 100 + (hash(location) % 50)  # Valeur par défaut

                results.append({
                    "metric_date": metric_date,
                    "location": location,
                    "metric_name": metric,
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
        print(f"Error triggering Airflow DAG: {e}")
        raise

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)