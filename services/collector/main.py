"""
GDELT News Collector Service
Recolecta noticias de GDELT relacionadas con Colombia y economía
"""

import os
import time
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict
import redis
import psycopg2
from psycopg2.extras import execute_values
import requests
import schedule

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GDELTCollector:
    """Recolector de noticias desde GDELT"""
    
    def __init__(self):
        # Configuración de Redis
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )
        
        # Configuración de PostgreSQL
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'database': os.getenv('POSTGRES_DB', 'news_colcap'),
            'user': os.getenv('POSTGRES_USER', 'newsuser'),
            'password': os.getenv('POSTGRES_PASSWORD', 'newspass123')
        }
        
        # Keywords económicos para filtrar
        self.economic_keywords = [
            'economía', 'bolsa', 'COLCAP', 'dólar', 'peso', 'inflación',
            'banco', 'inversión', 'mercado', 'finanzas', 'comercio',
            'PIB', 'empresas', 'negocios', 'petróleo', 'exportaciones',
            'acciones', 'divisas', 'tasa', 'interés', 'BVC', 'Ecopetrol',
            'Bancolombia', 'Grupo Aval', 'ISA'
        ]
        
        logger.info("GDELT Collector inicializado")
    
    def get_db_connection(self):
        """Obtener conexión a PostgreSQL"""
        return psycopg2.connect(**self.db_config)
    
    def fetch_gdelt_articles(self, days_back: int = 365) -> List[Dict]:
        """
        Obtener artículos de GDELT del último año
        Usando la API v2 de GDELT
        """
        logger.info(f"Obteniendo artículos GDELT de los últimos {days_back} días")
        
        # Calcular rango de fechas
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        # Formato de fecha para GDELT: YYYYMMDDHHMMSS
        start_str = start_date.strftime('%Y%m%d%H%M%S')
        end_str = end_date.strftime('%Y%m%d%H%M%S')
        
        articles = []
        
        # Buscar por diferentes keywords económicos - usar todos los keywords
        for keyword in self.economic_keywords:  # Usar todos los keywords (15)
            try:
                # URL de GDELT DOC 2.0 API
                url = "https://api.gdeltproject.org/api/v2/doc/doc"
                params = {
                    'query': f'colombia {keyword}',
                    'mode': 'artlist',
                    'maxrecords': 250,  # Máximo permitido por GDELT
                    'startdatetime': start_str,
                    'enddatetime': end_str,
                    'format': 'json'
                }
                
                response = requests.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'articles' in data:
                        articles.extend(data['articles'])
                        logger.info(f"Obtenidos {len(data['articles'])} artículos para keyword '{keyword}'")
                else:
                    logger.warning(f"Error en GDELT API: {response.status_code}")
                
                # Rate limiting - esperar entre requests
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error obteniendo artículos para '{keyword}': {str(e)}")
                continue
        
        # Eliminar duplicados por URL
        unique_articles = {article['url']: article for article in articles}
        logger.info(f"Total de artículos únicos: {len(unique_articles)}")
        
        return list(unique_articles.values())
    
    def save_to_database(self, articles: List[Dict]):
        """Guardar artículos en PostgreSQL"""
        if not articles:
            logger.info("No hay artículos para guardar")
            return 0
        
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        saved_count = 0
        
        try:
            for article in articles:
                try:
                    # Parsear fecha de publicación
                    pub_date = datetime.strptime(
                        article.get('seendate', datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')),
                        '%Y%m%dT%H%M%SZ'
                    )
                    
                    cursor.execute("""
                        INSERT INTO news (url, title, content, source, published_date, country)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (url) DO NOTHING
                    """, (
                        article.get('url', ''),
                        article.get('title', ''),
                        article.get('title', ''),  # GDELT no da contenido completo
                        article.get('domain', ''),
                        pub_date,
                        'CO'
                    ))
                    
                    if cursor.rowcount > 0:
                        saved_count += 1
                        
                except Exception as e:
                    logger.error(f"Error guardando artículo: {str(e)}")
                    continue
            
            conn.commit()
            logger.info(f"Guardados {saved_count} nuevos artículos en BD")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error en transacción de BD: {str(e)}")
        finally:
            cursor.close()
            conn.close()
        
        return saved_count
    
    def queue_for_processing(self, count: int):
        """Enviar señal a Redis para que el procesador trabaje"""
        if count > 0:
            message = {
                'timestamp': datetime.utcnow().isoformat(),
                'new_articles': count,
                'action': 'process_new_articles'
            }
            self.redis_client.publish('news_processing', json.dumps(message))
            logger.info(f"Señal de procesamiento enviada a Redis")
    
    def collect(self):
        """Ejecutar ciclo de recolección completo"""
        logger.info("=" * 50)
        logger.info("Iniciando ciclo de recolección")
        logger.info("=" * 50)
        
        start_time = time.time()
        
        # 1. Obtener artículos de GDELT del último año (365 días)
        articles = self.fetch_gdelt_articles(days_back=365)
        
        # 2. Guardar en base de datos
        saved_count = self.save_to_database(articles)
        
        # 3. Notificar al procesador
        self.queue_for_processing(saved_count)
        
        elapsed = time.time() - start_time
        logger.info(f"Ciclo completado en {elapsed:.2f} segundos")
        logger.info("=" * 50)
    
    def run(self):
        """Ejecutar servicio en loop continuo"""
        logger.info("🚀 Iniciando GDELT Collector Service")
        
        # Ejecutar inmediatamente al iniciar
        self.collect()
        
        # Programar ejecuciones cada 6 horas
        interval = int(os.getenv('COLLECTION_INTERVAL', 21600))  # 6 horas por defecto
        schedule.every(interval).seconds.do(self.collect)
        
        logger.info(f"Programado para ejecutar cada {interval/3600} horas")
        
        # Loop principal
        while True:
            schedule.run_pending()
            time.sleep(60)  # Verificar cada minuto


if __name__ == "__main__":
    collector = GDELTCollector()
    collector.run()
