"""
News Processor Service
Procesa y analiza el contenido de las noticias
"""

import os
import json
import logging
import time
import re
import unicodedata
from datetime import datetime
from typing import List, Dict, Tuple
import redis
import psycopg2
from psycopg2.extras import RealDictCursor
from textblob import TextBlob
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NewsProcessor:
    """Procesador de noticias con análisis de sentimiento"""
    
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
        
        # Inicializar analizador de sentimientos
        try:
            self.sia = SentimentIntensityAnalyzer()
            logger.info("Analizador de sentimientos VADER inicializado")
        except Exception as e:
            logger.error(f"Error inicializando VADER: {str(e)}")
            self.sia = None
        
        # Categorías económicas
        self.categories_keywords = {
            'mercados': ['bolsa', 'acciones', 'COLCAP', 'mercado', 'bursátil'],
            'divisas': ['dólar', 'euro', 'peso', 'divisa', 'cambio'],
            'commodities': ['petróleo', 'oro', 'café', 'carbón', 'commodity'],
            'banca': ['banco', 'financiero', 'crédito', 'tasa'],
            'empresas': ['empresa', 'negocio', 'compañía', 'corporación'],
            'politica_economica': ['gobierno', 'reforma', 'impuesto', 'política'],
            'comercio': ['exportación', 'importación', 'comercio', 'TLC']
        }
        
        logger.info("News Processor inicializado")
    
    def normalize_text(self, text: str) -> str:
        """Normaliza el texto: minúsculas, sin tildes, lematización básica"""
        # Minúsculas
        text = text.lower()
        
        # Eliminar tildes
        text = ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        )
        
        # Lematización básica (verbos comunes en español)
        lemmatization_rules = {
            'crecio': 'crece', 'creciendo': 'crece', 'crecieron': 'crece',
            'cayo': 'cae', 'cayeron': 'cae', 'cayendo': 'cae',
            'subio': 'sube', 'subieron': 'sube', 'subiendo': 'sube',
            'bajo': 'baja', 'bajaron': 'baja', 'bajando': 'baja',
            'aumento': 'aumenta', 'aumentaron': 'aumenta', 'aumentando': 'aumenta',
            'disminuyo': 'disminuye', 'disminuyeron': 'disminuye',
            'perdio': 'pierde', 'perdieron': 'pierde', 'perdiendo': 'pierde',
            'gano': 'gana', 'ganaron': 'gana', 'ganando': 'gana',
            'mejoro': 'mejora', 'mejoraron': 'mejora', 'mejorando': 'mejora',
            'empeoro': 'empeora', 'empeoraron': 'empeora',
            'logro': 'logra', 'lograron': 'logra', 'logrando': 'logra',
            'recupero': 'recupera', 'recuperaron': 'recupera',
            'afecto': 'afecta', 'afectaron': 'afecta', 'afectando': 'afecta',
            'impulso': 'impulsa', 'impulsaron': 'impulsa'
        }
        
        words = text.split()
        normalized_words = [lemmatization_rules.get(w, w) for w in words]
        return ' '.join(normalized_words)
    
    def get_db_connection(self):
        """Obtener conexión a PostgreSQL"""
        return psycopg2.connect(**self.db_config)
    
    def analyze_sentiment(self, text: str) -> Tuple[float, str]:
        """
        Análisis de sentimiento AVANZADO con normalización, intensificadores y negaciones
        Returns: (score: -1 a 1, label: positive/negative/neutral)
        """
        if not text:
            return 0.0, 'neutral'
        
        # Normalizar texto
        text_normalized = self.normalize_text(text)
        
        # Intensificadores
        intensifiers = {
            'muy': 1.5, 'significativamente': 1.7, 'fuertemente': 1.6,
            'drasticamente': 1.8, 'ligeramente': 0.7, 'moderadamente': 0.85,
            'extremadamente': 1.9, 'altamente': 1.6, 'sumamente': 1.7,
            'enormemente': 1.8, 'considerablemente': 1.6, 'notablemente': 1.5,
            'marcadamente': 1.6, 'profundamente': 1.7, 'severamente': 1.7,
            'apenas': 0.6, 'escasamente': 0.6, 'poco': 0.7, 'bastante': 1.3
        }
        
        # Negaciones
        negations = [
            'no', 'nunca', 'jamas', 'sin', 'evita', 'evito', 'ni',
            'tampoco', 'nada', 'nadie', 'ninguno', 'ninguna',
            'imposible', 'niega', 'nego', 'rechaza', 'rechazo',
            'impide', 'impidio', 'detiene', 'detuvo', 'frena', 'freno'
        ]
        
        # Keywords económicas expandidas
        positive_economic = {
            'crece': 0.4, 'crecimiento': 0.4, 'aumenta': 0.3, 'aumento': 0.3,
            'sube': 0.35, 'gana': 0.3, 'ganancia': 0.35, 'exito': 0.5,
            'logra': 0.4, 'record': 0.45, 'historico': 0.4, 'inversion': 0.3,
            'expansion': 0.35, 'recupera': 0.4, 'mejora': 0.35, 'beneficio': 0.4,
            'millones': 0.25, 'dolares': 0.2, 'negociacion': 0.25, 'acuerdo': 0.25,
            # Nuevas
            'estabilidad': 0.35, 'reactivacion': 0.4, 'superavit': 0.45,
            'confianza': 0.35, 'liquidez': 0.3, 'solidez': 0.4,
            'competitividad': 0.35, 'sostenido': 0.4, 'innovacion': 0.35,
            'prosperidad': 0.45, 'favorable': 0.3, 'prometedor': 0.35
        }
        
        negative_economic = {
            'cae': -0.4, 'caida': -0.4, 'baja': -0.3, 'pierde': -0.35,
            'crisis': -0.6, 'quiebra': -0.7, 'deficit': -0.45, 'recesion': -0.6,
            'riesgo': -0.3, 'afecta': -0.3, 'problema': -0.3, 'emergencia': -0.4,
            'dictadura': -0.6, 'guerra': -0.5, 'violencia': -0.5,
            # Nuevas
            'inflacion': -0.45, 'devaluacion': -0.4, 'desaceleracion': -0.4,
            'inestabilidad': -0.45, 'fuga': -0.5, 'sobreendeudamiento': -0.5,
            'desconfianza': -0.35, 'estancamiento': -0.4, 'corrupcion': -0.6,
            'sanciones': -0.45, 'bancarrota': -0.7, 'desempleo': -0.5,
            'escasez': -0.4, 'huelga': -0.4, 'recorte': -0.35
        }
        
        # Analizar con intensificadores y negaciones
        words = text_normalized.split()
        scores = []
        
        i = 0
        while i < len(words):
            word = words[i]
            intensifier = 1.0
            is_negated = False
            
            # Detectar intensificador
            if i > 0 and words[i-1] in intensifiers:
                intensifier = intensifiers[words[i-1]]
            
            # Detectar negación
            if i > 0 and words[i-1] in negations:
                is_negated = True
            elif i > 1 and words[i-2] in negations:
                is_negated = True
            
            # Calcular score
            if word in positive_economic:
                score = positive_economic[word] * intensifier
                if is_negated:
                    score = -score
                scores.append(score)
            elif word in negative_economic:
                score = negative_economic[word] * intensifier
                if is_negated:
                    score = -score
                scores.append(score)
            
            i += 1
        
        keyword_score = sum(scores)
        
        try:
            # VADER
            if self.sia:
                vader_compound = self.sia.polarity_scores(text)['compound']
            else:
                vader_compound = 0.0
            
            # TextBlob
            blob = TextBlob(text)
            textblob_polarity = blob.sentiment.polarity
            
            # Combinar: Keywords 70%, TextBlob 20%, VADER 10%
            final_score = (keyword_score * 0.7) + (textblob_polarity * 0.2) + (vader_compound * 0.1)
            final_score = max(-1.0, min(1.0, final_score))
            
            # Clasificar
            if final_score >= 0.08:
                label = 'positive'
            elif final_score <= -0.08:
                label = 'negative'
            else:
                label = 'neutral'
            
            return final_score, label
                
        except Exception as e:
            logger.error(f"Error en análisis de sentimiento: {str(e)}")
            return keyword_score, ('positive' if keyword_score > 0.08 else ('negative' if keyword_score < -0.08 else 'neutral'))
    
    def classify_categories(self, text: str) -> List[str]:
        """Clasificar noticias por categorías económicas"""
        text_lower = text.lower()
        categories = []
        
        for category, keywords in self.categories_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                categories.append(category)
        
        return categories if categories else ['general']
    
    def extract_keywords(self, text: str, top_n: int = 5) -> List[str]:
        """Extraer keywords principales del texto"""
        try:
            # Tokenizar y limpiar
            words = text.lower().split()
            
            # Filtrar palabras comunes (stopwords)
            stopwords = set(['el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'ser', 
                           'se', 'no', 'por', 'con', 'su', 'para', 'como', 'es'])
            
            words = [w for w in words if w not in stopwords and len(w) > 3]
            
            # Contar frecuencias
            word_freq = {}
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # Top N keywords
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            keywords = [word for word, freq in sorted_words[:top_n]]
            
            return keywords
            
        except Exception as e:
            logger.error(f"Error extrayendo keywords: {str(e)}")
            return []
    
    def process_article(self, article: Dict) -> Dict:
        """Procesar un artículo individual"""
        try:
            # Combinar título y contenido para análisis
            full_text = f"{article['title']} {article.get('content', '')}"
            
            # Análisis de sentimiento
            sentiment_score, sentiment_label = self.analyze_sentiment(full_text)
            
            # Clasificación de categorías
            categories = self.classify_categories(full_text)
            
            # Extracción de keywords
            keywords = self.extract_keywords(full_text)
            
            return {
                'id': article['id'],
                'sentiment_score': sentiment_score,
                'sentiment_label': sentiment_label,
                'categories': categories,
                'keywords': keywords
            }
            
        except Exception as e:
            logger.error(f"Error procesando artículo {article.get('id')}: {str(e)}")
            return None
    
    def get_unprocessed_articles(self, limit: int = 100) -> List[Dict]:
        """Obtener artículos sin procesar de la BD"""
        conn = self.get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cursor.execute("""
                SELECT id, title, content, published_date
                FROM news
                WHERE sentiment_score IS NULL
                ORDER BY published_date DESC
                LIMIT %s
            """, (limit,))
            
            articles = cursor.fetchall()
            logger.info(f"Obtenidos {len(articles)} artículos sin procesar")
            return articles
            
        finally:
            cursor.close()
            conn.close()
    
    def update_article(self, processed_data: Dict):
        """Actualizar artículo con datos procesados"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE news
                SET sentiment_score = %s,
                    sentiment_label = %s,
                    categories = %s,
                    keywords = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (
                processed_data['sentiment_score'],
                processed_data['sentiment_label'],
                processed_data['categories'],
                processed_data['keywords'],
                processed_data['id']
            ))
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error actualizando artículo: {str(e)}")
        finally:
            cursor.close()
            conn.close()
    
    def process_batch(self):
        """Procesar lote de artículos"""
        logger.info("Procesando lote de artículos...")
        
        # Obtener artículos sin procesar
        articles = self.get_unprocessed_articles(limit=50)
        
        if not articles:
            logger.info("No hay artículos para procesar")
            return 0
        
        processed_count = 0
        
        for article in articles:
            processed_data = self.process_article(dict(article))
            
            if processed_data:
                self.update_article(processed_data)
                processed_count += 1
        
        logger.info(f"✓ Procesados {processed_count} artículos")
        
        # Notificar al analizador si hay suficientes datos
        if processed_count > 0:
            self.notify_analyzer()
        
        return processed_count
    
    def notify_analyzer(self):
        """Notificar al servicio de análisis"""
        message = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': 'run_analysis'
        }
        self.redis_client.publish('analysis_trigger', json.dumps(message))
    
    def listen_for_jobs(self):
        """Escuchar mensajes de Redis"""
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe('news_processing')
        
        logger.info("Escuchando canal 'news_processing' en Redis...")
        
        for message in pubsub.listen():
            if message['type'] == 'message':
                logger.info(f"Mensaje recibido: {message['data']}")
                self.process_batch()
    
    def run(self):
        """Ejecutar servicio"""
        logger.info("🚀 Iniciando News Processor Service")
        
        # Procesar artículos existentes al iniciar
        self.process_batch()
        
        # Escuchar por nuevos trabajos
        while True:
            try:
                # Procesar cada 5 minutos
                time.sleep(300)
                self.process_batch()
                
            except KeyboardInterrupt:
                logger.info("Deteniendo procesador...")
                break
            except Exception as e:
                logger.error(f"Error en loop principal: {str(e)}")
                time.sleep(60)


if __name__ == "__main__":
    processor = NewsProcessor()
    processor.run()
