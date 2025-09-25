#!/usr/bin/env python3
"""
Script pour compter les lignes dans les données HDFS
"""

from pyspark.sql import SparkSession

def main():
    spark = SparkSession.builder \
        .appName("CountWeatherData") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    
    # Lire les données Parquet depuis HDFS
    df = spark.read.parquet("hdfs://hdfs-namenode:8020/user/spark/weather/raw/20250925_080649")
    
    # Compter les lignes
    count = df.count()
    columns = len(df.columns)
    
    print(f"📊 Nombre de lignes: {count}")
    print(f"📊 Nombre de colonnes: {columns}")
    print(f"📊 Colonnes: {df.columns}")
    
    # Afficher quelques exemples
    print("\n🔍 Premières lignes:")
    df.show(5)
    
    # Statistiques sur les données
    print("\n📈 Statistiques:")
    df.describe().show()
    
    spark.stop()

if __name__ == "__main__":
    main()
