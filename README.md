# Projet Couche Speed : Ingestion, Traitement Temps Réel et Visualisation Météo

## 1. Objectif du Projet

Mettre en place une chaîne de traitement temps réel (architecture de type Lambda – composante Speed Layer) pour des données météorologiques réelles :
1. Récupération périodique des données météo de plusieurs villes via une API publique (Visual Crossing ou simulation de secours).
2. Ingestion fiable dans Kafka (topic principal `weather_data_v2`).
3. Enrichissement et normalisation (attributs dérivés : indicateurs de pluie / orage, prévisions heure suivante, origine des données, format temporel RFC3339).
4. Consommation et mise à disposition pour analyse et visualisation via Telegraf → InfluxDB (série temporelle) → Grafana (tableau de bord temps réel).
5. Possibilité de traitement batch/analytique ultérieur (non couvert ici) et extension vers Spark / Cassandra (version précédente conservée dans `readme/README_lancement_et_debug.md`).

Ce document constitue la documentation de référence (rapport) pour l'installation, l'architecture fonctionnelle, les décisions techniques et l'exploitation.

## 2. Vue d'Architecture Logique

Flux principal :
Producteur Python → Kafka (topic `weather_data_v2`) → Telegraf (consumer Kafka + mapping JSON) → InfluxDB (bucket `speed_bucket`) → Grafana (tableau de bord provisionné)

Eléments :
- Producteur Python : collecte API + enrichissement.
- Kafka : buffer / découplage, résilience aux pics.
- Telegraf : transformation légère, parsing timestamp, insertion Influx.
- InfluxDB : stockage série temporelle optimisé pour requêtes temporelles.
- Grafana : visualisation et monitoring opérationnel (panels, variable ville, heartbeat, fraîcheur des données).

## 3. Schéma des Données Produites

Message JSON (topic `weather_data_v2`) – champs principaux :
- `city` (string)
- `country` (string)
- `station_id` (string) identifiant logique / agrégé
- `timestamp` (string RFC3339 UTC, ex: 2025-09-26T14:05:00Z)
- `temperature` (float °C)
- `humidity` (float %)
- `wind_speed` (float km/h ou m/s selon source normalisée)
- `precipitation` (float mm/h)
- `next_hour_temp` (float °C) prévision simple
- `next_hour_precip` (float mm) prévision simple
- `is_rain` (int 0/1)
- `is_storm` (int 0/1)
- `data_origin` (string: api|simulated)

InfluxDB (measurement `weather`) :
- Tags : `city`, `country`, `station_id`, `data_origin`
- Fields : numériques ci-dessus + dérivés
- Timestamp : valeur du champ JSON `timestamp` parsé (et non l'heure d'ingestion) afin de préserver l'alignement temporel réel.

## 4. Détails Techniques par Composant

### 4.1 Producteur (`kafka_producer.py`)
Fonctions clés :
- Récupération API (Visual Crossing) multi‑villes → fallback simulation si échec réseau/API.
- Enrichissement :
	- `is_rain` = 1 si `precipitation > 0`.
	- `is_storm` heuristique (ex : pluie + intensité ou condition orage détectée par API si exposée).
	- Prévisions approximatives prochaine heure (`next_hour_temp`, `next_hour_precip`).
	- Ajout `data_origin`.
- Formatage timestamp en UTC RFC3339 (suffixe Z) pour ingestion déterministe.
- Mode continu (option `--continuous`) avec intervalle configurable (`--interval` secondes).
- Gestion signaux (CTRL+C) pour arrêt propre.

Paramètres principaux (CLI) :
```
python kafka_producer.py --continuous --interval 60
```
Options additionnelles : `--num` (nombre de messages et arrêt si non continu).

### 4.2 Kafka
- Topic actif : `weather_data_v2` (ancien `weather_data` conservé uniquement pour historique / éviter collisions de schéma).
- Rôle : tampon, découplage producteur / pipeline d'observabilité.

### 4.3 Telegraf
- Input `kafka_consumer` avec `json_v2` mapping.
- Parsing explicite :
	- `timestamp_path = "timestamp"`
	- `timestamp_format = "2006-01-02T15:04:05Z07:00"`
- Transformation champs → measurement `weather`.
- Output vers InfluxDB (bucket `speed_bucket`).
- (Mode debug possible : file output — à désactiver en production pour éviter duplication.)

### 4.4 InfluxDB
- Bucket : `speed_bucket` (organisation `speed_org`).
- Token / auth gérés via provisioning environnement (non versionné dans ce dépôt – utiliser variables locales).
- Stockage index temporel pour requêtes Flux utilisées par Grafana.

### 4.5 Grafana
Provisioning :
- Datasource InfluxDB (UID stable `influxdb`).
- Dashboard versionné (JSON) non modifiable via UI (paramètre `allowUiUpdates=false`).

