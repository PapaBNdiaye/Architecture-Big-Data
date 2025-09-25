# Frontend Panneau de Filtrage - Architecture Big Data

Interface React moderne pour le traitement batch des données météorologiques avec architecture Lambda.

## 🚀 Fonctionnalités

- **Filtrage avancé** : Villes, périodes, métriques, granularité
- **Tableau triable** : Résultats avec pagination et tri multi-colonnes
- **Graphiques interactifs** :
  - Évolution des températures moyennes
  - Précipitations par mois
  - Amplitude thermique
- **Carte interactive** : Clic sur les villes pour détails
- **Monitoring temps réel** : WebSocket pour le statut des tâches

## 🛠️ Technologies

- **React 18** + **TypeScript**
- **Vite** pour le développement rapide
- **Ant Design** pour l'interface utilisateur
- **Recharts** pour les graphiques
- **Axios** pour les appels API

## 📦 Installation

```bash
# Installer les dépendances
npm install

# Copier la configuration d'environnement
cp .env.example .env

# Modifier l'URL de l'API dans .env si nécessaire
# VITE_API_BASE=http://localhost:8000
```

## 🚀 Démarrage

```bash
# Mode développement
npm run dev

# Build pour la production
npm run build

# Prévisualisation du build
npm run preview
```

## 🔧 Configuration

### Variables d'environnement

Créer un fichier `.env` à la racine :

```env
VITE_API_BASE=http://localhost:8000
```

### API Backend attendue

Le frontend communique avec un backend qui expose :

- `POST /run` : Lancer un traitement batch
- `GET /status/{taskId}` : Vérifier le statut
- `GET /fetch/{taskId}` : Récupérer les résultats

## 📊 Graphiques

### 1. Températures moyennes
- **Type** : Courbe (LineChart)
- **Données** : `metric_name: "avg_temp_c"`
- **Axes** : Mois × Température (°C)

### 2. Précipitations
- **Type** : Barres groupées
- **Données** : `metric_name: "sum_precip_mm"`
- **Axes** : Mois × Précipitations (mm)

### 3. Amplitude thermique
- **Type** : Barres
- **Données** : `metric_name: "temp_amp_c"`
- **Axes** : Mois × Amplitude (°C)

## 🎯 Utilisation

1. **Configurer les filtres** : Villes, période, métriques
2. **Lancer la requête** : Bouton "Lancer la requête"
3. **Attendre les résultats** : Monitoring automatique du statut
4. **Explorer les données** : Table triable + graphiques
5. **Détails par ville** : Clic sur la carte interactive

## 📄 Licence

Weather Data Provided by [Visual Crossing](https://www.visualcrossing.com/)
