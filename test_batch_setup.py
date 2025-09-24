#!/usr/bin/env python3
"""
Script de test pour valider la configuration de l'architecture Lambda batch
"""

import os
import sys
import requests
import subprocess
import time
from typing import Dict, List, Tuple

class BatchSetupTester:
    def __init__(self):
        self.test_results = {}
        self.services_to_test = {
            'hdfs-namenode': 'http://localhost:9870',
            'spark-master': 'http://localhost:9090', 
            'airflow': 'http://localhost:8080',
            'kafka': 'http://localhost:9021'
        }
    
    def test_environment_variables(self) -> bool:
        """Teste les variables d'environnement requises"""
        print("🧪 Test des variables d'environnement...")
        
        required_vars = ['VISUAL_CROSSING_API_KEY']
        missing_vars = []
        
        for var in required_vars:
            value = os.getenv(var)
            if not value or value == 'VOTRE_API_KEY':
                missing_vars.append(var)
                print(f"  ❌ {var}: Non configurée")
            else:
                print(f"  ✅ {var}: Configurée")
        
        if missing_vars:
            print(f"⚠️  Variables manquantes: {', '.join(missing_vars)}")
            return False
        
        print("✅ Toutes les variables d'environnement sont configurées")
        return True
    
    def test_docker_services(self) -> bool:
        """Teste la disponibilité des services Docker"""
        print("\n🧪 Test des services Docker...")
        
        try:
            # Vérification que docker-compose est disponible
            result = subprocess.run(['docker-compose', 'ps'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                print("❌ Docker Compose non disponible")
                return False
            
            # Analyse des services en cours d'exécution
            services_running = []
            for line in result.stdout.split('\n'):
                if 'Up' in line:
                    service_name = line.split()[0]
                    services_running.append(service_name)
            
            # Vérification des services essentiels (noms réels des conteneurs)
            essential_services = ['hdfs-namenode', 'spark-master', 'webserver']
            found_services = []
            
            for service in essential_services:
                if any(service in s for s in services_running):
                    found_services.append(service)
            
            missing_services = [s for s in essential_services if s not in found_services]
            
            if missing_services:
                print(f"❌ Services manquants: {', '.join(missing_services)}")
                return False
            
            print(f"✅ Services Docker en cours d'exécution: {', '.join(services_running)}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors du test Docker: {e}")
            return False
    
    def test_service_connectivity(self) -> Dict[str, bool]:
        """Teste la connectivité aux services"""
        print("\n🧪 Test de connectivité aux services...")
        
        results = {}
        
        for service, url in self.services_to_test.items():
            try:
                response = requests.get(url, timeout=10)
                is_accessible = response.status_code == 200
                results[service] = is_accessible
                
                status = "✅" if is_accessible else "❌"
                print(f"  {status} {service}: {url} (HTTP {response.status_code})")
                
            except requests.exceptions.RequestException as e:
                results[service] = False
                print(f"  ❌ {service}: {url} (Erreur: {e})")
        
        return results
    
    def test_hdfs_functionality(self) -> bool:
        """Teste la fonctionnalité HDFS"""
        print("\n🧪 Test de la fonctionnalité HDFS...")
        
        try:
            # Test de création d'un répertoire
            test_dir = "/test_batch_setup"
            create_cmd = f"docker exec hdfs-namenode hdfs dfs -mkdir -p {test_dir}"
            result = subprocess.run(create_cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ Impossible de créer le répertoire HDFS: {result.stderr}")
                return False
            
            # Test de liste des répertoires
            list_cmd = "docker exec hdfs-namenode hdfs dfs -ls /"
            result = subprocess.run(list_cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ Impossible de lister les répertoires HDFS: {result.stderr}")
                return False
            
            # Test de suppression du répertoire de test
            delete_cmd = f"docker exec hdfs-namenode hdfs dfs -rm -r {test_dir}"
            subprocess.run(delete_cmd, shell=True, capture_output=True, text=True)
            
            print("✅ HDFS fonctionne correctement")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors du test HDFS: {e}")
            return False
    
    def test_spark_functionality(self) -> bool:
        """Teste la fonctionnalité Spark"""
        print("\n🧪 Test de la fonctionnalité Spark...")
        
        try:
            # Test simple de connectivité Spark Master (rapide)
            response = requests.get('http://localhost:9090', timeout=5)
            if response.status_code == 200:
                print("✅ Spark Master accessible")
                return True
            else:
                print(f"❌ Spark Master non accessible: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur lors du test Spark: {e}")
            return False
    
    def test_batch_processing_import(self) -> bool:
        """Teste l'importation du module batch_processing"""
        print("\n🧪 Test d'importation du module batch_processing...")
        
        try:
            # Ajout du répertoire courant au path
            sys.path.insert(0, os.getcwd())
            
            # Import du module
            from batch_processing import WeatherBatchProcessor
            
            # Test d'instanciation
            processor = WeatherBatchProcessor(api_key="test_key")
            
            print("✅ Module batch_processing importé avec succès")
            return True
            
        except ImportError as e:
            print(f"❌ Erreur d'importation: {e}")
            return False
        except Exception as e:
            print(f"❌ Erreur lors de l'instanciation: {e}")
            return False
    
    def test_airflow_dag_syntax(self) -> bool:
        """Teste la syntaxe du DAG Airflow"""
        print("\n🧪 Test de la syntaxe du DAG Airflow...")
        
        try:
            dag_file = "dags/weather_batch_dag.py"
            
            if not os.path.exists(dag_file):
                print(f"❌ Fichier DAG non trouvé: {dag_file}")
                return False
            
            # Test de compilation Python
            with open(dag_file, 'r') as f:
                code = f.read()
            
            compile(code, dag_file, 'exec')
            print("✅ Syntaxe du DAG Airflow valide")
            return True
            
        except SyntaxError as e:
            print(f"❌ Erreur de syntaxe dans le DAG: {e}")
            return False
        except Exception as e:
            print(f"❌ Erreur lors du test du DAG: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Exécute tous les tests"""
        print("🚀 Début des tests de configuration batch\n")
        
        tests = [
            ("Variables d'environnement", self.test_environment_variables),
            ("Services Docker", self.test_docker_services),
            ("Connectivité services", lambda: all(self.test_service_connectivity().values())),
            ("Fonctionnalité HDFS", self.test_hdfs_functionality),
            ("Fonctionnalité Spark", self.test_spark_functionality),
            ("Import batch_processing", self.test_batch_processing_import),
            ("Syntaxe DAG Airflow", self.test_airflow_dag_syntax)
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                results[test_name] = result
            except Exception as e:
                print(f"❌ Erreur lors du test '{test_name}': {e}")
                results[test_name] = False
        
        return results
    
    def print_summary(self, results: Dict[str, bool]):
        """Affiche le résumé des tests"""
        print("\n" + "="*50)
        print("📊 RÉSUMÉ DES TESTS")
        print("="*50)
        
        passed = sum(results.values())
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASSÉ" if result else "❌ ÉCHOUÉ"
            print(f"{status} {test_name}")
        
        print(f"\nRésultat global: {passed}/{total} tests réussis")
        
        if passed == total:
            print("\n🎉 Tous les tests sont passés ! L'architecture batch est prête.")
        else:
            print(f"\n⚠️  {total - passed} test(s) ont échoué. Vérifiez la configuration.")
            
            # Suggestions de dépannage
            print("\n🔧 Suggestions de dépannage:")
            for test_name, result in results.items():
                if not result:
                    if "Variables" in test_name:
                        print("  - Configurez la variable VISUAL_CROSSING_API_KEY")
                    elif "Docker" in test_name:
                        print("  - Exécutez: docker-compose up -d")
                    elif "Connectivité" in test_name:
                        print("  - Attendez que tous les services soient démarrés (2-3 minutes)")
                    elif "HDFS" in test_name:
                        print("  - Vérifiez les logs: docker-compose logs hdfs-namenode")
                    elif "Spark" in test_name:
                        print("  - Vérifiez les logs: docker-compose logs spark-master")

def main():
    """Fonction principale"""
    tester = BatchSetupTester()
    results = tester.run_all_tests()
    tester.print_summary(results)
    
    # Code de sortie basé sur les résultats
    if all(results.values()):
        sys.exit(0)  # Succès
    else:
        sys.exit(1)  # Échec

if __name__ == "__main__":
    main()
