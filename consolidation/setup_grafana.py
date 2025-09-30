#!/usr/bin/env python3
"""
Script de configuration automatique de Grafana
Crée les dashboards et datasources pour les données météo
"""

import requests
import json
import time

class GrafanaSetup:
    def __init__(self):
        self.grafana_url = "http://grafana:3000"
        self.username = "admin"
        self.password = "admin"
        self.api_key = None
        
    def wait_for_grafana(self):
        """Attend que Grafana soit disponible"""
        print("⏳ Attente de Grafana...")
        max_attempts = 30
        
        for attempt in range(max_attempts):
            try:
                response = requests.get(f"{self.grafana_url}/api/health", timeout=5)
                if response.status_code == 200:
                    print("✅ Grafana est disponible")
                    return True
            except:
                pass
            
            time.sleep(2)
            print(f"   Tentative {attempt + 1}/{max_attempts}")
        
        print("❌ Grafana n'est pas disponible")
        return False
    
    def create_api_key(self):
        """Crée une clé API pour Grafana"""
        print("🔑 Création de la clé API...")
        
        auth_data = {
            "name": "weather-api",
            "role": "Admin"
        }
        
        response = requests.post(
            f"{self.grafana_url}/api/auth/keys",
            json=auth_data,
            auth=(self.username, self.password)
        )
        
        if response.status_code == 200:
            self.api_key = response.json()["key"]
            print("✅ Clé API créée")
            return True
        else:
            print(f"❌ Erreur création clé API: {response.text}")
            return False
    
    def create_postgres_datasource(self):
        """Crée la source de données PostgreSQL"""
        print("📊 Configuration de la source PostgreSQL...")
        
        datasource_config = {
            "name": "Weather PostgreSQL",
            "type": "postgres",
            "url": "postgres:5432",
            "database": "airflow",
            "user": "airflow",
            "secureJsonData": {
                "password": "airflow"
            },
            "jsonData": {
                "sslmode": "disable"
            }
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{self.grafana_url}/api/datasources",
            json=datasource_config,
            headers=headers
        )
        
        if response.status_code == 200:
            print("✅ Source PostgreSQL configurée")
            return True
        else:
            print(f"❌ Erreur configuration PostgreSQL: {response.text}")
            return False
    
    def create_weather_dashboard(self):
        """Crée le dashboard météo"""
        print("📈 Création du dashboard météo...")
        
        dashboard_config = {
            "dashboard": {
                "title": "Dashboard Météo Big Data",
                "panels": [
                    {
                        "title": "Températures par Ville",
                        "type": "timeseries",
                        "targets": [
                            {
                                "expr": "SELECT date, temp FROM weather_data WHERE city = 'Paris,FR' ORDER BY date",
                                "datasource": "Weather PostgreSQL"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
                    },
                    {
                        "title": "Précipitations",
                        "type": "timeseries",
                        "targets": [
                            {
                                "expr": "SELECT date, precip FROM weather_data ORDER BY date",
                                "datasource": "Weather PostgreSQL"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
                    },
                    {
                        "title": "Statistiques par Ville",
                        "type": "table",
                        "targets": [
                            {
                                "expr": "SELECT city, AVG(temp) as temp_moyenne, MAX(tempmax) as temp_max FROM weather_data GROUP BY city",
                                "datasource": "Weather PostgreSQL"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8}
                    }
                ],
                "time": {
                    "from": "now-1y",
                    "to": "now"
                },
                "refresh": "5m"
            }
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{self.grafana_url}/api/dashboards/db",
            json=dashboard_config,
            headers=headers
        )
        
        if response.status_code == 200:
            print("✅ Dashboard météo créé")
            return True
        else:
            print(f"❌ Erreur création dashboard: {response.text}")
            return False
    
    def setup_grafana(self):
        """Configuration complète de Grafana"""
        print("🚀 Configuration de Grafana pour les données météo...")
        print("=" * 60)
        
        if not self.wait_for_grafana():
            return False
        
        if not self.create_api_key():
            return False
        
        if not self.create_postgres_datasource():
            return False
        
        if not self.create_weather_dashboard():
            return False
        
        print("\n🎉 Configuration Grafana terminée!")
        print(f"🌐 Accédez à: {self.grafana_url}")
        print("👤 Utilisateur: admin / Mot de passe: admin")
        print("📊 Dashboard météo disponible dans la section Dashboards")
        
        return True

def main():
    setup = GrafanaSetup()
    setup.setup_grafana()

if __name__ == "__main__":
    main()
