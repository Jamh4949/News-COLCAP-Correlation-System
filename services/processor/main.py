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
        
        # Keywords económicas ULTRA EXPANDIDAS para mayor sensibilidad
        positive_economic = {
            # Crecimiento y aumento (0.3-0.6)
            'crece': 0.5, 'crecimiento': 0.5, 'aumenta': 0.45, 'aumento': 0.45,
            'sube': 0.5, 'subida': 0.5, 'incremento': 0.45, 'incrementa': 0.45,
            'repunte': 0.5, 'repunta': 0.5, 'avance': 0.45, 'avanza': 0.45,
            'alza': 0.5, 'eleva': 0.45, 'elevacion': 0.45, 'impulsa': 0.5,
            'impulso': 0.5, 'fortalece': 0.5, 'fortalecimiento': 0.5,
            
            # Ganancias y éxito (0.4-0.7)
            'gana': 0.5, 'ganancia': 0.55, 'ganancias': 0.55, 'exito': 0.6,
            'exitoso': 0.6, 'logra': 0.5, 'logro': 0.5, 'logros': 0.5,
            'record': 0.65, 'historico': 0.55, 'maximo': 0.6, 'maxima': 0.6,
            'beneficio': 0.55, 'beneficios': 0.55, 'rentable': 0.55,
            'rentabilidad': 0.55, 'utilidad': 0.5, 'utilidades': 0.5,
            
            # Inversión y expansión (0.3-0.5)
            'inversion': 0.4, 'invierte': 0.4, 'expansion': 0.5, 'expande': 0.5,
            'desarrollo': 0.45, 'desarrolla': 0.45, 'moderniza': 0.45,
            'modernizacion': 0.45, 'progreso': 0.5, 'progresa': 0.5,
            
            # Recuperación y mejora (0.4-0.6)
            'recupera': 0.55, 'recuperacion': 0.55, 'mejora': 0.5, 'mejoramiento': 0.5,
            'mejorando': 0.5, 'mejoro': 0.5, 'optimo': 0.55, 'optima': 0.55,
            'optimiza': 0.5, 'optimizacion': 0.5, 'optimismo': 0.5, 'optimista': 0.5,
            
            # Estabilidad y confianza (0.35-0.5)
            'estabilidad': 0.45, 'estable': 0.45, 'reactivacion': 0.55,
            'superavit': 0.6, 'confianza': 0.5, 'confiable': 0.45,
            'liquidez': 0.4, 'solido': 0.5, 'solidez': 0.5, 'solvencia': 0.5,
            'competitividad': 0.45, 'competitivo': 0.45, 'sostenido': 0.5,
            'sostenible': 0.45, 'sustentable': 0.45, 'sostenibilidad': 0.45,
            
            # Innovación y oportunidad (0.35-0.5)
            'innovacion': 0.45, 'innovador': 0.45, 'oportunidad': 0.4,
            'oportunidades': 0.4, 'prospero': 0.55, 'prosperidad': 0.55,
            'favorable': 0.45, 'favorables': 0.45, 'prometedor': 0.5,
            'promisorio': 0.5, 'positivo': 0.5, 'positiva': 0.5,
            
            # Acuerdos y negociación (0.25-0.45)
            'acuerdo': 0.4, 'acuerdos': 0.4, 'negociacion': 0.35,
            'alianza': 0.45, 'asociacion': 0.4, 'cooperacion': 0.4,
            'pacto': 0.35, 'convenio': 0.35, 'contrato': 0.3,
            
            # Mercados y comercio (0.25-0.45)
            'millones': 0.3, 'miles': 0.25, 'dolares': 0.25,
            'exportacion': 0.4, 'exporta': 0.4, 'exportaciones': 0.4,
            'demanda': 0.3, 'compra': 0.25, 'compras': 0.25, 'vende': 0.25,
            'comercio': 0.3, 'mercado': 0.25, 'mercados': 0.25,
            
            # Productividad y eficiencia (0.35-0.5)
            'productividad': 0.45, 'productivo': 0.45, 'eficiente': 0.45,
            'eficiencia': 0.45, 'produccion': 0.35, 'produce': 0.35,
            'genera': 0.35, 'generacion': 0.35, 'rendimiento': 0.4,
            
            # Adicionales positivos (0.3-0.55)
            'respalda': 0.4, 'respaldo': 0.4, 'apoya': 0.35, 'apoyo': 0.35,
            'consolida': 0.5, 'consolidacion': 0.5, 'robusto': 0.5, 'robustez': 0.5,
            'vigoroso': 0.5, 'vigoriza': 0.5, 'dinamico': 0.45, 'dinamismo': 0.45,
            'auge': 0.55, 'bonanza': 0.55, 'florecimiento': 0.5,
            
            # Palabras económicas comunes positivas (0.15-0.35)
            'nuevo': 0.2, 'nueva': 0.2, 'nuevos': 0.2, 'nuevas': 0.2,
            'proyecto': 0.25, 'proyectos': 0.25, 'plan': 0.2, 'planes': 0.2,
            'estrategia': 0.25, 'meta': 0.25, 'objetivo': 0.2, 'objetivos': 0.2,
            'aprueba': 0.3, 'aprobacion': 0.3, 'autoriza': 0.3, 'autorizacion': 0.3,
            'firma': 0.25, 'firmo': 0.25, 'firmado': 0.25, 'cierra': 0.25,
            'anuncia': 0.2, 'anuncio': 0.2, 'presenta': 0.2, 'presentacion': 0.2,
            'lanza': 0.3, 'lanzamiento': 0.3, 'estrena': 0.3, 'inaugura': 0.35,
            'inauguracion': 0.35, 'abre': 0.25, 'apertura': 0.25, 'inicia': 0.2,
            'activa': 0.25, 'activacion': 0.25, 'renueva': 0.3, 'renovacion': 0.3,
            'destina': 0.2, 'destinan': 0.2, 'asigna': 0.2, 'asignacion': 0.2,
            'anticipa': 0.25, 'espera': 0.15, 'esperado': 0.15, 'previsto': 0.15,
            'cumple': 0.3, 'cumplimiento': 0.3, 'alcanza': 0.35, 'obtiene': 0.3,
            'duplica': 0.4, 'triplica': 0.45, 'multiplica': 0.35, 'incrementa': 0.3,
            'suma': 0.2, 'adicional': 0.2, 'adicionales': 0.2, 'extra': 0.2,
            'mayor': 0.25, 'mayores': 0.25, 'mas': 0.15, 'mejor': 0.3, 'mejores': 0.3,
            'superior': 0.3, 'supera': 0.35, 'supero': 0.35, 'excelente': 0.4,
            'destacado': 0.35, 'destaca': 0.3, 'sobresale': 0.35, 'lidera': 0.35,
            'lider': 0.35, 'liderazgo': 0.35, 'primero': 0.3, 'primera': 0.3
        }
        
        negative_economic = {
            # Caídas y bajas (-0.4 a -0.6)
            'cae': -0.55, 'caida': -0.55, 'cayo': -0.55, 'cayeron': -0.55,
            'baja': -0.5, 'bajo': -0.5, 'bajaron': -0.5, 'descenso': -0.5,
            'desciende': -0.5, 'descendio': -0.5, 'desploma': -0.65,
            'desplome': -0.65, 'desplomo': -0.65, 'derrumba': -0.65,
            'derrumbe': -0.65, 'colapsa': -0.7, 'colapso': -0.7,
            
            # Pérdidas (-0.4 a -0.7)
            'pierde': -0.55, 'perdida': -0.55, 'perdidas': -0.55,
            'perdio': -0.55, 'perdieron': -0.55, 'deficit': -0.6,
            'deficitario': -0.6, 'quebranto': -0.65, 'merma': -0.5,
            
            # Crisis y recesión (-0.6 a -0.8)
            'crisis': -0.7, 'recesion': -0.7, 'recesivo': -0.7,
            'depresion': -0.75, 'quiebra': -0.8, 'bancarrota': -0.8,
            'insolvencia': -0.75, 'impago': -0.7, 'default': -0.75,
            
            # Problemas y riesgos (-0.3 a -0.6)
            'riesgo': -0.45, 'riesgos': -0.45, 'riesgoso': -0.45,
            'problema': -0.5, 'problemas': -0.5, 'dificultad': -0.5,
            'dificultades': -0.5, 'complicacion': -0.5, 'amenaza': -0.55,
            'amenazas': -0.55, 'peligro': -0.55, 'peligros': -0.55,
            
            # Afectaciones (-0.35 a -0.6)
            'afecta': -0.5, 'afectacion': -0.5, 'afectado': -0.5,
            'impacta': -0.45, 'impacto': -0.4, 'golpea': -0.55,
            'golpe': -0.55, 'dana': -0.55, 'dano': -0.55, 'danos': -0.55,
            'perjudica': -0.55, 'perjuicio': -0.55, 'deteriora': -0.55,
            'deterioro': -0.55, 'debilita': -0.55, 'debilitamiento': -0.55,
            
            # Inflación y devaluación (-0.45 a -0.7)
            'inflacion': -0.6, 'inflacionario': -0.6, 'devaluacion': -0.6,
            'devalua': -0.6, 'devaluo': -0.6, 'deprecia': -0.55,
            'depreciacion': -0.55, 'deprecio': -0.55, 'desvaloriza': -0.55,
            
            # Desaceleración y estancamiento (-0.4 a -0.6)
            'desaceleracion': -0.55, 'desacelera': -0.55, 'ralentiza': -0.5,
            'ralentizacion': -0.5, 'estancamiento': -0.6, 'estanca': -0.6,
            'estancado': -0.6, 'paraliza': -0.65, 'paralizacion': -0.65,
            'frena': -0.5, 'freno': -0.5, 'frenada': -0.5,
            
            # Inestabilidad y desconfianza (-0.45 a -0.65)
            'inestabilidad': -0.6, 'inestable': -0.6, 'volatilidad': -0.5,
            'volatil': -0.5, 'incertidumbre': -0.55, 'incierto': -0.55,
            'desconfianza': -0.55, 'desconfian': -0.55, 'desconfia': -0.55,
            'temor': -0.5, 'miedo': -0.5, 'panico': -0.65, 'nerviosismo': -0.5,
            
            # Desempleo y escasez (-0.5 a -0.7)
            'desempleo': -0.65, 'desempleado': -0.65, 'despido': -0.65,
            'despidos': -0.65, 'escasez': -0.6, 'escaso': -0.55,
            'carencia': -0.55, 'falta': -0.45, 'faltan': -0.45,
            
            # Corrupción y delitos (-0.6 a -0.8)
            'corrupcion': -0.7, 'corrupto': -0.7, 'fraude': -0.75,
            'fraudulento': -0.75, 'soborno': -0.7, 'lavado': -0.7,
            'ilegal': -0.65, 'ilicito': -0.65, 'delito': -0.65,
            
            # Conflictos (-0.5 a -0.8)
            'guerra': -0.75, 'conflicto': -0.6, 'violencia': -0.7,
            'violento': -0.7, 'huelga': -0.6, 'paro': -0.55,
            'protesta': -0.5, 'manifestacion': -0.45, 'disturbios': -0.65,
            
            # Negación y rechazo (-0.4 a -0.6)
            'niega': -0.45, 'negacion': -0.45, 'rechaza': -0.5,
            'rechazo': -0.5, 'suspende': -0.55, 'suspension': -0.55,
            'cancela': -0.55, 'cancelacion': -0.55, 'anula': -0.5,
            
            # Reducción y recorte (-0.35 a -0.55)
            'reduce': -0.5, 'reduccion': -0.5, 'disminuye': -0.5,
            'disminucion': -0.5, 'recorte': -0.55, 'recorta': -0.55,
            'recortaron': -0.55, 'contraccion': -0.55, 'contrae': -0.55,
            
            # Emergencia y catástrofe (-0.5 a -0.75)
            'emergencia': -0.6, 'emergente': -0.55, 'catastrofe': -0.75,
            'catastrofico': -0.75, 'desastre': -0.75, 'desastroso': -0.75,
            'tragedia': -0.7, 'tragico': -0.7, 'grave': -0.55, 'critico': -0.6,
            
            # Adicionales negativos (-0.4 a -0.65)
            'fuga': -0.65, 'sancion': -0.6, 'sanciones': -0.6,
            'penaliza': -0.55, 'penalizacion': -0.55, 'multa': -0.5,
            'perdurable': -0.45, 'adverso': -0.55, 'adversidad': -0.55,
            'desfavorable': -0.55, 'negativo': -0.5, 'negativa': -0.5,
            'pesimismo': -0.55, 'pesimista': -0.55, 'sombrio': -0.55,
            
            # Palabras económicas comunes negativas (-0.15 a -0.35)
            'no': -0.15, 'sin': -0.2, 'menos': -0.25, 'menor': -0.25, 'menores': -0.25,
            'cierra': -0.3, 'cierre': -0.3, 'cerro': -0.3, 'cerraron': -0.3,
            'clausura': -0.35, 'clausuro': -0.35, 'termina': -0.25, 'termino': -0.25,
            'detiene': -0.3, 'detenido': -0.3, 'detencion': -0.3, 'para': -0.25,
            'parado': -0.3, 'paraliza': -0.35, 'paralizado': -0.35,
            'limita': -0.3, 'limitacion': -0.3, 'limitado': -0.3, 'restringe': -0.35,
            'restriccion': -0.35, 'restringido': -0.35, 'prohibe': -0.4,
            'prohibicion': -0.4, 'veto': -0.4, 'bloquea': -0.4, 'bloqueo': -0.4,
            'retrasa': -0.35, 'retraso': -0.35, 'demora': -0.3, 'demorado': -0.3,
            'aplaza': -0.3, 'aplazamiento': -0.3, 'pospone': -0.3, 'posterga': -0.3,
            'elimina': -0.35, 'eliminacion': -0.35, 'elimino': -0.35,
            'suprime': -0.35, 'supresion': -0.35, 'suprimio': -0.35,
            'retira': -0.3, 'retiro': -0.3, 'retiraron': -0.3, 'abandona': -0.4,
            'abandono': -0.4, 'renuncia': -0.35, 'renuncio': -0.35,
            'falla': -0.35, 'fallo': -0.35, 'fallido': -0.35, 'fracasa': -0.4,
            'fracaso': -0.4, 'fracasado': -0.4, 'incumple': -0.4,
            'incumplimiento': -0.4, 'incumplido': -0.4, 'evita': -0.25,
            'evitado': -0.25, 'previene': -0.2, 'prevencion': -0.2,
            'advierte': -0.3, 'advertencia': -0.3, 'alerta': -0.35,
            'preocupa': -0.35, 'preocupacion': -0.35, 'preocupante': -0.35,
            'inquieta': -0.3, 'inquietud': -0.3, 'inquietante': -0.3,
            'debil': -0.35, 'debilidad': -0.35, 'fragil': -0.4, 'fragilidad': -0.4,
            'vulnerable': -0.35, 'vulnerabilidad': -0.35, 'peor': -0.35, 'peores': -0.35,
            'inferior': -0.3, 'inferiores': -0.3, 'bajo': -0.25, 'minimo': -0.3
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
            
            # Combinar con pesos optimizados: Keywords 65%, TextBlob 25%, VADER 10%
            # Keywords tienen más peso porque son específicos del dominio económico
            base_score = (keyword_score * 0.65) + (textblob_polarity * 0.25) + (vader_compound * 0.1)
            
            # AMPLIFICACIÓN: Multiplicar por 2.5 para mayor variación visual
            amplified_score = base_score * 2.5
            
            # NORMALIZACIÓN: Ajustar para que el promedio esté alrededor de 0.26 (como COLCAP)
            # Offset de +0.26 para alinear con el punto de inicio del COLCAP
            final_score = amplified_score + 0.26
            
            # Limitar a rango razonable para visualización
            final_score = max(-0.5, min(1.2, final_score))
            
            # Umbrales ajustados para la nueva escala
            if final_score >= 0.30:  # Por encima del baseline 0.26
                label = 'positive'
            elif final_score <= 0.22:  # Por debajo del baseline 0.26
                label = 'negative'
            else:
                label = 'neutral'
            
            return final_score, label
                
        except Exception as e:
            logger.error(f"Error en análisis de sentimiento: {str(e)}")
            # Fallback: usar solo keywords con amplificación y normalización
            amplified = keyword_score * 2.5 + 0.26
            amplified = max(-0.5, min(1.2, amplified))
            return amplified, ('positive' if amplified > 0.30 else ('negative' if amplified < 0.22 else 'neutral'))
    
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
                # Procesar cada 10 segundos (acelerado para demo)
                time.sleep(10)
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
