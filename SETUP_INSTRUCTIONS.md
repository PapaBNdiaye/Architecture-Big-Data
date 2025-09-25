# 🚀 Instructions de démarrage

## Prérequis
- Docker et Docker Compose installés
- Python 3.8+ installé
- Clé API Visual Crossing

## Démarrage rapide

### 1. Cloner le projet
```bash
git clone <votre-repo>
cd Architecture-Big-Data
```

### 2. Créer un environnement virtuel Python
```bash
# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
# Sur Windows :
venv\Scripts\activate
# Sur Linux/Mac :
source venv/bin/activate

# Vérifier que l'environnement est activé
which python  # Doit pointer vers venv/bin/python (ou venv\Scripts\python sur Windows)
```

### 3. Installer les dépendances Python (optionnel pour développement local)
```bash
# Installer les dépendances pour le développement local
pip install -r requirements_local.txt

# Ou pour le traitement batch uniquement
pip install -r requirements_batch.txt
```

### 4. Configurer la clé API
**Option A - Variable d'environnement :**
```bash
export VISUAL_CROSSING_API_KEY=votre_cle_api_ici
```

**Option B - Fichier .env :**
```bash
echo "VISUAL_CROSSING_API_KEY=votre_cle_api_ici" > .env
```

### 5. Démarrer l'infrastructure
```bash
docker-compose up -d
```

### 6. Vérifier le statut
```bash
docker ps
```

## 🔑 Obtenir une clé API Visual Crossing

1. Allez sur : https://www.visualcrossing.com/weather-api
2. Créez un compte gratuit
3. Obtenez votre clé API (1000 requêtes/jour gratuites)

## 🌐 Interfaces disponibles

- **HDFS Web UI** : http://localhost:9871
- **Spark UI** : http://localhost:9090
- **Airflow** : http://localhost:8080 (admin/admin)
- **Kafka Control Center** : http://localhost:9021

## 🧪 Tester le pipeline

```bash
docker exec spark-master spark-submit \
  --master spark://spark-master:7077 \
  --py-files //opt/spark/project/config/cities_config.py \
  //opt/spark/project/batch_processing_local.py
```

## 🛠️ Dépannage

### Problème : "zookeeper is unhealthy"
- Vérifiez que la variable `VISUAL_CROSSING_API_KEY` est définie
- Redémarrez : `docker-compose down && docker-compose up -d`

### Problème : "ModuleNotFoundError: No module named 'requests'"
```bash
docker exec spark-master pip install -r /opt/spark/requirements_batch.txt
```

### Problème : "Permission denied: user=spark, access=WRITE"
```bash
# Créer le répertoire pour l'utilisateur spark
docker exec -it hdfs-namenode bash -c "hdfs dfs -mkdir -p /user/spark/weather/raw"

# Donner les permissions à l'utilisateur spark
docker exec -it hdfs-namenode bash -c "hdfs dfs -chown -R spark:spark /user/spark"

# Vérifier les permissions
docker exec -it hdfs-namenode bash -c "hdfs dfs -ls -la /user/"
```

## 📊 Vérifier les données

```bash
docker exec hdfs-namenode bash -c "hdfs dfs -ls /user/spark/weather/raw/"
```

## 🗑️ Nettoyer HDFS (recommencer à zéro)

### Supprimer toutes les données raw
```bash
# Supprimer le répertoire raw complet
docker exec hdfs-namenode bash -c "hdfs dfs -rm -r /user/spark/weather/raw"

# Vérifier que c'est supprimé
docker exec hdfs-namenode bash -c "hdfs dfs -ls /user/spark/weather/"
```

### Supprimer tout le répertoire weather (optionnel)
```bash
# Supprimer tout le répertoire weather
docker exec hdfs-namenode bash -c "hdfs dfs -rm -r /user/spark/weather"

# Vérifier
docker exec hdfs-namenode bash -c "hdfs dfs -ls /user/spark/"
```

### Nettoyage complet (si nécessaire)
```bash
# Supprimer tout le répertoire utilisateur spark
docker exec hdfs-namenode bash -c "hdfs dfs -rm -r /user/spark"

# Recréer la structure
docker exec hdfs-namenode bash -c "hdfs dfs -mkdir -p /user/spark/weather/raw"
docker exec hdfs-namenode bash -c "hdfs dfs -chown -R spark:spark /user/spark"
```

## 🔄 Gestion de l'environnement virtuel

### Désactiver l'environnement virtuel
```bash
deactivate
```

### Réactiver l'environnement virtuel
```bash
# Sur Windows :
venv\Scripts\activate
# Sur Linux/Mac :
source venv/bin/activate
```

### Supprimer l'environnement virtuel (si nécessaire)
```bash
# Désactiver d'abord
deactivate

# Supprimer le dossier
rm -rf venv  # Linux/Mac
rmdir /s venv  # Windows
```
