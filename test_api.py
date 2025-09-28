#!/usr/bin/env python3
"""
Script de test pour l'API Weather Batch
Teste les différentes fonctionnalités de l'API
"""

import requests
import time
import json
import sys

BASE_URL = "http://localhost:8000"

def test_api_root():
    """Test de l'endpoint racine"""
    print("🧪 Test de l'endpoint racine...")
    try:
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        print("✅ Endpoint racine OK")
        return True
    except Exception as e:
        print(f"❌ Erreur endpoint racine: {e}")
        return False

def test_run_query():
    """Test de lancement d'une requête"""
    print("🧪 Test de lancement de requête...")
    payload = {
        "locations": ["Paris,FR"],
        "startDate": "2024-01-01",
        "endDate": "2024-03-31",
        "metrics": ["temp"],
        "agg": "avg_by_month"
    }
    try:
        response = requests.post(f"{BASE_URL}/run", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        task_id = data["task_id"]
        print(f"✅ Requête lancée avec task_id: {task_id}")
        return task_id
    except Exception as e:
        print(f"❌ Erreur lancement requête: {e}")
        return None

def test_task_status(task_id):
    """Test de vérification du statut d'une tâche"""
    print(f"🧪 Test du statut de la tâche {task_id}...")
    try:
        response = requests.get(f"{BASE_URL}/status/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert "state" in data
        state = data["state"]
        print(f"✅ Statut de la tâche: {state}")
        return state
    except Exception as e:
        print(f"❌ Erreur vérification statut: {e}")
        return None

def test_fetch_results(task_id):
    """Test de récupération des résultats"""
    print(f"🧪 Test de récupération des résultats pour {task_id}...")
    max_attempts = 10
    attempt = 0

    while attempt < max_attempts:
        try:
            response = requests.get(f"{BASE_URL}/fetch/{task_id}")
            if response.status_code == 200:
                data = response.json()
                assert "data" in data
                results = data["data"]
                assert isinstance(results, list)
                assert len(results) > 0
                print(f"✅ Résultats récupérés: {len(results)} enregistrements")
                return results
            elif response.status_code == 400:
                error_data = response.json()
                if "Task not completed" in error_data.get("detail", ""):
                    print(f"⏳ Tâche pas encore terminée, tentative {attempt + 1}/{max_attempts}")
                    time.sleep(3)
                    attempt += 1
                    continue
                else:
                    print(f"❌ Erreur récupération résultats: {error_data}")
                    return None
            else:
                print(f"❌ Code HTTP inattendu: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Erreur récupération résultats: {e}")
            return None

    print("❌ Timeout: tâche pas terminée dans le temps imparti")
    return None

def validate_results(results):
    """Validation des résultats"""
    print("🧪 Validation des résultats...")
    try:
        assert isinstance(results, list)
        assert len(results) > 0

        # Vérifier la structure d'un résultat
        sample = results[0]
        required_fields = ["metric_date", "location", "metric_name", "metric_value", "source"]
        for field in required_fields:
            assert field in sample, f"Champ manquant: {field}"

        # Vérifier les types
        assert isinstance(sample["metric_date"], str)
        assert isinstance(sample["location"], str)
        assert isinstance(sample["metric_name"], str)
        assert isinstance(sample["metric_value"], (int, float))
        assert isinstance(sample["source"], str)

        # Vérifier les valeurs
        assert sample["source"] == "visualcrossing"
        assert sample["metric_name"] in ["avg_temp_c", "sum_precip_mm", "avg_humidity", "avg_windspeed"]

        print("✅ Structure des résultats valide")
        return True
    except Exception as e:
        print(f"❌ Erreur validation résultats: {e}")
        return False

def run_all_tests():
    """Exécute tous les tests"""
    print("🚀 Démarrage des tests de l'API Weather Batch")
    print("=" * 50)

    tests_passed = 0
    total_tests = 4

    # Test 1: Endpoint racine
    if test_api_root():
        tests_passed += 1

    # Test 2: Lancement de requête
    task_id = test_run_query()
    if task_id:
        tests_passed += 1

        # Test 3: Statut de la tâche
        status = test_task_status(task_id)
        if status:
            tests_passed += 1

        # Test 4: Récupération des résultats
        results = test_fetch_results(task_id)
        if results and validate_results(results):
            tests_passed += 1
    else:
        print("❌ Impossible de continuer les tests sans task_id")

    print("=" * 50)
    print(f"📊 Résultats: {tests_passed}/{total_tests} tests réussis")

    if tests_passed == total_tests:
        print("🎉 Tous les tests sont passés !")
        return True
    else:
        print("⚠️ Certains tests ont échoué")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)