"""
Common Crawl News Collector - Para datos históricos
Recolecta noticias históricas de Colombia del último año
Compatible con la misma estructura de base de datos que GDELT
"""

import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import psycopg2
import requests
from bs4 import BeautifulSoup

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CommonCrawlCollector:
    """Recolector de noticias históricas desde Common Crawl News"""

    def __init__(self):
        # Configuración de PostgreSQL (igual que GDELT)
        self.db_config = {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "dbname": os.getenv("POSTGRES_DB", "news_colcap"),
            "user": os.getenv("POSTGRES_USER", "newsuser"),
            "password": os.getenv("POSTGRES_PASSWORD", "newspass123"),
        }

        # Mismos keywords económicos que GDELT
        self.economic_keywords = [
            "colombia economía",
            "colombia economy",
            "colombia bolsa",
            "colombia stock",
            "colombia finanzas",
            "colombia finance",
            "colcap",
            "BVC colombia",
            "colombia peso",
            "colombia banco",
            "bancolombia",
            "banco bogotá",
            "ecopetrol",
            "avianca",
            "colombia petróleo",
            "colombia oil",
            "colombia inflación",
            "colombia inflation",
            "colombia PIB",
            "colombia GDP",
            "colombia exportación",
            "colombia export",
            "colombia comercio",
            "colombia TRM",
            "colombia dólar",
            "colombia dollar",
        ]

        # Base URL para Common Crawl Index API
        self.cc_index_url = "https://index.commoncrawl.org/CC-MAIN-{}-index"

        # Índices de Common Crawl (actualizados mensualmente)
        # Formato: CC-MAIN-YYYY-WW (año-semana)
        self.available_indices = self._get_recent_indices()

        logger.info("Common Crawl Collector inicializado")
        logger.info(f"Keywords: {len(self.economic_keywords)}")
        logger.info(f"Índices disponibles: {len(self.available_indices)}")

    def _get_recent_indices(self) -> List[str]:
        """Obtener los índices de Common Crawl del último año"""
        indices = []

        # Common Crawl publica índices mensualmente
        # Generar índices del último año (aproximadamente 12 índices)
        end_date = datetime.now()

        # Lista de índices conocidos recientes (2024-2025)
        # Common Crawl usa formato CC-MAIN-YYYY-WW donde WW es la semana del año
        known_indices = [
            "2024-51",
            "2024-46",
            "2024-42",
            "2024-38",
            "2024-33",  # 2024
            "2024-30",
            "2024-26",
            "2024-22",
            "2024-18",
            "2024-10",
            "2025-04",  # 2025 (si está disponible)
        ]

        indices = [f"CC-MAIN-{idx}" for idx in known_indices]

        logger.info(
            f"Índices a consultar: {', '.join(indices[:3])}... (total: {len(indices)})"
        )
        return indices

    def get_db_connection(self):
        """Obtener conexión a PostgreSQL"""
        return psycopg2.connect(**self.db_config)

    def search_commoncrawl(
        self, keyword: str, index: str, max_results: int = 100
    ) -> List[Dict]:
        """Buscar en Common Crawl Index por keyword"""
        articles = []

        try:
            # Construir URL de búsqueda
            search_url = f"https://index.commoncrawl.org/{index}-index"
            params = {
                "url": f"*.com/*",  # Buscar en dominios .com
                "filter": f"~text:{keyword}",  # Filtro de texto
                "output": "json",
                "limit": max_results,
            }

            # Alternativa: usar cdx-api para búsquedas más específicas
            cdx_url = f"https://index.commoncrawl.org/{index}-index"
            query_url = (
                f"{cdx_url}?url=*.co/*&matchType=domain&filter=status:200&output=json"
            )

            response = requests.get(query_url, timeout=30)

            if response.status_code == 200:
                lines = response.text.strip().split("\n")

                for line in lines[:max_results]:
                    try:
                        record = json.loads(line)

                        # Filtrar solo si contiene el keyword
                        url = record.get("url", "")

                        # Verificar si es de Colombia o contiene keywords
                        if self._is_relevant_url(url, keyword):
                            articles.append(
                                {
                                    "url": url,
                                    "timestamp": record.get("timestamp"),
                                    "filename": record.get("filename"),
                                    "offset": record.get("offset"),
                                    "length": record.get("length"),
                                }
                            )
                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            logger.warning(f"Error buscando '{keyword}' en {index}: {str(e)}")

        return articles

    def _is_relevant_url(self, url: str, keyword: str) -> bool:
        """Verificar si la URL es relevante para el keyword"""
        url_lower = url.lower()
        keyword_lower = keyword.lower()

        # Dominios colombianos
        colombian_domains = [".co/", ".com.co/", "colombia", "bogota", "medellin"]

        # Dominios de noticias económicas
        news_domains = [
            "eltiempo",
            "semana",
            "portafolio",
            "larepublica",
            "dinero",
            "elespectador",
            "bloomberg",
            "reuters",
            "wsj",
            "ft.com",
            "eleconomista",
        ]

        # Verificar si es de Colombia o de medios económicos
        is_colombian = any(domain in url_lower for domain in colombian_domains)
        is_economic_news = any(domain in url_lower for domain in news_domains)

        # Verificar si contiene el keyword
        keyword_parts = keyword_lower.split()
        contains_keyword = any(
            part in url_lower for part in keyword_parts if len(part) > 3
        )

        return (is_colombian or is_economic_news) and contains_keyword

    def fetch_article_content(self, warc_record: Dict) -> Optional[Dict]:
        """Obtener contenido del artículo desde archivo WARC"""
        try:
            # Construir URL para obtener el contenido
            warc_url = f"https://data.commoncrawl.org/{warc_record['filename']}"

            headers = {
                "Range": f"bytes={warc_record['offset']}-{warc_record['offset'] + warc_record['length']}"
            }

            response = requests.get(warc_url, headers=headers, timeout=30)

            if response.status_code in [200, 206]:
                # Parsear el contenido HTML
                # El formato WARC incluye headers HTTP, necesitamos extraer solo el HTML
                content = response.content

                # Buscar el HTML (después de los headers WARC)
                html_start = content.find(b"<!DOCTYPE") or content.find(b"<html")

                if html_start > 0:
                    html_content = content[html_start:]
                    soup = BeautifulSoup(html_content, "html.parser")

                    # Extraer título
                    title = soup.find("title")
                    title_text = (
                        title.get_text().strip() if title else warc_record["url"]
                    )

                    # Extraer fecha de publicación (intentar varios métodos)
                    pub_date = self._extract_publish_date(
                        soup, warc_record["timestamp"]
                    )

                    # Extraer texto del artículo
                    article_text = self._extract_article_text(soup)

                    return {
                        "title": title_text[:500],  # Limitar a 500 chars
                        "url": warc_record["url"],
                        "published_date": pub_date,
                        "content": article_text[:5000],  # Limitar a 5000 chars
                        "source": self._extract_source(warc_record["url"]),
                    }

        except Exception as e:
            logger.debug(
                f"Error obteniendo contenido de {warc_record.get('url', 'unknown')}: {str(e)}"
            )

        return None

    def _extract_publish_date(self, soup: BeautifulSoup, timestamp: str) -> datetime:
        """Extraer fecha de publicación del HTML"""
        # Intentar encontrar fecha en meta tags
        date_meta_tags = [
            ("meta", {"property": "article:published_time"}),
            ("meta", {"name": "date"}),
            ("meta", {"name": "pubdate"}),
            ("time", {"datetime": True}),
        ]

        for tag, attrs in date_meta_tags:
            element = soup.find(tag, attrs)
            if element:
                date_str = element.get("content") or element.get("datetime")
                if date_str:
                    try:
                        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    except:
                        pass

        # Si no se encuentra, usar el timestamp del WARC
        # Formato timestamp: YYYYMMDDhhmmss
        try:
            return datetime.strptime(timestamp, "%Y%m%d%H%M%S")
        except:
            return datetime.now()

    def _extract_article_text(self, soup: BeautifulSoup) -> str:
        """Extraer texto del artículo"""
        # Remover scripts y estilos
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        # Buscar el contenido principal
        article = soup.find("article") or soup.find(
            "div", class_=re.compile("article|content|post")
        )

        if article:
            text = article.get_text(separator=" ", strip=True)
        else:
            text = soup.get_text(separator=" ", strip=True)

        # Limpiar texto
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _extract_source(self, url: str) -> str:
        """Extraer nombre de la fuente desde la URL"""
        try:
            from urllib.parse import urlparse

            domain = urlparse(url).netloc
            # Remover www. y .com/.co
            source = domain.replace("www.", "").split(".")[0]
            return source.title()
        except:
            return "Common Crawl"

    def collect_from_indices(self, days_back: int = 365) -> List[Dict]:
        """Recolectar noticias de múltiples índices"""
        all_articles = []
        article_urls = set()  # Para deduplicación

        logger.info(
            f"🔍 Iniciando recolección de Common Crawl (últimos {days_back} días)"
        )

        # Limitar a los primeros índices (más recientes)
        indices_to_search = self.available_indices[:6]  # ~6 meses de datos

        for index_idx, index in enumerate(indices_to_search, 1):
            logger.info(
                f"📥 Procesando índice {index_idx}/{len(indices_to_search)}: {index}"
            )

            for keyword_idx, keyword in enumerate(
                self.economic_keywords[:20], 1
            ):  # Primeros 20 keywords
                try:
                    # Buscar artículos para este keyword
                    warc_records = self.search_commoncrawl(
                        keyword, index, max_results=50
                    )

                    logger.info(
                        f"  [{keyword_idx}/20] '{keyword}': {len(warc_records)} encontrados"
                    )

                    # Procesar cada registro WARC (limitar a 10 por keyword para no sobrecargar)
                    for record in warc_records[:10]:
                        if record["url"] in article_urls:
                            continue  # Skip duplicados

                        article = self.fetch_article_content(record)

                        if article and len(article["title"]) > 10:
                            article_urls.add(record["url"])
                            all_articles.append(article)

                    # Pequeña pausa para no sobrecargar el servidor
                    time.sleep(0.5)

                except Exception as e:
                    logger.warning(f"Error procesando keyword '{keyword}': {str(e)}")
                    continue

            logger.info(
                f"✅ Índice {index} completado. Total acumulado: {len(all_articles)}"
            )

            # Si ya tenemos suficientes artículos, parar
            if len(all_articles) >= 2000:
                logger.info("✅ Alcanzado límite de 2000 artículos")
                break

        logger.info(f"📊 Total recolectado: {len(all_articles)} artículos únicos")
        return all_articles

    def save_to_database(self, articles: List[Dict]) -> int:
        """Guardar artículos en la base de datos (misma tabla que GDELT)"""
        if not articles:
            return 0

        conn = self.get_db_connection()
        cursor = conn.cursor()
        saved = 0

        try:
            for article in articles:
                try:
                    cursor.execute(
                        """
                        INSERT INTO news (title, url, content, source, published_date, collected_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (url) DO NOTHING
                    """,
                        (
                            article["title"],
                            article["url"],
                            article.get("content", ""),
                            article["source"],
                            article["published_date"],
                            datetime.now(),
                        ),
                    )

                    if cursor.rowcount > 0:
                        saved += 1

                except Exception as e:
                    logger.debug(f"Error insertando artículo: {str(e)}")
                    continue

            conn.commit()
            logger.info(f"💾 Guardados: {saved} artículos nuevos en la BD")

        except Exception as e:
            conn.rollback()
            logger.error(f"Error en transacción: {str(e)}")
        finally:
            cursor.close()
            conn.close()

        return saved

    def run(self, days_back: int = 365):
        """Ejecutar recolección completa"""
        logger.info("=" * 70)
        logger.info("🚀 Common Crawl Historical Collection")
        logger.info("=" * 70)

        start = time.time()

        # Recolectar artículos
        articles = self.collect_from_indices(days_back)

        # Guardar en BD
        saved = self.save_to_database(articles)

        elapsed = time.time() - start
        logger.info(
            f"✅ Completado en {int(elapsed)}s - {len(articles)} artículos, {saved} nuevos guardados"
        )
        logger.info("=" * 70)

        return saved


def main():
    """Función principal para ejecutar desde línea de comandos"""
    logger.info("🌐 Common Crawl News Collector - Datos Históricos")

    collector = CommonCrawlCollector()

    # Recolectar noticias del último año
    days = int(os.getenv("CC_DAYS_BACK", 365))
    saved = collector.run(days_back=days)

    logger.info(f"✅ Proceso finalizado. {saved} noticias históricas agregadas.")


if __name__ == "__main__":
    main()
