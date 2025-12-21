"""
DEMO SIMPLIFICADA - Processor
Analiza sentimiento de las noticias obtenidas
"""
import json
import re
import unicodedata
from nltk.sentiment import SentimentIntensityAnalyzer
from textblob import TextBlob

def normalize_text(text):
    """
    Normaliza el texto: minúsculas, sin tildes, lematización básica
    """
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
        'disminuyo': 'disminuye', 'disminuyeron': 'disminuye', 'disminuyendo': 'disminuye',
        'perdio': 'pierde', 'perdieron': 'pierde', 'perdiendo': 'pierde',
        'gano': 'gana', 'ganaron': 'gana', 'ganando': 'gana',
        'mejoro': 'mejora', 'mejoraron': 'mejora', 'mejorando': 'mejora',
        'empeoro': 'empeora', 'empeoraron': 'empeora', 'empeorando': 'empeora',
        'logro': 'logra', 'lograron': 'logra', 'logrando': 'logra',
        'fracaso': 'fracasa', 'fracasaron': 'fracasa', 'fracasando': 'fracasa',
        'recupero': 'recupera', 'recuperaron': 'recupera', 'recuperando': 'recupera',
        'afecto': 'afecta', 'afectaron': 'afecta', 'afectando': 'afecta',
        'impulso': 'impulsa', 'impulsaron': 'impulsa', 'impulsando': 'impulsa',
        'declino': 'declina', 'declinaron': 'declina', 'declinando': 'declina'
    }
    
    words = text.split()
    normalized_words = [lemmatization_rules.get(w, w) for w in words]
    return ' '.join(normalized_words)