Panels principaux :
- Séries : Température, Humidité, Vent, Précipitations, Température prévue.
- Indicateurs booléens pluie / orage (affichent 0 ou 1 maintenant sans icônes).
- Compteur messages dernière minute (heartbeat pipeline).
- Âge de la dernière mesure (fraîcheur en secondes).
- Table debug (peut être retirée après validation fonctionnelle).

Variable : `city` (sélection dynamique multi‑ville via tag values + filtrage regex dans requêtes Flux).

## 5. Processus d'Installation et Lancement

### 5.1 Prérequis Logiciels
- Docker & Docker Compose
- Python >= 3.9
- Accès Internet (API temps réel) – sinon fallback simulation interne.

### 5.2 Clonage et Préparation
```bash
git clone <url-du-repo>
cd speed_layer
python -m venv venv
venv\Scripts\activate  # Windows
# ou source venv/bin/activate (Linux/Mac)
pip install -r requirements.txt
```

### 5.3 Démarrage des Services de Base
```bash
docker-compose up -d
```
Attendre que tous les conteneurs passent en statut healthy (Kafka, InfluxDB, Grafana, Telegraf si conteneurisé, etc.).

### 5.4 Lancement du Producteur en Continu
Windows (script si fourni) :
```powershell
./start_producer.bat
```
Ou manuel :
```powershell
python kafka_producer.py --continuous --interval 300
```

### 5.5 Vérification InfluxDB (optionnel via UI ou API)
- Vérifier qu'une mesure `weather` contient des points récents.

### 5.6 Accès Grafana
- URL locale : http://localhost:3000
- Tableau de bord provisionné automatiquement : sélectionner (Weather / Speed Layer) selon titre configuré.
- Changer la variable `city` pour filtrer.

## 6. Référence des Commandes (Docker / Spark / Kafka / Cassandra)

Cette section structure et documente les commandes opérationnelles. Elle remplace la liste brute initiale.

### 6.1 Spark
- Lancer le job (détaché) :
```bash
docker exec -d speed_layer-spark-master-1 spark-submit \
	--packages com.datastax.spark:spark-cassandra-connector_2.12:3.4.1,org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1 \
	/opt/bitnami/spark/spark_streaming.py
```
- Vérifier qu'il tourne :
```bash
docker exec speed_layer-spark-master-1 ps aux | grep spark-submit
```
- Liste complète des processus :
```bash
docker exec speed_layer-spark-master-1 ps aux
```
- Logs Spark :
```bash
docker logs speed_layer-spark-master-1
```
- Installer dépendance (unique) :
```bash
docker exec speed_layer-spark-master-1 pip install cassandra-driver
```

### 6.2 Cassandra (CQLSH)
- Compter les enregistrements :
```bash
docker exec cassandra cqlsh -e "SELECT COUNT(*) FROM spark_streams.weather_data;"
```
- Échantillon :
```bash
docker exec cassandra cqlsh -e "SELECT station_id, city, temperature, timestamp FROM spark_streams.weather_data LIMIT 10;"
```
- Schéma keyspaces :
```bash
docker exec cassandra cqlsh -e "DESCRIBE KEYSPACES;"
```
- Schéma table :
```bash
docker exec cassandra cqlsh -e "DESCRIBE spark_streams.weather_data;"
```
- Dernières lignes (selon clé de clustering) :
```bash
docker exec cassandra cqlsh -e "SELECT * FROM spark_streams.weather_data ORDER BY timestamp DESC LIMIT 10;"
```

### 6.3 Kafka
- Lister les topics :
```bash
docker exec broker kafka-topics --bootstrap-server localhost:9092 --list
```
- Redémarrer broker :
```bash
docker-compose restart broker
```
- Redémarrer ZooKeeper (rare) :
```bash
docker-compose restart zookeeper
```
- Logs broker :
```bash
docker logs broker
```

### 6.4 Docker (Général)
- Démarrer toute la stack :
```bash
docker-compose up -d
```
- Arrêter (conserver données) :
```bash
docker-compose down
```
- Arrêt + purge volumes (DESTRUCTIF) :
```bash
docker-compose down -v
```
ATTENTION : cette purge supprime les volumes (perte de données persistées).

- Redémarrer un service :
```bash
docker-compose restart <nom_du_service>
```
- Statut :
```bash
docker-compose ps
```
- Logs agrégés continus :
```bash
docker-compose logs -f
```
- Logs d'un service :
```bash
docker logs cassandra
```

