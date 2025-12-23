"""
GDELT News Collector Service - OPTIMIZADO
Recolecta noticias de GDELT relacionadas con Colombia y economía
Optimizado para obtener 2,000-3,000 artículos por ejecución
"""

import os
import time
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict
import redis
import psycopg2
import requests
import schedule

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GDELTCollector:
    """Recolector de noticias desde GDELT - Optimizado para alto volumen"""
    
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
        
        # Keywords económicos expandidos - 60+ términos para alto volumen
        self.economic_keywords = [
            # Términos económicos generales
            'colombia economía', 'colombia bolsa', 'colombia finanzas', 'colombia negocios',
            'colombia comercio', 'colombia PIB', 'colombia inversión', 'colombia mercado',
            'colombia exportaciones', 'colombia importaciones', 'colombia industria',
            
            # Índices y mercados
            'colcap', 'BVC colombia', 'colombia acciones', 'colombia valores',
            'colombia bursátil', 'colombia renta fija',
            
            # Moneda y divisas
            'colombia peso', 'colombia dólar', 'colombia divisas', 'colombia tipo cambio',
            'colombia devaluación', 'colombia TRM',
            
            # Sector bancario y financiero
            'colombia banco', 'bancolombia', 'banco bogotá', 'davivienda',
            'grupo aval', 'colombia crédito', 'colombia tasa interés',
            'colombia banrep', 'banco república colombia',
            
            # Empresas estratégicas
            'ecopetrol', 'avianca colombia', 'grupo éxito colombia', 'nutresa',
            'grupo argos colombia', 'celsia colombia', 'ISA colombia',
            'cemex colombia', 'bavaria colombia', 'corona colombia',
            
            # Sectores productivos
            'colombia petróleo', 'colombia energía', 'colombia minería',
            'colombia agricultura', 'colombia café', 'colombia flores',
            'colombia turismo', 'colombia construcción', 'colombia manufactura',
            'colombia tecnología', 'colombia telecomunicaciones',
            
            # Indicadores económicos
            'colombia inflación', 'colombia desempleo', 'colombia crecimiento',
            'colombia déficit', 'colombia deuda', 'colombia presupuesto',
            'colombia balanza comercial',
            
            # Ciudades económicas
            'bogotá economía', 'medellín economía', 'cali economía',
            'barranquilla economía', 'cartagena economía',
            
            # Acuerdos y comercio internacional
            'colombia TLC', 'colombia exportación', 'colombia importación'
        ]
        
        self.days_back = int(os.getenv('GDELT_DAYS_BACK', 365))  # 1 año completo
        self.max_records_per_query = 250
        
        logger.info("GDELT Collector inicializado (OPTIMIZADO)")
        logger.info(f"Keywords: {len(self.economic_keywords)}")
        logger.info(f"Días: {self.days_back} (1 año completo)")
        logger.info(f"Días: {self.days_back}")
    
    def get_db_connection(self):
        return psycopg2.connect(**self.db_config)
    
    def fetch_gdelt_articles(self) -> List[Dict]:
        logger.info(f"🔍 Búsqueda GDELT ({self.days_back} días)")
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=self.days_back)
        start_str = start_date.strftime('%Y%m%d%H%M%S')
        end_str = end_date.strftime('%Y%m%d%H%M%S')
        
        articles = []
        successful = 0
        
        for i, keyword in enumerate(self.economic_keywords, 1):
            try:
                url = "https://api.gdeltproject.org/api/v2/doc/doc"
                params = {
                    'query': keyword,
                    'mode': 'artlist',
                    'maxrecords': self.max_records_per_query,
                    'startdatetime': start_str,
                    'enddatetime': end_str,
                    'format': 'json'
                }
                
                response = requests.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'articles' in data:
                        count = len(data['articles'])
                        articles.extend(data['articles'])
                        successful += 1
                        logger.info(f"  [{i}/{len(self.economic_keywords)}] '{keyword}': {count} ✓")
                
                time.sleep(1.2)
                
            except Exception as e:
                logger.error(f"  [{i}] '{keyword}': Error")
                continue
        
        unique = {a.get('url'): a for a in articles if a.get('url')}
        result = list(unique.values())
        
        logger.info(f"📊 Total: {len(articles)} → Únicos: {len(result)}")
        return result
    
    def save_to_database(self, articles: List[Dict]):
        if not articles:
            return 0
        
        conn = self.get_db_connection()
        cursor = conn.cursor()
        saved = 0
        
        try:
            for article in articles:
                try:
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
                        article.get('title', ''),
                        article.get('domain', ''),
                        pub_date,
                        'CO'
                    ))
                    
                    if cursor.rowcount > 0:
                        saved += 1
                except:
                    continue
            
            conn.commit()
            logger.info(f"💾 Guardados: {saved}")
        except Exception as e:
            conn.rollback()
            logger.error(f"Error BD: {e}")
        finally:
            cursor.close()
            conn.close()
        
        return saved
    
    def queue_for_processing(self, count: int):
        if count > 0:
            message = {
                'timestamp': datetime.utcnow().isoformat(),
                'new_articles': count,
                'action': 'process_new_articles'
            }
            self.redis_client.publish('news_processing', json.dumps(message))
    
    def collect(self):
        logger.info("="*70)
        logger.info("🚀 GDELT Collection")
        logger.info("="*70)
        
        start = time.time()
        articles = self.fetch_gdelt_articles()
        saved = self.save_to_database(articles)
        self.queue_for_processing(saved)
        
        elapsed = time.time() - start
        logger.info(f"✅ Completado en {int(elapsed)}s - {len(articles)} artículos, {saved} guardados")
    
    def run(self):
        logger.info("🚀 GDELT Collector (OPTIMIZADO)")
        self.collect()
        
        interval = int(os.getenv('COLLECTION_INTERVAL', 21600))
        schedule.every(interval).seconds.do(self.collect)
        
        while True:
            schedule.run_pending()
            time.sleep(60)


if __name__ == "__main__":
    collector = GDELTCollector()
    collector.run()
