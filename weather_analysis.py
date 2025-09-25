#!/usr/bin/env python3
"""
Script d'agrégation et d'analyse des données météo
Répond aux questions d'analyse météo avancées
Exécuté dans l'environnement Docker Spark
"""

from datetime import datetime, timedelta
from pyspark.sql import SparkSession, Row
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.clustering import KMeans
from pyspark.ml.stat import Correlation
import numpy as np

# Import config depuis le répertoire config monté dans Docker
import sys, os
sys.path.append("/opt/spark/project/config")
from cities_config import CITIES, API_CONFIG, get_api_params

class WeatherAnalyzer:
    def __init__(self):
        self.spark = SparkSession.builder \
            .appName("WeatherAnalysisAdvanced") \
            .config("spark.hadoop.fs.defaultFS", "hdfs://hdfs-namenode:8020") \
            .getOrCreate()
        
        self.spark.sparkContext.setLogLevel("WARN")
        
    def load_weather_data(self, hdfs_path=None):
        """Charge les données météo depuis HDFS"""
        if hdfs_path is None:
            # Trouver le répertoire le plus récent
            hdfs_base = "hdfs://hdfs-namenode:8020/user/spark/weather/raw"
            # Pour la démo, on utilise un chemin fixe
            hdfs_path = f"{hdfs_base}/20250925_133714"
        
        print(f"📊 Chargement des données depuis {hdfs_path}")
        
        try:
            df = self.spark.read.parquet(hdfs_path)
            print(f"✅ {df.count()} enregistrements chargés")
            return df
        except Exception as e:
            print(f"❌ Erreur lors du chargement: {e}")
            return None
    
    def analyze_extremes_and_variability(self, df):
        """1. Analyse des extrêmes et variabilité météo"""
        print("\n🌡️  === ANALYSE DES EXTRÊMES ET VARIABILITÉ ===")
        
        # Températures extrêmes par ville
        temp_extremes = df.groupBy("city") \
            .agg(
                avg("temp").alias("temp_moyenne"),
                max("tempmax").alias("temp_max_absolue"),
                min("tempmin").alias("temp_min_absolue"),
                stddev("temp").alias("variabilite_temp"),
                max("precip").alias("precip_max"),
                max("windspeed").alias("vent_max"),
                avg("humidity").alias("humidite_moyenne")
            ) \
            .orderBy(desc("temp_max_absolue"))
        
        print("🏆 Villes avec les températures les plus extrêmes:")
        temp_extremes.show()
        
        # Jours avec conditions extrêmes
        extreme_days = df.filter(
            (col("tempmax") > 35) |  # Vague de chaleur
            (col("tempmin") < -5) |  # Vague de froid
            (col("precip") > 20) |   # Fortes précipitations
            (col("windspeed") > 15)  # Vent fort
        ).orderBy(desc("tempmax"))
        
        print("⚠️  Jours avec conditions météo extrêmes:")
        extreme_days.select("city", "date", "tempmax", "tempmin", "precip", "windspeed").show(20)
        
        return temp_extremes, extreme_days
    
    def analyze_city_comparisons(self, df):
        """2. Comparaisons et benchmarks entre villes"""
        print("\n🏙️  === COMPARAISONS ENTRE VILLES ===")
        
        # Statistiques comparatives par ville
        city_stats = df.groupBy("city") \
            .agg(
                avg("temp").alias("temp_moyenne"),
                avg("precip").alias("precip_moyenne"),
                avg("windspeed").alias("vent_moyen"),
                avg("cloudcover").alias("nuages_moyen"),
                avg("visibility").alias("visibilite_moyenne"),
                count("*").alias("nb_jours")
            ) \
            .orderBy(desc("temp_moyenne"))
        
        print("📊 Comparaison des villes (moyennes):")
        city_stats.show()
        
        # Classements
        rankings = {}
        
        # Ville la plus ensoleillée (moins de nuages)
        sunniest = df.groupBy("city") \
            .agg(avg("cloudcover").alias("nuages_moyen")) \
            .orderBy("nuages_moyen") \
            .first()
        rankings["ensoleillee"] = sunniest["city"]
        
        # Ville la plus pluvieuse
        rainiest = df.groupBy("city") \
            .agg(avg("precip").alias("precip_moyenne")) \
            .orderBy(desc("precip_moyenne")) \
            .first()
        rankings["pluvieuse"] = rainiest["city"]
        
        # Ville la plus venteuse
        windiest = df.groupBy("city") \
            .agg(avg("windspeed").alias("vent_moyen")) \
            .orderBy(desc("vent_moyen")) \
            .first()
        rankings["venteuse"] = windiest["city"]
        
        print("🏆 Classements des villes:")
        print(f"☀️  Plus ensoleillée: {rankings['ensoleillee']}")
        print(f"🌧️  Plus pluvieuse: {rankings['pluvieuse']}")
        print(f"💨 Plus venteuse: {rankings['venteuse']}")
        
        return city_stats, rankings
    
    def analyze_correlations_and_patterns(self, df):
        """3. Corrélations et patterns météo"""
        print("\n🔗 === CORRÉLATIONS ET PATTERNS ===")
        
        # Préparation des données pour l'analyse de corrélation
        correlation_data = df.select(
            "temp", "humidity", "precip", "windspeed", 
            "pressure", "cloudcover", "visibility"
        ).na.drop()
        
        # Conversion en vecteur pour l'analyse de corrélation
        assembler = VectorAssembler(
            inputCols=["temp", "humidity", "precip", "windspeed", "pressure", "cloudcover", "visibility"],
            outputCol="features"
        )
        
        vector_data = assembler.transform(correlation_data)
        
        # Calcul de la matrice de corrélation
        correlation_matrix = Correlation.corr(vector_data, "features").head()[0]
        
        print("📈 Matrice de corrélation:")
        features = ["temp", "humidity", "precip", "windspeed", "pressure", "cloudcover", "visibility"]
        corr_array = correlation_matrix.toArray()
        
        for i, feature1 in enumerate(features):
            for j, feature2 in enumerate(features):
                if i < j:  # Éviter les doublons
                    corr_value = corr_array[i][j]
                    print(f"{feature1} ↔ {feature2}: {corr_value:.3f}")
        
        # Clustering météo par ville
        print("\n🎯 Clustering des villes par conditions météo:")
        
        city_weather = df.groupBy("city") \
            .agg(
                avg("temp").alias("temp_moyen"),
                avg("humidity").alias("humidity_moyen"),
                avg("precip").alias("precip_moyen"),
                avg("windspeed").alias("windspeed_moyen")
            )
        
        # Assemblage pour clustering
        cluster_assembler = VectorAssembler(
            inputCols=["temp_moyen", "humidity_moyen", "precip_moyen", "windspeed_moyen"],
            outputCol="weather_features"
        )
        
        cluster_data = cluster_assembler.transform(city_weather)
        
        # K-means clustering
        kmeans = KMeans(k=2, seed=1, featuresCol="weather_features")
        model = kmeans.fit(cluster_data)
        predictions = model.transform(cluster_data)
        
        print("Clusters météo:")
        predictions.select("city", "prediction").show()
        
        return correlation_matrix, predictions
    
    def analyze_risks_and_projections(self, df):
        """4. Analyse des risques et projections"""
        print("\n⚠️  === ANALYSE DES RISQUES ET PROJECTIONS ===")
        
        # Identification des périodes à risque
        risk_periods = df.filter(
            (col("tempmax") > 35) |  # Risque de chaleur
            (col("tempmin") < -5) |  # Risque de froid
            (col("precip") > 15) |   # Risque de précipitations
            (col("windspeed") > 12)  # Risque de vent fort
        ).orderBy(desc("date"))
        
        print("🚨 Périodes à risque identifiées:")
        risk_periods.select("city", "date", "tempmax", "tempmin", "precip", "windspeed").show(10)
        
        # Analyse des tendances par mois
        monthly_trends = df.withColumn("month", month("date")) \
            .groupBy("city", "month") \
            .agg(
                avg("temp").alias("temp_moyenne"),
                avg("precip").alias("precip_moyenne"),
                avg("windspeed").alias("vent_moyen")
            ) \
            .orderBy("city", "month")
        
        print("📅 Tendances mensuelles:")
        monthly_trends.show(20)
        
        return risk_periods, monthly_trends
    
    def analyze_energy_agriculture(self, df):
        """5. Analyses énergie et agriculture"""
        print("\n🌱 === ANALYSES ÉNERGIE ET AGRICULTURE ===")
        
        # Calcul des degrés-jours (approximation)
        df_with_degree_days = df.withColumn(
            "heating_degree_days", 
            when(col("temp") < 18, 18 - col("temp")).otherwise(0)
        ).withColumn(
            "cooling_degree_days",
            when(col("temp") > 24, col("temp") - 24).otherwise(0)
        )
        
        # Analyse par ville
        energy_analysis = df_with_degree_days.groupBy("city") \
            .agg(
                avg("heating_degree_days").alias("degres_chauffage_moyen"),
                avg("cooling_degree_days").alias("degres_climatisation_moyen"),
                avg("temp").alias("temp_moyenne"),
                avg("cloudcover").alias("nuages_moyen")
            )
        
        print("⚡ Analyse énergétique par ville:")
        energy_analysis.show()
        
        # Potentiel solaire (approximation basée sur la couverture nuageuse)
        solar_potential = df.groupBy("city") \
            .agg(
                avg("cloudcover").alias("nuages_moyen"),
                avg("visibility").alias("visibilite_moyenne")
            ) \
            .withColumn("potentiel_solaire", 100 - col("nuages_moyen"))
        
        print("☀️  Potentiel solaire par ville:")
        solar_potential.show()
        
        return energy_analysis, solar_potential
    
    def generate_summary_report(self, results):
        """Génère un rapport de synthèse"""
        print("\n📋 === RAPPORT DE SYNTHÈSE ===")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Sauvegarde des résultats dans HDFS
        output_path = f"hdfs://hdfs-namenode:8020/user/spark/weather/analysis/{timestamp}"
        
        for name, data in results.items():
            if data is not None:
                # Si c'est un tuple, sauvegarder chaque élément
                if isinstance(data, tuple):
                    for i, df in enumerate(data):
                        if hasattr(df, 'write'):  # Vérifier que c'est un DataFrame
                            df.write.mode("overwrite").parquet(f"{output_path}/{name}_{i}")
                            print(f"✅ {name}_{i} sauvegardé dans {output_path}/{name}_{i}")
                else:
                    # Si c'est un DataFrame simple
                    if hasattr(data, 'write'):
                        data.write.mode("overwrite").parquet(f"{output_path}/{name}")
                        print(f"✅ {name} sauvegardé dans {output_path}/{name}")
        
        print(f"\n🎯 Toutes les analyses sont disponibles dans: {output_path}")
        
        return output_path
    
    def run_complete_analysis(self, hdfs_path=None):
        """Exécute l'analyse complète"""
        print("🚀 Démarrage de l'analyse météo complète...")
        
        # Chargement des données
        df = self.load_weather_data(hdfs_path)
        if df is None:
            return None
        
        # Exécution de toutes les analyses
        results = {}
        
        try:
            results["extremes"] = self.analyze_extremes_and_variability(df)
            results["comparisons"] = self.analyze_city_comparisons(df)
            results["correlations"] = self.analyze_correlations_and_patterns(df)
            results["risks"] = self.analyze_risks_and_projections(df)
            results["energy"] = self.analyze_energy_agriculture(df)
            
            # Génération du rapport
            output_path = self.generate_summary_report(results)
            
            print("\n✅ Analyse complète terminée!")
            return output_path
            
        except Exception as e:
            print(f"❌ Erreur lors de l'analyse: {e}")
            return None
        
        finally:
            self.spark.stop()

def main():
    print("🌤️  ANALYSE MÉTÉO BIG DATA")
    print("=" * 50)
    
    analyzer = WeatherAnalyzer()
    output_path = analyzer.run_complete_analysis()
    
    if output_path:
        print(f"\n🎉 Analyse terminée! Résultats dans: {output_path}")
        print("\n💡 Pour utiliser le frontend web:")
        print("   python weather_frontend.py")
    else:
        print("\n❌ Échec de l'analyse")

if __name__ == "__main__":
    main()
