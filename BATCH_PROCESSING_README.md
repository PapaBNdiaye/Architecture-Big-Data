# Architecture Lambda - Couche Batch

Ce document décrit l'implémentation de la couche batch de l'architecture Lambda pour le traitement des données météo.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Visual    │───▶│  Batch Processor │───▶│      HDFS      │
│   Crossing      │    │   (Spark)       │    │   (Stockage)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │     Airflow     │
                       │  (Orchestration) │
                       └─────────────────┘
```

## 📋 Composants

### 1. HDFS (Hadoop Distributed File System)
- **Namenode**: `hdfs-namenode:9870` (Interface web)
- **Datanode**: `hdfs-datanode` (Stockage des données)
- **Volumes persistants**: `hadoop_namenode`, `hadoop_datanode`

### 2. Traitement Batch
- **Script principal**: `batch_processing.py`
- **Framework**: Apache Spark
- **Format de stockage**: Parquet (optimisé pour les requêtes analytiques)

### 3. Orchestration
- **DAG Airflow**: `dags/weather_batch_dag.py`
- **Planification**: Exécution quotidienne
- **Monitoring**: Interface Airflow sur `localhost:8080`

## 🚀 Déploiement

### Prérequis
```bash
# Variables d'environnement requises
export VISUAL_CROSSING_API_KEY="votre_clé_api"
```

### 1. Démarrage des services
```bash
# Démarrage de tous les services
docker-compose up -d

# Vérification du statut
docker-compose ps
```

### 2. Configuration de l'environnement
```bash
# Configuration complète
python setup_batch_environment.py --full-setup

# Vérification des services
python setup_batch_environment.py --check-services

# Configuration HDFS
python setup_batch_environment.py --setup-hdfs
```

### 3. Test du traitement batch
```bash
# Test manuel
python batch_processing.py

# Via Airflow (interface web)
# http://localhost:8080
```

## 📊 Données Traitées

### Villes traitées
- **Villes françaises principales**: Paris, Lyon, Marseille, Toulouse, Nice, Nantes, Strasbourg, Montpellier, Bordeaux, Lille
- **Traitement parallèle**: 3 villes simultanément pour optimiser les performances
- **Configuration flexible**: Facilement modifiable dans `config/cities_config.py`

### Variables météo récupérées
- **Température**: `temp`, `tempmax`, `tempmin`
- **Humidité**: `humidity`, `dew`
- **Précipitations**: `precip`, `preciptype`, `snow`, `snowdepth`
- **Pression**: `pressure`
- **Vent**: `windspeed`, `windgust`, `winddir`
- **Visibilité**: `visibility`, `cloudcover`
- **Rayonnement**: `uvindex`, `solarradiation`, `solarenergy`
- **Localisation**: `latitude`, `longitude`, `address`

### Agrégations calculées
- **Température**: Moyenne, maximum, minimum par jour
- **Humidité**: Moyenne, maximum, minimum par jour
- **Pression**: Moyenne, maximum, minimum par jour
- **Vent**: Moyenne et maximum par jour
- **Précipitations**: Total et maximum par jour
- **Rayonnement**: Total d'énergie solaire par jour

## 📁 Structure HDFS

```
/weather_data/
├── raw/                    # Données brutes de l'API
│   ├── Paris_FR/
│   │   └── 20250101_143022/
│   ├── Lyon_FR/
│   │   └── 20250101_143022/
│   ├── Marseille_FR/
│   │   └── 20250101_143022/
│   └── ... (autres villes)
├── batch/                  # Données agrégées
│   ├── Paris_FR/
│   │   └── 20250101_143022/
│   ├── Lyon_FR/
│   │   └── 20250101_143022/
│   ├── Marseille_FR/
│   │   └── 20250101_143022/
│   └── ... (autres villes)
└── processed/              # Données finales (futur)
```

## 🔧 Configuration

### Variables Airflow
Configurez ces variables dans l'interface Airflow (`localhost:8080`):

```python
VISUAL_CROSSING_API_KEY = "votre_clé_api"
HDFS_URL = "hdfs://hdfs-namenode:9000"
SPARK_MASTER_URL = "spark://spark-master:7077"
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
```

### Paramètres du DAG
```python
# Exécution quotidienne à 6h00
schedule_interval = '@daily'

# Retry en cas d'échec
retries = 2
retry_delay = timedelta(minutes=5)
```

## 📈 Monitoring

### Interfaces de monitoring
- **Airflow**: http://localhost:8080
- **HDFS Namenode**: http://localhost:9870
- **Spark Master**: http://localhost:9090
- **Kafka Control Center**: http://localhost:9021

### Logs
```bash
# Logs Airflow
docker-compose logs scheduler
docker-compose logs webserver

# Logs HDFS
docker-compose logs hdfs-namenode
docker-compose logs hdfs-datanode

# Logs Spark
docker-compose logs spark-master
docker-compose logs spark-worker
```

## 🧪 Tests

### Test unitaire du processeur
```bash
python -c "
from batch_processing import WeatherBatchProcessor
processor = WeatherBatchProcessor('test_key')
print('Processeur initialisé avec succès')
"
```

### Test de connectivité HDFS
```bash
# Vérification du cluster HDFS
docker exec hdfs-namenode hdfs dfsadmin -report

# Liste des fichiers
docker exec hdfs-namenode hdfs dfs -ls /weather_data
```

### Test multi-villes
```bash
# Test du traitement de plusieurs villes
python test_multi_cities.py
```

### Test de l'API Visual Crossing
```bash
# Test de l'endpoint API pour une ville
curl "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/Paris,FR/2025-01-01/2025-01-01?key=VOTRE_API_KEY&include=days&elements=temp,humidity&contentType=csv"
```

## 🔍 Dépannage

### Problèmes courants

1. **HDFS non accessible**
   ```bash
   # Vérifier le statut des conteneurs
   docker-compose ps
   
   # Redémarrer HDFS
   docker-compose restart hdfs-namenode hdfs-datanode
   ```

2. **Erreur de clé API**
   ```bash
   # Vérifier la variable d'environnement
   echo $VISUAL_CROSSING_API_KEY
   
   # Configurer dans Airflow
   # Interface web > Admin > Variables
   ```

3. **Spark non disponible**
   ```bash
   # Vérifier les logs Spark
   docker-compose logs spark-master
   
   # Redémarrer Spark
   docker-compose restart spark-master spark-worker
   ```

## 📚 Ressources

- [Documentation Visual Crossing API](https://www.visualcrossing.com/resources/documentation/weather-api/)
- [Apache Spark Documentation](https://spark.apache.org/docs/latest/)
- [HDFS User Guide](https://hadoop.apache.org/docs/current/hadoop-project-dist/hadoop-hdfs/HdfsUserGuide.html)
- [Apache Airflow Documentation](https://airflow.apache.org/docs/)

## 🤝 Contribution

Pour contribuer à ce projet:

1. Fork le repository
2. Créer une branche feature (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commit vos changements (`git commit -am 'Ajout nouvelle fonctionnalité'`)
4. Push vers la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Créer une Pull Request
