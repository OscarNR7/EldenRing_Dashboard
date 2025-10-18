import os
import glob
import pandas as pd
import numpy as np
from pathlib import Path
from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    logger.error("MONGO_URI no configurada")
    exit()

class DataCleaner:
    '''Clase para limpiar y cargar datos en MongoDB'''
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client['eldenring_db']
        logger.info("Conexión a MongoDB establecida.")
    
    def base_cleaning(self, df: pd.DataFrame, name: str) -> pd.DataFrame:
        '''Limpieza basica de datos'''
        df.columns = df.columns.str.strip()
        df = df.replace({'': None, 'nan': None})
        df = df.where(pd.notna(df), None)
        df = df.drop_duplicates(keep='first')
        logger.info(f"{name}: {len(df)} registros")
        return df
    
    def parse_json(self, df: pd.DataFrame, cols: list) -> pd.DataFrame:
        '''Parsea columnas con datos JSON'''
        for col in cols:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: json.loads(x) if pd.notna(x) and isinstance(x,str)else None)
        return df
    
    def parse_list(self, df: pd.DataFrame, cols: list) -> pd.DataFrame:
        '''Parsea columnas con listas'''
        for col in cols:
            if col in df.columns:
               df[col] = df[col].apply(lambda x: eval(x) if pd.notna(x) and isinstance(x,str) else None)
        return df
    
    def numeric_conversion(self, df: pd.DataFrame, cols: list) -> pd.DataFrame:
        for col in cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    
    def clean_ammo(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.base_cleaning(df, 'ammo')
        df = self.parse_json(df, ['attack', 'defence'])
        df = self.numeric_conversion(df, ['weight'])
        return df
    
    def clean_armor(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.base_cleaning(df, 'armor')
        df = self.parse_json(df, ['defence', 'resistances'])
        df = self.numeric_conversion(df, ['weight'])
        return df
    
    def clean_ashes_of_war(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.base_cleaning(df, 'ashes_of_war')
        return df
    
    def clean_spells(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.base_cleaning(df, 'spells')
        return df
    
    def clean_spirit_ashes(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.base_cleaning(df, 'spirit_ashes')
        df = self.numeric_conversion(df, ['level'])
        return df
    
    def clean_npcs(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.base_cleaning(df, 'npcs')
        return df
    
    def clean_items(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.base_cleaning(df, 'items')
        return df
    
    def clean_upgrades(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.base_cleaning(df, 'upgrades')
        df = self.numeric_conversion(df, ['cost'])
        return df
    
    def clean_status_effects(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.base_cleaning(df, 'status_effects')
        return df

    def insert_collection(self, df: pd.DataFrame, collection_name: str):
        """Insertar datos en MongoDB"""
        try:
            collection = self.db[collection_name]
            collection.delete_many({})
            
            if len(df) > 0:
                records = df.to_dict('records')
                result = collection.insert_many(records)
                logger.info(f"Insertados {len(result.inserted_ids)} registros en {collection_name}")
                
                if 'id' in df.columns:
                    collection.create_index([('id', ASCENDING)])
            
        except Exception as e:
            logger.error(f"Error en {collection_name}: {e}")

    def process_csv(self, filepath: str, collection_name: str, cleaning_func):
        '''Procesa un archivo CSV'''
        try:
            if not os.path.exists(filepath):
                logger.warning(f"Archivo no encontrado: {filepath}")
                return False
            
            df = pd.read_csv(filepath)
            df = cleaning_func(df)
            self.insert_collection(df, collection_name)
            return True
                
        except Exception as e:
            logger.error(f"Error procesando {filepath}: {e}")
            return False

    def run_full_pipeline(self, data_dir: str):
        """Ejecutar pipeline completo"""
        logger.info("Iniciando pipeline completo...")
        
        files_config = [
            ('ammos.csv', 'ammo', self.clean_ammo),
            ('armors.csv', 'armor', self.clean_armor),
            ('ashes.csv', 'ashes_of_war', self.clean_ashes_of_war),
            ('bosses.csv', 'bosses', lambda df: self.base_cleaning(df, 'bosses')),
            ('classes.csv', 'classes', lambda df: self.base_cleaning(df, 'classes')),
            ('creatures.csv', 'creatures', lambda df: self.base_cleaning(df, 'creatures')),
            ('incantations.csv', 'incantations', self.clean_spells),
            ('items.csv', 'items', self.clean_items),
            ('locations.csv', 'locations', lambda df: self.base_cleaning(df, 'locations')),
            ('npcs.csv', 'npcs', self.clean_npcs),
            ('shields.csv', 'shields', lambda df: self.base_cleaning(df, 'shields')),
            ('sorceries.csv', 'sorceries', self.clean_spells),
            ('spirits.csv', 'spirit_ashes', self.clean_spirit_ashes),
            ('talismans.csv', 'talismans', lambda df: self.base_cleaning(df, 'talismans')),
            ('weapons.csv', 'weapons', lambda df: self.base_cleaning(df, 'weapons')),
        ]
        
        results = {}
        for filename, collection, cleaning_func in files_config:
            filepath = os.path.join(data_dir, filename)
            success = self.process_csv(filepath, collection, cleaning_func)
            results[filename] = 'OK' if success else 'ERROR'
        
        logger.info("\n=== RESUMEN FINAL ===")
        for filename, status in results.items():
            logger.info(f"{filename}: {status}")
    
    def close(self):
        if self.client:
            self.client.close()
            logger.info("Conexión a MongoDB cerrada.")

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(current_dir, 'data')
    
    logger.info(f"Buscando datos en: {data_dir}")
    
    if not os.path.exists(data_dir):
        logger.error(f"Directorio no existe: {data_dir}")
        logger.info(f"Directorio actual del script: {current_dir}")
        logger.info(f"Archivos en este directorio: {os.listdir(current_dir)}")
        return
    
    logger.info(f"Archivos encontrados: {os.listdir(data_dir)}")

    cleaner = DataCleaner()
    try:
        cleaner.run_full_pipeline(data_dir)
    finally:
        cleaner.close()

if __name__ == "__main__":
    main()
        