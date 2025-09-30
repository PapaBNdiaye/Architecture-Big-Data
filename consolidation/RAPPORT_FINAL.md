# Architecture Lambda pour le Traitement de Données Météorologiques

**Projet académique - Big Data & Architecture Lambda**

---

## Table des matières

1. [Introduction](#1-introduction)
2. [Contexte et objectifs](#2-contexte-et-objectifs)
3. [Architecture Lambda](#3-architecture-lambda)
4. [Technologies utilisées](#4-technologies-utilisées)
5. [Implémentation détaillée](#5-implémentation-détaillée)
6. [Guide de déploiement](#6-guide-de-déploiement)
7. [Difficultés rencontrées](#7-difficultés-rencontrées)
8. [Apprentissages](#8-apprentissages)
9. [Conclusion](#9-conclusion)

---

## 1. Introduction

Ce document présente la réalisation d'un pipeline de traitement de données complet basé sur l'architecture Lambda. Le projet vise à mettre en place un système capable de collecter, traiter et visualiser des données météorologiques en temps réel et par batch, tout en respectant les principes fondamentaux de l'architecture Lambda.

L'architecture Lambda, introduite par Nathan Marz, répond à un besoin croissant dans le domaine du Big Data : la capacité de traiter simultanément des données historiques volumineuses (batch) et des données en flux continu (streaming) pour fournir une vue unifiée et cohérente des informations.

Notre implémentation s'appuie sur des technologies open-source reconnues dans l'écosystème Big Data et démontre concrètement comment orchestrer plusieurs systèmes distribués pour répondre à des besoins de traitement de données variés.

---

## 2. Contexte et objectifs

### 2.1 Contexte du projet

Dans le cadre d'un projet académique sur les architectures Big Data, nous avons été amenés à concevoir et implémenter un pipeline complet de traitement de données. Le choix s'est porté sur les données météorologiques pour plusieurs raisons :

- Disponibilité de données réelles via des APIs publiques
- Variabilité temporelle intéressante pour l'analyse
- Pertinence pour des cas d'usage réels (agriculture, transport, énergie)
- Volume de données suffisant pour justifier une architecture distribuée

### 2.2 Objectifs principaux

Le projet devait répondre aux exigences suivantes :

1. **Architecture Lambda complète** : Implémenter les trois couches (Batch, Speed, Serving)
2. **Collecte de données réelles** : Utiliser l'API Visual Crossing Weather
3. **Traitement batch** : Analyses historiques et calculs d'agrégats
4. **Traitement temps réel** : Ingestion et traitement de flux continus
5. **Visualisation unifiée** : Dashboards combinant données batch et streaming
6. **Orchestration** : Automatisation des workflows via Airflow
7. **Isolation des services** : Déploiement containerisé avec Docker
8. **Documentation** : Guide complet d'installation et d'utilisation

### 2.3 Cas d'usage visés

Le système permet de répondre à plusieurs besoins :

- Surveillance en temps réel des conditions météorologiques
- Analyse de tendances historiques sur plusieurs mois
- Comparaison des conditions entre différentes villes
- Détection d'événements météorologiques significatifs
- Prévisions basées sur l'historique des données

---

## 3. Architecture Lambda

### 3.1 Principes de l'architecture Lambda

L'architecture Lambda repose sur trois couches complémentaires :

**Couche Batch (Batch Layer)**
- Traite l'ensemble des données historiques
- Précision maximale au détriment de la latence
- Vue complète et immuable des données
- Recalcule périodiquement les vues batch

**Couche Speed (Speed Layer)**
- Traite uniquement les données récentes
- Latence minimale au détriment de la précision
- Compense le délai de la couche batch
- Données incrémentales et éphémères

**Couche Serving (Serving Layer)**
- Fusionne les résultats des deux couches
- Répond aux requêtes des utilisateurs
- Présente une vue unifiée des données
- Gère la visualisation et l'accès aux données

### 3.2 Architecture globale du système

Notre implémentation se structure comme suit :

```
┌─────────────────────────────────────────────────────────────┐
│                   API VISUAL CROSSING                        │
│              (Source de données météo)                       │
└──────────────────┬──────────────────────────────────────────┘
                   │
      ┌────────────┴────────────┐
      │                         │
      ▼                         ▼
┌─────────────┐          ┌─────────────┐
│   BATCH     │          │   SPEED     │
│   LAYER     │          │   LAYER     │
└─────────────┘          └─────────────┘
      │                         │
      │  Spark                  │  Kafka
      │  HDFS                   │  InfluxDB
      │  PostgreSQL             │  Cassandra
      │  Airflow                │  Telegraf
      │                         │
      └────────────┬────────────┘
                   │
                   ▼
           ┌───────────────┐
           │   SERVING     │
           │   LAYER       │
           └───────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
   ┌─────────┐         ┌──────────┐
   │ Grafana │         │ FastAPI  │
   │         │         │ Frontend │
   └─────────┘         └──────────┘
```

### 3.3 Flux de données détaillé

#### 3.3.1 Couche Batch

```
API Visual Crossing
      ↓
Script Python (collecte périodique)
      ↓
Apache Spark (traitement distribué)
      ↓
HDFS (stockage brut + résultats)
      ↓
Analyses Spark (agrégations, statistiques)
      ↓
Export PostgreSQL
      ↓
Grafana (visualisation batch)
```

**Orchestration** : Apache Airflow déclenche le workflow batch selon un planning défini (quotidien, hebdomadaire).

#### 3.3.2 Couche Speed

```
API Visual Crossing (polling continu)
      ↓
Producteur Kafka Python
      ↓
Topic Kafka (weather_data_v2)
      ├─────────────────────┐
      ↓                     ↓
Telegraf              Spark Streaming
      ↓                     ↓
InfluxDB              Cassandra
      ↓                     
Grafana (visualisation temps réel)
```

**Temps de latence** : Moins de 5 secondes entre la collecte et la visualisation dans Grafana.

#### 3.3.3 Couche Serving

La couche serving combine les deux sources :

- **Grafana** : Dashboards avec sources multiples (InfluxDB + PostgreSQL)
- **FastAPI** : API REST exposant batch et speed data
- **Frontend React** : Interface utilisateur avec filtres et visualisations

### 3.4 Choix d'architecture

Plusieurs décisions architecturales ont été prises :

**1. Séparation physique des stockages**
- HDFS pour les données batch (immutables, volumineuses)
- InfluxDB pour le streaming (time-series, optimisé lecture rapide)
- PostgreSQL pour l'export batch (requêtes SQL complexes)
- Cassandra pour le streaming alternatif (haute disponibilité)

**2. Double pipeline de streaming**
- Telegraf → InfluxDB : Simplicité, faible latence
- Spark Streaming → Cassandra : Flexibilité, transformations complexes

**3. Orchestration centralisée**
- Airflow gère les workflows batch ET speed
- Visibilité unifiée de tous les traitements
- Gestion des dépendances entre tâches

---

## 4. Technologies utilisées

### 4.1 Infrastructure et orchestration

**Docker & Docker Compose**
- Isolation complète des services
- Reproductibilité de l'environnement
- Facilité de déploiement
- Gestion des réseaux et volumes

**Apache Airflow 2.6**
- Orchestration des workflows
- Planification des tâches batch
- Monitoring des exécutions
- Gestion des dépendances

### 4.2 Couche Batch

**Apache Spark 3.4**
- Traitement distribué en mémoire
- API PySpark pour Python
- Support natif HDFS et Parquet
- Transformations et agrégations performantes

**HDFS (Hadoop 3.2)**
- Système de fichiers distribué
- Tolérance aux pannes
- Scalabilité horizontale
- Format Parquet pour l'optimisation

**PostgreSQL 14**
- Base relationnelle robuste
- Requêtes SQL complexes
- Intégration native avec Grafana
- Indexation performante

### 4.3 Couche Speed

**Apache Kafka 7.4**
- Plateforme de streaming distribuée
- Haute disponibilité et débit
- Rétention configurable des messages
- Découplage producteur/consommateur

**InfluxDB 2.7**
- Base de données time-series
- Requêtes Flux optimisées
- Compression efficace
- Rétention automatique

**Telegraf 1.30**
- Agent de collecte léger
- Parsing JSON natif
- Plugins multiples
- Faible overhead

**Cassandra (optionnel)**
- Base NoSQL distribuée
- Écriture haute performance
- Pas de point unique de défaillance
- Schéma flexible

### 4.4 Couche Serving

**Grafana 10.4**
- Visualisation multi-sources
- Dashboards interactifs
- Alertes configurables
- Provisioning as code

**FastAPI**
- Framework Python moderne
- Documentation auto-générée
- Validation automatique
- Performance élevée

**React + TypeScript**
- Interface utilisateur moderne
- Composants réutilisables
- Type-safety
- Écosystème riche

### 4.5 Langages et outils

**Python 3.9**
- Scripts de collecte et traitement
- DAGs Airflow
- API backend
- Librairies : PySpark, Kafka-Python, Requests

**Configuration as Code**
- Docker Compose (YAML)
- Telegraf (TOML)
- Grafana Provisioning (YAML/JSON)

---

## 5. Implémentation détaillée

### 5.1 Structure du projet

Le projet est organisé en trois dossiers principaux avant consolidation :

**batch/** : Couche batch complète
**speedLayers/** : Couche speed complète  
**front/** : Frontend et API

**consolidation/** : Architecture Lambda unifiée

### 5.2 Couche Batch - Implémentation

#### 5.2.1 Collecte des données (batch_processing_local.py)

Le script de collecte batch utilise PySpark pour distribuer les appels API :

```python
def fetch_city_weather(city, start_date, end_date):
    """Récupère les données météo pour une ville"""
    # Appel API Visual Crossing
    # Gestion retry avec backoff exponentiel
    # Formatage des données
    # Retour format structuré
```

Chaque worker Spark traite une ville indépendamment, permettant la parallélisation. Les données sont stockées en Parquet dans HDFS avec partitionnement par date.

#### 5.2.2 Analyses (weather_analysis.py)

Analyses météorologiques avancées :

- Calcul des moyennes mensuelles
- Identification des extrêmes
- Comparaisons inter-villes
- Corrélations entre variables
- Clustering des villes par profil météo
- Analyse d'amplitude thermique

#### 5.2.3 Export PostgreSQL (export_to_postgres.py)

Les résultats d'analyses sont exportés dans PostgreSQL pour :
- Faciliter les requêtes SQL complexes
- Permettre l'intégration avec Grafana
- Offrir une API de données structurées

#### 5.2.4 Orchestration Airflow

DAG `weather_batch_dag.py` :

```python
check_hdfs >> process_batch >> validate_data >> export_postgres >> setup_grafana
```

Planification : Quotidien à 2h du matin
Retry : 3 tentatives avec délai exponentiel
Alertes : Email en cas d'échec

### 5.3 Couche Speed - Implémentation

#### 5.3.1 Producteur Kafka (kafka_producer.py)

Producteur Python avec deux modes :

**Mode ponctuel** : Envoie N messages puis s'arrête
**Mode continu** : Boucle infinie avec intervalle configurable

Fonctionnalités :
- Appel API Visual Crossing en temps réel
- Fallback simulation si API indisponible
- Enrichissement des données (is_rain, is_storm, prévisions)
- Format RFC3339 pour les timestamps
- Gestion des signaux (CTRL+C propre)

#### 5.3.2 Pipeline Telegraf

Configuration Telegraf (`telegraf.conf`) :

**Input** : Consumer Kafka
- Topic : weather_data_v2
- Format : JSON v2 avec mapping explicite
- Parsing timestamp : RFC3339

**Output** : InfluxDB v2
- Bucket : speed_bucket
- Tags : city, country, station_id, data_origin
- Fields : Toutes les variables météo

#### 5.3.3 Spark Streaming (optionnel)

Pour des traitements plus complexes :

```python
# Lecture du stream Kafka
spark_df = spark.readStream.format("kafka")...

# Parsing JSON
parsed_df = parse_json(spark_df)

# Écriture Cassandra
parsed_df.writeStream.format("cassandra")...
```

### 5.4 Couche Serving - Implémentation

#### 5.4.1 Grafana

**Datasources provisionnées** :
- InfluxDB (speed layer)
- PostgreSQL (batch layer)

**Dashboards** :
- Speed Dashboard : Température, humidité, vent en temps réel
- Batch Dashboard : Analyses historiques, tendances
- Variables dynamiques : Sélection de ville

#### 5.4.2 API FastAPI (api_server.py)

Endpoints :

```
POST /run : Lancer une requête batch
GET /status/{task_id} : Vérifier le statut
GET /fetch/{task_id} : Récupérer les résultats
GET /speed/latest : Dernières données temps réel
GET /batch/monthly : Moyennes mensuelles
```

#### 5.4.3 Frontend React

Interface avec :
- Filtres de recherche (villes, dates, métriques)
- Graphiques interactifs (Recharts)
- Carte interactive (Leaflet)
- Tables de résultats triables

### 5.5 Intégration et consolidation

Le dossier `consolidation/` unifie les trois couches :

**Docker Compose unique** :
- Réseau partagé `lambda_network`
- 15+ services orchestrés
- Variables d'environnement centralisées
- Volumes persistants

**Configuration unifiée** :
- Telegraf pointe vers le bon InfluxDB
- Grafana connecté aux deux sources
- API backend accède à tout
- Airflow orchestre batch ET speed

---

## 6. Guide de déploiement

### 6.1 Prérequis

**Matériel recommandé** :
- CPU : 4 cœurs minimum (8 recommandés)
- RAM : 8 GB minimum (16 GB recommandés)
- Disque : 20 GB libres
- Réseau : Connexion Internet stable

**Logiciels** :
- Docker Desktop 20.10+
- Docker Compose 2.0+
- Python 3.9+ (optionnel, pour tests)
- Git

**Compte API** :
- Visual Crossing Weather (gratuit jusqu'à 1000 requêtes/jour)

### 6.2 Installation étape par étape

**Étape 1 : Cloner le dépôt**

```bash
git clone <url_du_depot>
cd Architecture-Big-Data/consolidation
```

**Étape 2 : Configurer l'environnement**

```bash
# Copier le template
cp env.example .env

# Éditer le fichier .env
# Ajouter votre clé API Visual Crossing
nano .env
```

**Étape 3 : Démarrer les services**

```bash
# Lancer tous les conteneurs
docker-compose up -d

# Vérifier le statut
docker-compose ps

# Suivre les logs
docker-compose logs -f
```

Temps d'initialisation : 3-5 minutes pour que tous les services soient opérationnels.

**Étape 4 : Vérifier le déploiement**

```bash
# Vérifier Airflow
curl http://localhost:8080/health

# Vérifier Grafana
curl http://localhost:3000/api/health

# Vérifier Kafka
docker exec broker kafka-topics --bootstrap-server localhost:9092 --list
```

### 6.3 Accès aux interfaces

| Service | URL | Identifiants |
|---------|-----|--------------|
| Airflow | http://localhost:8080 | admin / admin |
| Grafana | http://localhost:3000 | admin / admin12345 |
| Spark Master | http://localhost:9090 | - |
| Kafka Control Center | http://localhost:9021 | - |
| HDFS NameNode | http://localhost:9871 | - |
| InfluxDB | http://localhost:8086 | admin / admin12345 |
| API Backend | http://localhost:8000 | - |

### 6.4 Lancement des traitements

**Batch Layer** :

```bash
# Via Airflow UI
1. Accéder à http://localhost:8080
2. Activer le DAG "weather_batch_processing"
3. Déclencher manuellement ou attendre le schedule

# Via CLI
docker exec airflow-webserver airflow dags trigger weather_batch_processing
```

**Speed Layer** :

```bash
# Lancer le producteur Kafka
python scripts/kafka_producer.py --continuous --interval 60

# Ou via le DAG Airflow
# Activer "kafka_weather_stream"
```

**Vérification des données** :

```bash
# HDFS
docker exec hdfs-namenode hdfs dfs -ls /user/spark/weather/raw

# InfluxDB
docker exec influxdb influx query 'from(bucket:"speed_bucket") |> range(start:-1h) |> count()'

# PostgreSQL
docker exec -it postgres-batch psql -U weather -d weather_db -c "SELECT COUNT(*) FROM weather_data;"
```

### 6.5 Visualisation dans Grafana

1. Accéder à http://localhost:3000
2. Login : admin / admin12345
3. Naviguer vers Dashboards
4. Sélectionner "Speed Layer Dashboard" ou "Batch Dashboard"
5. Utiliser les filtres de ville et de période

---

## 7. Difficultés rencontrées

### 7.1 Gestion de la clé API

**Problème** : Limitation de 1000 requêtes/jour sur l'API Visual Crossing.

**Impact** : Impossibilité de récupérer des données historiques massives pour toutes les villes.

**Solution adoptée** :
- Limitation à 5 villes françaises stratégiques
- Mise en cache des données dans HDFS
- Fallback sur simulation de données si quota atteint
- Implémentation d'un retry avec backoff exponentiel

### 7.2 Synchronisation HDFS et Spark

**Problème** : Spark n'arrivait pas à écrire dans HDFS au démarrage.

**Cause** : HDFS NameNode en mode "safe mode" au démarrage, permissions insuffisantes.

**Solution** :
- Ajout de healthchecks sur HDFS
- Script d'initialisation pour créer les répertoires
- Configuration explicite de `fs.defaultFS` dans Spark
- Attente de HDFS dans le DAG Airflow

### 7.3 Parsing des timestamps

**Problème** : Incohérences temporelles entre les différentes sources de données.

**Cause** : Formats de timestamps différents (ISO 8601, epoch, RFC3339).

**Solution** :
- Standardisation sur RFC3339 UTC avec suffixe Z
- Parsing explicite dans Telegraf
- Conversion systématique dans les scripts Python
- Validation des timestamps dans les tests

### 7.4 Mémoire Spark

**Problème** : Out of Memory lors du traitement de datasets volumineux.

**Cause** : Configuration par défaut insuffisante pour les workers Spark.

**Solution** :
- Augmentation de `SPARK_WORKER_MEMORY` à 1GB
- Partitionnement des données par ville
- Utilisation du format Parquet (compression)
- Nettoyage régulier des fichiers temporaires

### 7.5 Conflits de ports

**Problème** : Plusieurs services voulaient utiliser le port 8080.

**Cause** : Airflow, Spark UI et autres services en conflit.

**Solution** :
- Spark UI mappé sur 9090
- Documentation claire des ports utilisés
- Vérification des ports avant démarrage
- Flexibilité dans le docker-compose

### 7.6 Intégration Grafana

**Problème** : Dashboards perdus après redémarrage de Grafana.

**Cause** : Configuration manuelle non persistée.

**Solution** :
- Provisioning as code (YAML + JSON)
- Volumes persistants pour Grafana
- Dashboards versionnés dans Git
- `allowUiUpdates=false` pour garantir cohérence

### 7.7 Dépendances Python

**Problème** : Versions incompatibles entre Airflow, Spark et les scripts.

**Cause** : Multiples fichiers `requirements.txt` non synchronisés.

**Solution** :
- Requirements.txt consolidé
- Installation dans les images Docker
- Tests d'intégration avant déploiement
- Documentation des versions exactes

### 7.8 Réseau Docker

**Problème** : Services ne se trouvaient pas entre eux.

**Cause** : Réseaux Docker différents entre batch, speed et front.

**Solution** :
- Réseau unique `lambda_network`
- Noms de services cohérents et documentés
- DNS Docker pour la résolution
- Tests de connectivité entre services

---

## 8. Apprentissages

### 8.1 Architecture distribuée

**Architecture Lambda en pratique**

La mise en œuvre concrète de l'architecture Lambda nous a permis de comprendre :
- L'importance de séparer les traitements batch et streaming
- Les compromis latence/précision inhérents à chaque couche
- La complexité de fusionner deux vues des données
- Les bénéfices d'une architecture tolérante aux pannes

**Coordination de services distribués**

Orchestrer 15+ services Docker nous a appris :
- L'importance des healthchecks et dépendances
- La gestion des ordres de démarrage
- Les stratégies de retry et timeout
- La nécessité d'une bonne observabilité

### 8.2 Technologies Big Data

**Apache Spark**

Apprentissages sur Spark :
- PySpark pour le traitement distribué en Python
- Optimisations : partitionnement, broadcast, cache
- Gestion de la mémoire et du garbage collection
- Intégration avec HDFS et formats optimisés (Parquet)

**Apache Kafka**

Compréhensions clés :
- Architecture producteur/consommateur découplée
- Notion de topics, partitions et consumer groups
- Garanties de livraison (at-least-once, exactly-once)
- Performance et tuning (batch size, linger time)

**HDFS**

Concepts maîtrisés :
- Architecture NameNode/DataNode
- Réplication et tolérance aux pannes
- Organisation hiérarchique des données
- Intégration avec l'écosystème Hadoop

**Apache Airflow**

Compétences acquises :
- Définition de DAGs et dépendances
- Gestion de l'état et des retries
- Variables et connexions
- Monitoring et debugging des workflows

### 8.3 Bases de données spécialisées

**InfluxDB (Time-Series)**

Apprentissages :
- Optimisation pour les séries temporelles
- Langage Flux pour les requêtes
- Tags vs Fields
- Stratégies de rétention

**Cassandra (NoSQL distribuée)**

Concepts découverts :
- Architecture sans master
- Modélisation orientée requêtes
- Cohérence éventuelle
- Performance en écriture

**PostgreSQL (Relationnelle)**

Utilisation pour :
- Requêtes analytiques complexes
- Jointures et agrégations
- Intégration BI (Grafana)
- Indexation et optimisation

### 8.4 DevOps et conteneurisation

**Docker & Docker Compose**

Maîtrise de :
- Création d'images multi-stages
- Gestion des volumes et réseaux
- Variables d'environnement et secrets
- Orchestration de services complexes

**Infrastructure as Code**

Pratiques adoptées :
- Configuration versionnée (Git)
- Provisioning automatique (Grafana)
- Reproductibilité des environnements
- Documentation technique

### 8.5 Programmation et bonnes pratiques

**Python pour le Big Data**

Compétences renforcées :
- Scripts robustes avec retry et error handling
- Logging structuré et debuggable
- Gestion des APIs avec rate limiting
- Code modulaire et réutilisable

**Documentation et communication**

Importance de :
- Documentation technique claire et à jour
- Diagrammes d'architecture
- Guides d'installation détaillés
- Exemples de commandes pratiques

### 8.6 Analyse de données

**Métriques météorologiques**

Compréhension de :
- Variables climatiques (température, pression, humidité)
- Corrélations entre phénomènes
- Saisonnalité et tendances
- Détection d'anomalies

**Visualisation**

Apprentissages sur :
- Choix des types de graphiques adaptés
- Dashboards interactifs et ergonomiques
- Couleurs et lisibilité
- Variables dynamiques et filtres

### 8.7 Gestion de projet

**Méthodologie**

Leçons apprises :
- Importance de tests à chaque étape
- Développement itératif par couche
- Documentation continue
- Gestion des blocages et pivots

**Travail collaboratif**

Si en équipe :
- Coordination sur Git (branches, merges)
- Revue de code
- Communication sur les dépendances
- Partage de connaissance

---

## 9. Conclusion

### 9.1 Bilan du projet

Ce projet nous a permis de mettre en pratique les concepts théoriques de l'architecture Lambda et de l'écosystème Big Data. Nous avons réussi à déployer un système complet et fonctionnel capable de :

- Collecter des données météorologiques réelles via API
- Les traiter en batch pour des analyses historiques
- Les ingérer en temps réel pour un monitoring continu
- Les visualiser de manière unifiée dans Grafana
- Orchestrer l'ensemble via Airflow

L'architecture déployée est robuste, scalable et maintenable. Elle démontre la puissance de l'approche Lambda pour traiter simultanément des besoins batch et streaming.

### 9.2 Objectifs atteints

Tous les objectifs initiaux ont été remplis :

- Architecture Lambda complète (3 couches fonctionnelles)
- Collecte de données réelles (Visual Crossing API)
- Traitement batch (Spark + HDFS + PostgreSQL)
- Traitement streaming (Kafka + InfluxDB + Cassandra)
- Visualisation unifiée (Grafana multi-sources)
- Orchestration (Airflow avec DAGs)
- Isolation (Docker Compose avec 15+ services)
- Documentation (README + Rapport technique)

### 9.3 Points forts de la solution

**Modularité** : Chaque couche peut évoluer indépendamment.

**Scalabilité** : Architecture distribuée prête pour la montée en charge.

**Résilience** : Redondance des stockages, retry automatiques.

**Flexibilité** : Double pipeline speed (Telegraf et Spark Streaming).

**Observabilité** : Monitoring complet via Airflow, Grafana et logs.

### 9.4 Limites et améliorations possibles

**Limites actuelles** :

1. Pas de haute disponibilité (single node)
2. Sécurité basique (mots de passe en clair)
3. Pas d'alerting automatique
4. Volume de données limité par l'API gratuite
5. Pas de tests automatisés

**Améliorations envisageables** :

**Court terme** :
- Alerting Grafana sur anomalies
- Tests unitaires et d'intégration
- CI/CD avec GitHub Actions
- Monitoring des ressources (Prometheus)

**Moyen terme** :
- Authentification et RBAC
- Chiffrement des communications (SSL/TLS)
- Backup automatisé des données
- Documentation API avec Swagger

**Long terme** :
- Déploiement Kubernetes
- Cluster Spark multi-nœuds
- Machine Learning pour prévisions
- Data Lake avec Delta Lake

### 9.5 Compétences acquises

Ce projet a permis de développer des compétences sur :

**Technique** :
- Architecture distribuée et Big Data
- Technologies Hadoop, Spark, Kafka
- Orchestration Airflow
- Visualisation Grafana
- Conteneurisation Docker

**Méthodologie** :
- Infrastructure as Code
- Documentation technique
- Débogage de systèmes distribués
- Gestion de dépendances complexes

**Analyse** :
- Traitement de données temporelles
- Agrégations et statistiques
- Visualisation de métriques
- Détection de patterns

### 9.6 Perspectives professionnelles

Les compétences acquises sont directement applicables dans :

- Ingénierie de données (Data Engineering)
- Architecture Big Data
- DevOps et SRE
- Développement de pipelines ETL
- Projets IoT et time-series

L'expérience pratique d'orchestrer plusieurs technologies distribuées est particulièrement valorisable dans le monde professionnel.

### 9.7 Mot de fin

Ce projet a été une expérience enrichissante qui nous a confrontés à la complexité réelle des systèmes Big Data en production. Les difficultés rencontrées nous ont permis de développer notre capacité à débugger, chercher des solutions et adapter notre approche.

L'architecture Lambda s'est révélée être un pattern puissant pour répondre à des besoins mixtes batch/streaming. Sa mise en œuvre concrète nous a fait prendre conscience des compromis inhérents à toute architecture distribuée.

Nous sommes satisfaits du résultat obtenu : un système fonctionnel, documenté et démontrable qui illustre les concepts fondamentaux du Big Data moderne.

---

**Date de réalisation** : Septembre 2025
**Technologies** : Spark, Kafka, Airflow, HDFS, InfluxDB, Grafana, Docker
**Architecture** : Lambda (Batch + Speed + Serving)
