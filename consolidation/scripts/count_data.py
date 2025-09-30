#!/usr/bin/env python3
"""
Script de vérification et comptage des données HDFS.

Ce script charge les données météo depuis HDFS et affiche
des statistiques de base sur le contenu.
"""

from pyspark.sql import SparkSession
import os
import subprocess

def find_latest_hdfs_directory():
    """Trouve le répertoire le plus récent dans HDFS"""
    try:
        # Utiliser hadoop fs pour lister les répertoires
        cmd = ["hadoop", "fs", "-ls", "/user/spark/weather/raw/"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Parser la sortie pour trouver les répertoires avec des timestamps
        lines = result.stdout.strip().split('\n')
        directories = []
        
        for line in lines:
            if '2025' in line and 'drwx' in line:
                # Extraire le nom du répertoire (dernier élément du chemin)
                path = line.split()[-1]
                dir_name = os.path.basename(path)
                directories.append(dir_name)
        
        if directories:
            # Trier par nom (qui contient le timestamp) et prendre le plus récent
            directories.sort(reverse=True)
            return directories[0]
        else:
            return None
            
    except Exception as e:
        print(f"Erreur lors de la recherche du répertoire HDFS: {e}")
        return None

def main():
    spark = SparkSession.builder \
        .appName("CountWeatherData") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    
    # Trouver le répertoire le plus récent
    latest_dir = find_latest_hdfs_directory()
    
    if latest_dir is None:
        print("Aucun répertoire de données trouvé dans HDFS")
        print("Assurez-vous que le traitement batch a été exécuté")
        spark.stop()
        return
    
    hdfs_path = f"hdfs://hdfs-namenode:8020/user/spark/weather/raw/{latest_dir}"
    print(f"Lecture des données depuis: {hdfs_path}")
    
    try:
        # Lire les données Parquet depuis HDFS
        df = spark.read.parquet(hdfs_path)
    except Exception as e:
        print(f"Erreur lors de la lecture des données: {e}")
        spark.stop()
        return
    
    # Compter les lignes
    count = df.count()
    columns = len(df.columns)
    
    print(f"Nombre de lignes: {count}")
    print(f"Nombre de colonnes: {columns}")
    print(f"Colonnes: {df.columns}")
    
    # Afficher quelques exemples
    print("\nPremières lignes:")
    df.show(5)
    
    # Statistiques sur les données
    print("\nStatistiques:")
    df.describe().show()
    
    spark.stop()

if __name__ == "__main__":
    main()