### 6.5 Temporisation
Linux / Mac :
```bash
sleep 120
```
PowerShell (Windows) :
```powershell
Start-Sleep -Seconds 120
```
(Remplace l'usage impropre de `timeout 120`).

### 6.6 Fiche Diagnostic Rapide
Symptôme | Étapes
---------|-------
Pas de nouveaux points Grafana | Vérifier producteur (mode --continuous), lister topics Kafka, vérifier Telegraf, interroger Influx/Cassandra.
Compteur messages/min = 0 | Producteur arrêté ou intervalle trop long.
Âge dernière mesure élevé | Producteur inactif ou retard API.
Topic absent | Vérifier `kafka-topics --list`, redémarrer broker.
Erreurs Spark | Lire logs Spark, dépendances manquantes, schéma inattendu.

---

## 7. Flux des Requêtes (Exemple Flux Simplifié)
Filtre type utilisé dans panels :
```
from(bucket: "speed_bucket")
	|> range(start: -1h)
	|> filter(fn: (r) => r._measurement == "weather" and r.city =~ /${city:regex}/)
	|> filter(fn: (r) => r._field == "temperature")
```

Panel pluie / orage : identique mais champ `_field` = `is_rain` ou `is_storm` et fenêtre `range` élargie (ex -2h) pour rendre les événements rares visibles.

Calcul âge dernière mesure :
```
... |> last() |> map(fn: (r) => ({ r with age_seconds: int(v: now() - r._time)/1000000000 }))
```

## 8. Supervision et Exploitation

Indicateurs essentiels :
- Heartbeat (messages sur dernière minute) > 0.
- Age dernière mesure < (intervalle producteur * 2).
- Absence de dérive de temps : vérifier ordre chronologique dans Influx.

Actions courantes :
```powershell
docker-compose ps           # Statut conteneurs
docker-compose logs -f      # Suivi live
docker logs <service>       # Logs ciblés
```

## 9. Dépannage Spécifique (Compléments)
- Pas de points dans Grafana mais présents dans Influx : vérifier variable `city` (regex vide ou non correspondante).
- Timestamps incohérents : confirmer parsing actif dans config Telegraf (champ `timestamp_format`).
- Doublons de schéma : s'assurer que seul `weather_data_v2` est consommé.
- Valeurs pluie/orage toujours 0 : vérifier API (météo réellement sèche) vs simulation; tester en forçant une précipitation dans code pour validation.

## 10. Sécurité et Bonnes Pratiques
- Ne pas commiter la clé API (utiliser variable d'environnement `VISUAL_CROSSING_API_KEY`).
- Surveiller la fréquence d'appel (respect des limites API).
- Mettre en place une rotation token InfluxDB en production.

## 11. Évolutions Futures Potentielles
- Ajout d'alerting (Grafana Alert Rules) sur absence de données (> X minutes).
- Intégration Spark + Cassandra (déjà prototypé – voir fichier historique) pour requêtes analytiques.
- Normalisation unités (vent m/s → km/h) centralisée.
- Ajout d'un panneau rose des vents (wind direction + buckets).
- Export vers Data Lake (parquet) pour batch.

## 12. Structure Répertoire (Résumé Actuel)
```
docker-compose.yml
grafana-provisioning/ (datasource + dashboard JSON)
telegraf/ (config consommation Kafka → InfluxDB)
kafka_producer.py
spark_streaming.py (héritage / extension batch temps réel)
scripts/*.bat | *.sh
readme/README_lancement_et_debug.md (ancien guide)
README.md (présent document)
```

## 13. Validation Fonctionnelle Checklist
- [ ] Kafka topic `weather_data_v2` créé automatiquement (ou via script) et reçoit des messages.
- [ ] Telegraf journalise absence d'erreurs et écrit dans InfluxDB.
- [ ] Dashboard Grafana charge les panels sans erreur Flux.
- [ ] Variable `city` propose toutes les villes attendues.
- [ ] Heartbeat > 0 après 1 minute de fonctionnement continu.
- [ ] Age dernière mesure cohérent (< 2 * intervalle producteur).

## 14. Notes de Conception
Choix InfluxDB vs Cassandra pour visualisation rapide : latence lecture/agrégation et opérateurs Flux adaptés aux panneaux de monitoring. Cassandra reste pertinent pour rétention longue / analytics (non contradictoire : architectures hybrides possibles).

Gestion du temps : adoption d'horodatage source → évite distorsion lors de retards réseau; nécessite confiance dans l'API ou fallback cohérent.

Provisioning Grafana verrouillé (`allowUiUpdates=false`) pour garantir reproductibilité (infra as code) – modifications se font par édition JSON versionnée.

## 15. Licence / Crédits
Projet académique / démonstration pédagogique. L'API météo Visual Crossing est soumise à ses propres conditions d'utilisation.

---
Pour les détails d'exécution Spark + Cassandra antérieurs : consulter `readme/README_lancement_et_debug.md`.