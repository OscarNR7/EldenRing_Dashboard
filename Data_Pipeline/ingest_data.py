import os
import glob
import pandas as pd
import numpy as np
from pathlib import Path
from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv
import logging
import json
import ast

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
        '''Parsea columnas con datos JSON (LEGACY - usar con cuidado)'''
        for col in cols:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: json.loads(x) if pd.notna(x) and isinstance(x,str) else None)
        return df
    
    def parse_list(self, df: pd.DataFrame, cols: list) -> pd.DataFrame:
        '''Parsea columnas con listas (LEGACY - usar con cuidado)'''
        for col in cols:
            if col in df.columns:
               df[col] = df[col].apply(lambda x: eval(x) if pd.notna(x) and isinstance(x,str) else None)
        return df
    
    def numeric_conversion(self, df: pd.DataFrame, cols: list) -> pd.DataFrame:
        '''Convierte columnas a numérico de forma segura'''
        for col in cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    
    def clean_weapons(self, df: pd.DataFrame) -> pd.DataFrame:
        '''Limpieza robusta de armas con parsing de campos anidados'''
        df = self.base_cleaning(df, 'weapons')
        logger.info("=== INICIANDO LIMPIEZA DE WEAPONS ===")
        
        attack_keys = ["physical", "magic", "fire", "lightning", "holy", "critical", "status_effects"]
        defence_keys = ["physical", "magic", "fire", "lightning", "holy", "boost"]
        
        stat_map = {
            'Phy': 'physical', 'Mag': 'magic', 'Fire': 'fire', 'Ligt': 'lightning', 'Holy': 'holy',
            'Crit': 'critical', 'Boost': 'boost',
            'Str': 'strength', 'Dex': 'dexterity', 'Int': 'intelligence', 'Fai': 'faith', 'Arc': 'arcane',
            'Arcane': 'arcane', 'Faith': 'faith', 'Dexterity': 'dexterity', 'Strength': 'strength', 
            'Intelligence': 'intelligence',
        }
        scale_keys = ["strength", "dexterity", "intelligence", "faith", "arcane"]
        req_keys = ["strength", "dexterity", "intelligence", "faith", "arcane"]

        def parse_stats(val, keys):
            d = {k: None for k in keys}
            if val is None or val == "" or val == "null":
                return d
            if not isinstance(val, (list, dict)) and pd.isna(val):
                return d
            if isinstance(val, list):
                for entry in val:
                    if isinstance(entry, dict) and 'name' in entry:
                        k = stat_map.get(entry['name'], entry['name'].lower())
                        if k in keys:
                            d[k] = entry.get('amount', entry.get('scaling', None))
                return d
            if isinstance(val, dict):
                for abbr, full in stat_map.items():
                    if abbr in val:
                        d[full] = val[abbr]
                for k in keys:
                    if k in val:
                        d[k] = val[k]
                return d
            if isinstance(val, str):
                try:
                    loaded = ast.literal_eval(val)
                    return parse_stats(loaded, keys)
                except Exception:
                    try:
                        loaded = json.loads(val)
                        return parse_stats(loaded, keys)
                    except Exception:
                        return d
            return d

        if 'attack' in df.columns:
            df['attack'] = df['attack'].apply(lambda v: parse_stats(v, attack_keys))
        if 'defence' in df.columns:
            df['defence'] = df['defence'].apply(lambda v: parse_stats(v, defence_keys))

        def list_to_dict(val, keys):
            result = {k: None for k in keys}
            if val is None or val == "" or val == "null":
                return result
            if not isinstance(val, (list, dict)) and pd.isna(val):
                return result
            if isinstance(val, dict):
                for abbr, full in stat_map.items():
                    if abbr in val and full in keys:
                        result[full] = val[abbr]
                for k in keys:
                    if k in val:
                        result[k] = val[k]
                return result
            if isinstance(val, str):
                try:
                    d = ast.literal_eval(val)
                    return list_to_dict(d, keys)
                except Exception:
                    try:
                        d = json.loads(val)
                        return list_to_dict(d, keys)
                    except Exception:
                        return result
            if isinstance(val, list):
                for entry in val:
                    if isinstance(entry, dict) and 'name' in entry:
                        abbr = entry['name']
                        k = stat_map.get(abbr, abbr.lower())
                        if k in keys:
                            value = entry.get('scaling') if 'scaling' in entry else entry.get('amount', None)
                            result[k] = value
                return result
            return result

        if 'scalesWith' in df.columns:
            df['scalesWith'] = df['scalesWith'].apply(lambda v: list_to_dict(v, scale_keys))
        if 'requiredAttributes' in df.columns:
            df['requiredAttributes'] = df['requiredAttributes'].apply(lambda v: list_to_dict(v, req_keys))

        if 'weight' in df.columns:
            df['weight'] = pd.to_numeric(df['weight'], errors='coerce')

        return df
    
    def clean_armor(self, df: pd.DataFrame) -> pd.DataFrame:
        '''Limpieza robusta de armaduras con parsing de campos anidados'''
        df = self.base_cleaning(df, 'armor')
        logger.info("=== INICIANDO LIMPIEZA DE ARMORS ===")
        
        if len(df) > 0 and 'dmgNegation' in df.columns:
            logger.info(f"Primera fila dmgNegation (antes): {df['dmgNegation'].iloc[0]}")
        
        defense_keys = ["physical", "strike", "slash", "pierce", "magic", "fire", "lightning", "holy"]
        resistance_keys = ["immunity", "robustness", "focus", "vitality", "poise"]
        
        stat_map = {
            'Phy': 'physical', 'Physical': 'physical',
            'Strike': 'strike', 'Slash': 'slash', 'Pierce': 'pierce',
            'Mag': 'magic', 'Magic': 'magic',
            'Fire': 'fire', 'Ligt': 'lightning', 'Lightning': 'lightning', 'Holy': 'holy',
            'Immunity': 'immunity', 'Robustness': 'robustness', 
            'Focus': 'focus', 'Vitality': 'vitality', 'Poise': 'poise'
        }
        
        def parse_stats(val, keys):
            result = {k: None for k in keys}
            if val is None or val == "" or val == "null":
                return result
            if not isinstance(val, (list, dict)) and pd.isna(val):
                return result
            if isinstance(val, list):
                for entry in val:
                    if not isinstance(entry, dict):
                        continue
                    name = entry.get('name')
                    amount = entry.get('amount')
                    if name and amount is not None:
                        mapped_name = stat_map.get(name, name.lower())
                        if mapped_name in keys:
                            try:
                                result[mapped_name] = float(amount)
                            except (ValueError, TypeError):
                                result[mapped_name] = amount
                return result
            if isinstance(val, dict):
                for abbr, full in stat_map.items():
                    if abbr in val and full in keys:
                        try:
                            result[full] = float(val[abbr])
                        except (ValueError, TypeError):
                            result[full] = val[abbr]
                for key in keys:
                    if key in val:
                        try:
                            result[key] = float(val[key])
                        except (ValueError, TypeError):
                            result[key] = val[key]
                return result
            if isinstance(val, str):
                try:
                    parsed = ast.literal_eval(val)
                    return parse_stats(parsed, keys)
                except (ValueError, SyntaxError):
                    try:
                        parsed = json.loads(val)
                        return parse_stats(parsed, keys)
                    except (json.JSONDecodeError, TypeError):
                        logger.warning(f"No se pudo parsear valor: {val[:100]}...")
                        return result
            logger.warning(f"Tipo inesperado en parse_stats: {type(val)}")
            return result
        
        if 'dmgNegation' in df.columns:
            df['dmgNegation'] = df['dmgNegation'].apply(lambda v: parse_stats(v, defense_keys))
            if len(df) > 0:
                logger.info(f"Primera fila dmgNegation (después): {df['dmgNegation'].iloc[0]}")
        
        if 'resistance' in df.columns:
            df['resistance'] = df['resistance'].apply(lambda v: parse_stats(v, resistance_keys))
            if len(df) > 0:
                logger.info(f"Primera fila resistance (después): {df['resistance'].iloc[0]}")
        
        if 'weight' in df.columns:
            df['weight'] = pd.to_numeric(df['weight'], errors='coerce')
        
        logger.info(f"Armaduras procesadas: {len(df)} registros")
        return df
    
    def clean_classes(self, df: pd.DataFrame) -> pd.DataFrame:
        '''Limpieza robusta de clases con parsing de stats anidados'''
        df = self.base_cleaning(df, 'classes')
        logger.info("=== INICIANDO LIMPIEZA DE CLASSES ===")
        
        if len(df) > 0 and 'stats' in df.columns:
            logger.info(f"Primera fila stats (antes): {df['stats'].iloc[0]}")
        
        stat_keys = ['level', 'vigor', 'mind', 'endurance', 'strength', 'dexterity', 'intelligence', 'faith', 'arcane']
        stat_name_map = {
            'Level': 'level', 'Vigor': 'vigor', 'Mind': 'mind', 'Endurance': 'endurance',
            'Strength': 'strength', 'Str': 'strength',
            'Dexterity': 'dexterity', 'Dex': 'dexterity',
            'Intelligence': 'intelligence', 'Int': 'intelligence',
            'Faith': 'faith', 'Fai': 'faith',
            'Arcane': 'arcane', 'Arc': 'arcane'
        }
        
        def parse_character_stats(val):
            if val is None or val == "" or val == "null":
                return None
            if pd.isna(val):
                return None
            if isinstance(val, dict):
                normalized = {}
                for key, value in val.items():
                    mapped_key = stat_name_map.get(key, key.lower())
                    if mapped_key in stat_keys:
                        if value is not None:
                            try:
                                normalized[mapped_key] = int(value)
                            except (ValueError, TypeError):
                                logger.warning(f"Valor no numérico para {mapped_key}: {value}")
                                normalized[mapped_key] = None
                        else:
                            normalized[mapped_key] = None
                return normalized if normalized else None
            if isinstance(val, str):
                try:
                    parsed = ast.literal_eval(val)
                    return parse_character_stats(parsed)
                except (ValueError, SyntaxError):
                    try:
                        parsed = json.loads(val)
                        return parse_character_stats(parsed)
                    except (json.JSONDecodeError, TypeError):
                        logger.warning(f"No se pudo parsear stats: {val[:100]}...")
                        return None
            logger.warning(f"Tipo inesperado en parse_character_stats: {type(val)}")
            return None
        
        if 'stats' in df.columns:
            df['stats'] = df['stats'].apply(parse_character_stats)
            if len(df) > 0:
                logger.info(f"Primera fila stats (después): {df['stats'].iloc[0]}")
                valid_stats = df['stats'].notna().sum()
                logger.info(f"Clases con stats válidas: {valid_stats}/{len(df)}")
                if valid_stats < len(df):
                    missing = df[df['stats'].isna()]['name'].tolist()
                    logger.warning(f"Clases sin stats: {missing}")
        
        if 'name' in df.columns:
            df['name'] = df['name'].apply(lambda x: x.strip().title() if pd.notna(x) else x)
        
        logger.info(f"Clases procesadas: {len(df)} registros")
        return df
    
    def clean_bosses(self, df: pd.DataFrame) -> pd.DataFrame:
        '''Limpieza robusta de jefes con parsing de drops'''
        df = self.base_cleaning(df, 'bosses')
        logger.info("=== INICIANDO LIMPIEZA DE BOSSES ===")
        
        if len(df) > 0 and 'drops' in df.columns:
            logger.info(f"Primera fila drops (antes): {df['drops'].iloc[0]}")
        
        def parse_drops(val):
            if val is None or val == "" or val == "null":
                return None
            if pd.isna(val):
                return None
            if isinstance(val, list):
                return [str(item).strip() for item in val if item]
            if isinstance(val, str):
                try:
                    parsed = ast.literal_eval(val)
                    return parse_drops(parsed)
                except (ValueError, SyntaxError):
                    try:
                        parsed = json.loads(val)
                        return parse_drops(parsed)
                    except (json.JSONDecodeError, TypeError):
                        return [val.strip()] if val.strip() else None
            return None
        
        if 'drops' in df.columns:
            df['drops'] = df['drops'].apply(parse_drops)
            if len(df) > 0:
                logger.info(f"Primera fila drops (después): {df['drops'].iloc[0]}")
                valid_drops = df['drops'].notna().sum()
                logger.info(f"Jefes con drops: {valid_drops}/{len(df)}")
        
        if 'region' in df.columns:
            df['region'] = df['region'].apply(lambda x: x.strip().title() if pd.notna(x) and x else None)
        if 'location' in df.columns:
            df['location'] = df['location'].apply(lambda x: x.strip() if pd.notna(x) and x else None)
        
        logger.info(f"Jefes procesados: {len(df)} registros")
        return df
    
    def clean_spells(self, df: pd.DataFrame) -> pd.DataFrame:
        '''Limpieza de hechizos (sorceries e incantations)'''
        df = self.base_cleaning(df, 'spells')
        
        if 'cost' in df.columns:
            df['cost'] = pd.to_numeric(df['cost'], errors='coerce')
        if 'slots' in df.columns:
            df['slots'] = pd.to_numeric(df['slots'], errors='coerce')
        
        return df
    
    def clean_ammo(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.base_cleaning(df, 'ammo')
        df = self.parse_json(df, ['attack', 'defence'])
        df = self.numeric_conversion(df, ['weight'])
        return df
    
    def clean_ashes_of_war(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.base_cleaning(df, 'ashes_of_war')
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
        """Ejecutar pipeline completo con limpieza robusta"""
        logger.info("Iniciando pipeline completo...")

        files_config = [
            ('ammos.csv', 'ammo', self.clean_ammo),
            ('armors.csv', 'armor', self.clean_armor),
            ('ashes.csv', 'ashes_of_war', self.clean_ashes_of_war),
            ('bosses.csv', 'bosses', self.clean_bosses),
            ('classes.csv', 'classes', self.clean_classes),
            ('creatures.csv', 'creatures', lambda df: self.base_cleaning(df, 'creatures')),
            ('incantations.csv', 'incantations', self.clean_spells),
            ('items.csv', 'items', self.clean_items),
            ('locations.csv', 'locations', lambda df: self.base_cleaning(df, 'locations')),
            ('npcs.csv', 'npcs', self.clean_npcs),
            ('shields.csv', 'shields', lambda df: self.base_cleaning(df, 'shields')),
            ('sorceries.csv', 'sorceries', self.clean_spells),
            ('spirits.csv', 'spirit_ashes', self.clean_spirit_ashes),
            ('talismans.csv', 'talismans', lambda df: self.base_cleaning(df, 'talismans')),
            ('weapons.csv', 'weapons', self.clean_weapons),
        ]

        try:
            self.db['weapons'].drop()
            logger.info("Colección 'weapons' eliminada antes de reingestar.")
        except Exception as e:
            logger.warning(f"No se pudo eliminar 'weapons': {e}")

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