def analyze_sentiment_enhanced(text):
    """
    Análisis de sentimiento AVANZADO con normalización, intensificadores y negaciones
    """
    if not text:
        return 0.0, 'neutral'
    
    # Normalizar texto
    text_normalized = normalize_text(text)
    
    # DICCIONARIO DE INTENSIFICADORES
    intensifiers = {
        'muy': 1.5,
        'significativamente': 1.7,
        'fuertemente': 1.6,
        'drasticamente': 1.8,
        'ligeramente': 0.7,
        'moderadamente': 0.85,
        'extremadamente': 1.9,
        'altamente': 1.6,
        'sumamente': 1.7,
        'enormemente': 1.8,
        'considerablemente': 1.6,
        'notablemente': 1.5,
        'marcadamente': 1.6,
        'profundamente': 1.7,
        'severamente': 1.7,
        'agudamente': 1.6,
        'apenas': 0.6,
        'escasamente': 0.6,
        'poco': 0.7,
        'relativamente': 0.8,
        'bastante': 1.3,
        'demasiado': 1.4
    }
    
    # DICCIONARIO DE NEGACIONES
    negations = [
        'no', 'nunca', 'jamas', 'sin', 'evita', 'evito', 'ni',
        'tampoco', 'nada', 'nadie', 'ninguno', 'ninguna',
        'imposible', 'niega', 'nego', 'rechaza', 'rechazo',
        'impide', 'impidio', 'detiene', 'detuvo', 'frena', 'freno'
    ]
    
    # KEYWORDS ECONÓMICAS EXPANDIDAS
    positive_economic = {
        # Crecimiento
        'crece': 0.4, 'crecimiento': 0.4, 'aumenta': 0.3, 'aumento': 0.3, 'incremento': 0.3,
        'sube': 0.35, 'subida': 0.35, 'gana': 0.3, 'ganancia': 0.35,
        
        # Éxito
        'exito': 0.5, 'exitoso': 0.5, 'logro': 0.4, 'logra': 0.4,
        'record': 0.45, 'historico': 0.4,
        
        # Inversión y expansión
        'inversion': 0.3, 'invierte': 0.3, 'desarrollo': 0.25,
        'expansion': 0.35, 'recupera': 0.4, 'recuperacion': 0.4,
        
        # Mejora general
        'mejora': 0.35, 'positivo': 0.4, 'optimismo': 0.45,
        'fortalecer': 0.3, 'impulsa': 0.35, 'beneficio': 0.4,
        'rentable': 0.4, 'oportunidad': 0.3, 'progreso': 0.35,
        
        # Valores monetarios
        'millones': 0.25, 'billones': 0.3, 'dolares': 0.2,
        
        # Negocios
        'reconocida': 0.25, 'importante': 0.2, 'condecora': 0.35,
        'sostenibilidad': 0.3, 'negociacion': 0.25, 'priorizar': 0.25,
        'exporta': 0.3, 'vende': 0.25, 'contrato': 0.2,
        'acuerdo': 0.25, 'alianza': 0.3, 'lanza': 0.25, 'inaugura': 0.3,
        
        # NUEVAS - Estabilidad y confianza
        'estabilidad': 0.35, 'reactivacion': 0.4, 'superavit': 0.45,
        'confianza': 0.35, 'liquidez': 0.3, 'dinamiza': 0.35,
        'solidez': 0.4, 'competitividad': 0.35, 'sostenido': 0.4,
        'atraccion': 0.4, 'innovacion': 0.35, 'modernizacion': 0.35,
        'eficiencia': 0.3, 'productividad': 0.35, 'rentabilidad': 0.4,
        'fortalecimiento': 0.35, 'consolidacion': 0.35,
        'repunte': 0.4, 'auge': 0.45, 'bonanza': 0.5,
        'prospera': 0.45, 'prosperidad': 0.45, 'floreciente': 0.4,
        'favorable': 0.3, 'promisorio': 0.35, 'prometedor': 0.35
    }
    
    negative_economic = {
        # Caídas y pérdidas
        'cae': -0.4, 'caida': -0.4, 'baja': -0.3, 'disminuye': -0.35, 'reduce': -0.3,
        'pierde': -0.35, 'perdida': -0.4,
        
        # Crisis severa
        'crisis': -0.6, 'quiebra': -0.7, 'deficit': -0.45, 'deuda': -0.35,
        'recesion': -0.6, 'desplome': -0.6, 'colapso': -0.7,
        
        # Riesgos y amenazas
        'riesgo': -0.3, 'amenaza': -0.4, 'fracaso': -0.5,
        'preocupa': -0.35, 'preocupacion': -0.35,
        'afecta': -0.3, 'afectara': -0.3, 'daño': -0.4, 'problema': -0.3,
        'dificultad': -0.35, 'incertidumbre': -0.4, 'volatilidad': -0.3,
        
        # Deterioro
        'negativo': -0.4, 'declive': -0.4, 'deterioro': -0.45, 'empeora': -0.4,
        'suspende': -0.35, 'cierra': -0.3, 'despido': -0.5,
        
        # Violencia y conflicto
        'emergencia': -0.4, 'dictadura': -0.6, 'combaten': -0.3, 'mercenarios': -0.4,
        'guerra': -0.5, 'conflicto': -0.4, 'asesina': -0.6, 'violencia': -0.5,
        
        # NUEVAS - Económicas negativas
        'inflacion': -0.45, 'devaluacion': -0.4, 'desaceleracion': -0.4,
        'inestabilidad': -0.45, 'fuga': -0.5, 'sobreendeudamiento': -0.5,
        'desconfianza': -0.35, 'estancamiento': -0.4, 'corrupcion': -0.6,
        'sanciones': -0.45, 'multa': -0.35, 'penalizacion': -0.35,
        'contraccion': -0.4, 'depreciacion': -0.35, 'bancarrota': -0.7,
        'insolvencia': -0.6, 'morosidad': -0.4, 'impago': -0.45,
        'rescate': -0.4, 'intervencion': -0.35, 'ajuste': -0.3,
        'recorte': -0.35, 'austeridad': -0.35, 'desempleo': -0.5,
        'paro': -0.45, 'huelga': -0.4, 'protesta': -0.35,
        'escasez': -0.4, 'desabastecimiento': -0.45, 'racionamiento': -0.45
    }
    
    # PASO 1: Detectar intensificadores y negaciones
    words = text_normalized.split()
    scores = []
    
    i = 0
    while i < len(words):
        word = words[i]
        intensifier = 1.0
        is_negated = False
        
        # Verificar si hay intensificador antes
        if i > 0 and words[i-1] in intensifiers:
            intensifier = intensifiers[words[i-1]]
        
        # Verificar si hay negación antes (1-2 palabras atrás)
        if i > 0 and words[i-1] in negations:
            is_negated = True
        elif i > 1 and words[i-2] in negations:
            is_negated = True
        
        # Buscar en keywords positivas
        if word in positive_economic:
            score = positive_economic[word] * intensifier
            if is_negated:
                score = -score  # Invertir si está negado
            scores.append(score)
        
        # Buscar en keywords negativas
        elif word in negative_economic:
            score = negative_economic[word] * intensifier
            if is_negated:
                score = -score  # Invertir si está negado (doble negativo = positivo)
            scores.append(score)
        
        i += 1
    
    # Sumar todos los scores de keywords
    keyword_score = sum(scores)
    
    # PASO 2: Análisis con VADER (inglés)
    try:
        sia = SentimentIntensityAnalyzer()
        vader_scores = sia.polarity_scores(text)
        vader_compound = vader_scores['compound']
    except:
        vader_compound = 0.0
    
    # PASO 3: Análisis con TextBlob (mejor para español)
    try:
        blob = TextBlob(text)
        textblob_polarity = blob.sentiment.polarity
    except:
        textblob_polarity = 0.0
    
    # PASO 4: Combinar scores con pesos
    # Keywords tienen MÁS peso (70%), luego TextBlob (20%), luego VADER (10%)
    final_score = (keyword_score * 0.7) + (textblob_polarity * 0.2) + (vader_compound * 0.1)
    
    # Normalizar a rango -1 a 1
    final_score = max(-1.0, min(1.0, final_score))
    
    # Clasificar con thresholds bajos (muy sensible)
    if final_score >= 0.08:
        label = 'positive'
    elif final_score <= -0.08:
        label = 'negative'
    else:
        label = 'neutral'
    
    return final_score, label

