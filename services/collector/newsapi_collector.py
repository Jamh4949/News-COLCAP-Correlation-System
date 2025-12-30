"""
NewsAPI Collector - Alternativa a GDELT
Recolecta noticias históricas usando NewsAPI.org (30 días de histórico gratis)
Compatible con la misma estructura de base de datos
"""

import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List

import psycopg2
import requests

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class NewsAPICollector:
    """Recolector de noticias desde NewsAPI.org"""

    def __init__(self):
        # API Key de NewsAPI (obtener gratis en https://newsapi.org)
        self.api_key = os.getenv("NEWSAPI_KEY", "TU_API_KEY_AQUI")

        if self.api_key == "TU_API_KEY_AQUI":
            logger.warning(
                "⚠️  No se configuró NEWSAPI_KEY. Usa: https://newsapi.org para obtener una key gratuita"
            )

        # Configuración de PostgreSQL
        self.db_config = {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "database": os.getenv("POSTGRES_DB", "news_colcap"),
            "user": os.getenv("POSTGRES_USER", "newsuser"),
            "password": os.getenv("POSTGRES_PASSWORD", "newspass123"),
        }

        # Keywords económicos de Colombia
        self.keywords = [
            "Colombia economy",
            "Colombia stock market",
            "COLCAP",
            "Bancolombia",
            "Ecopetrol",
            "Colombia finance",
            "Colombia peso",
            "Colombia central bank",
            "Colombia inflation",
            "Colombia GDP",
            "Colombia exports",
            "Colombia oil",
        ]

        self.base_url = "https://newsapi.org/v2/everything"

        logger.info("NewsAPI Collector inicializado")
        logger.info(f"Keywords: {len(self.keywords)}")

    def get_db_connection(self):
        """Obtener conexión a PostgreSQL"""
        return psycopg2.connect(**self.db_config)

    def fetch_articles(
        self, keyword: str, from_date: datetime, to_date: datetime, page: int = 1
    ) -> Dict:
        """Buscar artículos en NewsAPI"""
        params = {
            "q": keyword,
            "from": from_date.strftime("%Y-%m-%d"),
            "to": to_date.strftime("%Y-%m-%d"),
            "language": "en",  # Inglés tiene más cobertura
            "sortBy": "relevancy",
            "pageSize": 100,
            "page": page,
            "apiKey": self.api_key,
        }

        try:
            response = requests.get(self.base_url, params=params, timeout=30)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 426:
                logger.error(
                    "❌ API Key requerida. Obtén una gratis en https://newsapi.org"
                )
                return {"articles": []}
            else:
                logger.warning(f"Error {response.status_code}: {response.text}")
                return {"articles": []}

        except Exception as e:
            logger.error(f"Error en request: {str(e)}")
            return {"articles": []}

    def collect_all_articles(self, days_back: int = 30) -> List[Dict]:
        """Recolectar todos los artículos disponibles"""
        all_articles = []
        article_urls = set()

        end_date = datetime.now()
        start_date = end_date - timedelta(
            days=min(days_back, 30)
        )  # Max 30 días en plan gratuito

        logger.info(
            f"🔍 Recolectando noticias del {start_date.date()} al {end_date.date()}"
        )

        for idx, keyword in enumerate(self.keywords, 1):
            logger.info(f"  [{idx}/{len(self.keywords)}] Buscando: '{keyword}'")

            try:
                result = self.fetch_articles(keyword, start_date, end_date)
                articles = result.get("articles", [])

                for article in articles:
                    url = article.get("url")

                    if url and url not in article_urls:
                        article_urls.add(url)

                        # Transformar al formato de nuestra BD
                        transformed = {
                            "title": article.get("title", "")[:500],
                            "url": url,
                            "content": (
                                article.get("description", "")
                                + " "
                                + article.get("content", "")
                            )[:5000],
                            "source": article.get("source", {}).get("name", "NewsAPI"),
                            "published_date": self._parse_date(
                                article.get("publishedAt")
                            ),
                        }

                        all_articles.append(transformed)

                logger.info(
                    f"    ✓ Encontrados: {len(articles)}, Únicos totales: {len(all_articles)}"
                )
                time.sleep(0.5)  # Pausita para no sobrecargar la API

            except Exception as e:
                logger.warning(f"Error con keyword '{keyword}': {str(e)}")
                continue

        logger.info(f"📊 Total recolectado: {len(all_articles)} artículos únicos")
        return all_articles

    def _parse_date(self, date_str: str) -> datetime:
        """Parsear fecha de NewsAPI"""
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except:
            return datetime.now()

    def save_to_database(self, articles: List[Dict]) -> int:
        """Guardar artículos en la base de datos"""
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
                            article["content"],
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

    def run(self, days_back: int = 30):
        """Ejecutar recolección completa"""
        logger.info("=" * 70)
        logger.info("🌐 NewsAPI Collection")
        logger.info("=" * 70)

        if self.api_key == "TU_API_KEY_AQUI":
            logger.error("❌ Configura NEWSAPI_KEY primero")
            logger.info("👉 Visita https://newsapi.org y obtén una API key gratuita")
            logger.info("👉 Luego ejecuta: $env:NEWSAPI_KEY='tu_key_aqui'")
            return 0

        start = time.time()

        # Recolectar artículos
        articles = self.collect_all_articles(days_back)

        # Guardar en BD
        saved = self.save_to_database(articles)

        elapsed = time.time() - start
        logger.info(
            f"✅ Completado en {int(elapsed)}s - {len(articles)} artículos, {saved} nuevos guardados"
        )
        logger.info("=" * 70)

        return saved


def main():
    """Función principal"""
    logger.info("🌐 NewsAPI Collector - Alternativa a GDELT")

    collector = NewsAPICollector()
    saved = collector.run(days_back=30)

    logger.info(f"✅ Proceso finalizado. {saved} noticias agregadas.")


if __name__ == "__main__":
    main()