print("=" * 60)
print("DEMO: News Sentiment Processor (AVANZADO)")
print("=" * 60)

# Cargar noticias
try:
    with open('data/news.json', 'r', encoding='utf-8') as f:
        articles = json.load(f)
    print(f"\nCargados {len(articles)} articulos")
except FileNotFoundError:
    print("\nERROR: Primero ejecuta 1_run_collector.py")
    exit(1)

# Inicializar analizador VADER
print("Inicializando analizador de sentimientos VADER...")
sia = SentimentIntensityAnalyzer()

# Categorías económicas
categories_keywords = {
    'mercados': ['bolsa', 'acciones', 'COLCAP', 'mercado'],
    'divisas': ['dolar', 'euro', 'peso', 'divisa'],
    'commodities': ['petroleo', 'oro', 'cafe'],
    'banca': ['banco', 'financiero', 'credito'],
    'empresas': ['empresa', 'negocio', 'compania'],
    'politica_economica': ['gobierno', 'reforma', 'impuesto'],
    'comercio': ['exportacion', 'importacion', 'comercio']
}

processed_articles = []
sentiment_stats = {'positive': 0, 'negative': 0, 'neutral': 0}

print("\nProcesando articulos...")
print("-" * 60)

for i, article in enumerate(articles, 1):
    title = article.get('title', '')
    
    # Análisis de sentimiento MEJORADO
    compound, label = analyze_sentiment_enhanced(title)
    
    # Clasificar
    sentiment_stats[label] += 1
    
    # Clasificar categorías
    text_lower = title.lower()
    categories = []
    for category, keywords in categories_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            categories.append(category)
    if not categories:
        categories = ['general']
    
    # Guardar resultado
    processed = {
        'title': title,
        'url': article.get('url', ''),
        'domain': article.get('domain', ''),
        'sentiment_score': compound,
        'sentiment_label': label,
        'categories': categories
    }
    processed_articles.append(processed)
    
    # Mostrar primeros 10
    if i <= 10:
        emoji = "+" if label == 'positive' else ("-" if label == 'negative' else "=")
        print(f"{i:2}. [{emoji}] {compound:+.2f} | {title[:50]}...")

# Guardar resultados procesados
with open('data/processed_news.json', 'w', encoding='utf-8') as f:
    json.dump(processed_articles, f, indent=2, ensure_ascii=False)

print(f"\n{'='*60}")
print(f"RESULTADOS DEL PROCESAMIENTO:")
print(f"  Total procesados: {len(processed_articles)}")
print(f"  Positivas: {sentiment_stats['positive']} ({sentiment_stats['positive']/len(processed_articles)*100:.1f}%)")
print(f"  Negativas: {sentiment_stats['negative']} ({sentiment_stats['negative']/len(processed_articles)*100:.1f}%)")
print(f"  Neutrales: {sentiment_stats['neutral']} ({sentiment_stats['neutral']/len(processed_articles)*100:.1f}%)")

# Calcular sentimiento promedio
avg_sentiment = sum(a['sentiment_score'] for a in processed_articles) / len(processed_articles)
print(f"  Sentimiento promedio: {avg_sentiment:+.3f}")
print(f"{'='*60}")

print(f"\nGuardado en: data/processed_news.json")
print(f"\nSiguiente paso: Ejecutar 3_run_analyzer.py")
print(f"{'='*60}")
