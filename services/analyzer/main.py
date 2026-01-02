"""
Analysis Service
Analiza correlaciones entre noticias y el índice COLCAP
Con ThreadPoolExecutor para operaciones I/O paralelas
"""

import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import psycopg2
import redis
import yfinance as yf
from psycopg2 import OperationalError
from psycopg2.extras import RealDictCursor, execute_values
from scipy import stats

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class COLCAPAnalyzer:
    """Analizador de correlaciones entre noticias y COLCAP"""

    def __init__(self):
        # Configuración de Redis
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            decode_responses=True,
        )

        # Configuración de PostgreSQL
        self.db_config = {
            "host": os.getenv("POSTGRES_HOST"),
            "dbname": os.getenv("POSTGRES_DB"),
            "user": os.getenv("POSTGRES_USER"),
            "password": os.getenv("POSTGRES_PASSWORD"),
            "port": 5432,
        }

        # Símbolo del COLCAP en Yahoo Finance (GXG es el ticker correcto)
        self.colcap_symbol = "GXG"

        logger.info("COLCAP Analyzer inicializado")

    def get_db_connection(self, retries=10, delay=5):
        for i in range(retries):
            try:
                return psycopg2.connect(**self.db_config)
            except OperationalError as e:
                print(f"[DB] Postgres not ready ({i + 1}/{retries}): {e}")
                time.sleep(delay)

        raise Exception("PostgreSQL not available after retries")

    def fetch_colcap_data(self, days_back: int = 90) -> pd.DataFrame:
        """Obtener datos históricos del COLCAP desde Yahoo Finance"""
        logger.info(f"Obteniendo datos COLCAP de los últimos {days_back} días")

        try:
            # Descargar datos usando yf.download (más confiable que Ticker().history())
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)

            # Formatear fechas como strings
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")

            logger.info(f"Descargando GXG desde {start_str} hasta {end_str}")

            # Usar yf.download con auto_adjust=True como en el ejemplo que funciona
            df = yf.download(
                "GXG", start=start_str, end=end_str, auto_adjust=True, progress=False
            )

            if df is None or df.empty:
                logger.warning("No se obtuvieron datos del COLCAP (DataFrame vacío)")
                return pd.DataFrame()

            logger.info(
                f"Datos descargados: {len(df)} filas, columnas: {df.columns.tolist()}"
            )

            # Resetear índice para tener la fecha como columna
            df.reset_index(inplace=True)

            # Calcular cambio diario porcentual
            df["Daily_Change"] = df["Close"].pct_change() * 100

            logger.info(f"✅ Obtenidos {len(df)} días de datos COLCAP exitosamente")
            return df

        except Exception as e:
            logger.error(f"❌ Error obteniendo datos COLCAP: {str(e)}")
            import traceback

            logger.error(traceback.format_exc())
            return pd.DataFrame()

    def save_colcap_data(self, df: pd.DataFrame):
        """Guardar datos del COLCAP en la base de datos usando BATCH INSERT"""
        if df.empty:
            logger.warning("DataFrame vacío, no hay datos COLCAP para guardar")
            return

        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            # Preparar datos para batch insert
            batch_data = []
            for idx, row in df.iterrows():
                try:
                    date_val = row["Date"]
                    if isinstance(date_val, pd.Timestamp):
                        date_val = date_val.date()

                    batch_data.append(
                        (
                            date_val,
                            float(row["Open"]) if not pd.isna(row["Open"]) else None,
                            float(row["High"]) if not pd.isna(row["High"]) else None,
                            float(row["Low"]) if not pd.isna(row["Low"]) else None,
                            float(row["Close"]) if not pd.isna(row["Close"]) else None,
                            int(row["Volume"]) if not pd.isna(row["Volume"]) else 0,
                            float(row["Close"]) if not pd.isna(row["Close"]) else None,
                            float(row["Daily_Change"])
                            if not pd.isna(row["Daily_Change"])
                            else 0.0,
                        )
                    )
                except Exception as e:
                    logger.error(f"Error preparando fecha {idx}: {str(e)}")
                    continue

            if not batch_data:
                return

            # BATCH UPSERT usando execute_values
            execute_values(
                cursor,
                """
                INSERT INTO colcap_data
                (date, open_price, high_price, low_price, close_price,
                 volume, adj_close, daily_change)
                VALUES %s
                ON CONFLICT (date)
                DO UPDATE SET
                    close_price = EXCLUDED.close_price,
                    daily_change = EXCLUDED.daily_change,
                    volume = EXCLUDED.volume
                """,
                batch_data,
                template="(%s, %s, %s, %s, %s, %s, %s, %s)",
                page_size=100,
            )

            conn.commit()
            logger.info(
                f"✅ BATCH guardados/actualizados {len(batch_data)} registros COLCAP"
            )

        except Exception as e:
            conn.rollback()
            logger.error(f"Error en transacción COLCAP: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def get_daily_news_sentiment(self, days_back: int = 90) -> pd.DataFrame:
        """Obtener sentimiento promedio de noticias por día"""
        conn = self.get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)

            cursor.execute(
                """
                SELECT
                    DATE(published_date) as date,
                    COUNT(*) as news_count,
                    AVG(sentiment_score) as avg_sentiment,
                    STDDEV(sentiment_score) as sentiment_stddev,
                    COUNT(CASE WHEN sentiment_label = 'positive' THEN 1 END) as positive_count,
                    COUNT(CASE WHEN sentiment_label = 'negative' THEN 1 END) as negative_count,
                    ARRAY_AGG(id) as news_ids
                FROM news
                WHERE published_date >= %s
                  AND published_date <= %s
                  AND sentiment_score IS NOT NULL
                GROUP BY DATE(published_date)
                ORDER BY date
            """,
                (start_date, end_date),
            )

            results = cursor.fetchall()

            if not results:
                logger.warning("No hay datos de sentimiento de noticias")
                return pd.DataFrame()

            df = pd.DataFrame(results)
            df["date"] = pd.to_datetime(df["date"])
            df.set_index("date", inplace=True)

            logger.info(f"Obtenidos datos de sentimiento para {len(df)} días")
            return df

        finally:
            cursor.close()
            conn.close()

    def calculate_correlation(
        self, news_df: pd.DataFrame, colcap_df: pd.DataFrame
    ) -> Dict:
        """Calcular correlación entre sentimiento de noticias y cambios en COLCAP"""

        # Merge de los dataframes por fecha
        merged = pd.merge(
            news_df[["avg_sentiment", "news_count"]],
            colcap_df[["Daily_Change"]],
            left_index=True,
            right_index=True,
            how="inner",
        )

        if len(merged) < 10:
            logger.warning("Datos insuficientes para correlación")
            return {}

        # Calcular correlación de Pearson
        correlation, p_value = stats.pearsonr(
            merged["avg_sentiment"], merged["Daily_Change"]
        )

        # Calcular correlación de Spearman (no paramétrica)
        spearman_corr, spearman_p = stats.spearmanr(
            merged["avg_sentiment"], merged["Daily_Change"]
        )

        # Estadísticas adicionales
        stats_dict = {
            "pearson_correlation": float(correlation),
            "pearson_p_value": float(p_value),
            "spearman_correlation": float(spearman_corr),
            "spearman_p_value": float(spearman_p),
            "sample_size": int(len(merged)),
            "avg_sentiment": float(merged["avg_sentiment"].mean()),
            "avg_colcap_change": float(merged["Daily_Change"].mean()),
            "sentiment_volatility": float(merged["avg_sentiment"].std()),
            "colcap_volatility": float(merged["Daily_Change"].std()),
        }

        logger.info(f"Correlación Pearson: {correlation:.4f} (p={p_value:.4f})")
        logger.info(f"Correlación Spearman: {spearman_corr:.4f} (p={spearman_p:.4f})")

        return stats_dict

    def save_correlations(self, news_df: pd.DataFrame, colcap_df: pd.DataFrame):
        """Guardar correlaciones diarias en la base de datos usando BATCH INSERT"""
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            # Merge de datos
            merged = pd.merge(
                news_df[["avg_sentiment", "news_count", "news_ids"]],
                colcap_df[["Daily_Change"]],
                left_index=True,
                right_index=True,
                how="inner",
            )

            # Preparar datos para batch insert
            batch_data = []

            for date, row in merged.iterrows():
                # Calcular correlación móvil de 7 días
                date_window = merged.loc[:date].tail(7)

                if len(date_window) >= 3:
                    corr, _ = stats.pearsonr(
                        date_window["avg_sentiment"], date_window["Daily_Change"]
                    )
                else:
                    corr = 0.0

                try:
                    batch_data.append(
                        (
                            date.date(),
                            int(row["news_count"]),
                            float(row["avg_sentiment"]),
                            float(row["Daily_Change"]),
                            float(corr),
                            list(row["news_ids"]),
                        )
                    )
                except Exception as e:
                    logger.error(f"Error preparando correlación para {date}: {str(e)}")
                    continue

            if not batch_data:
                return

            # BATCH UPSERT usando execute_values
            execute_values(
                cursor,
                """
                INSERT INTO correlations
                (date, news_count, avg_sentiment, colcap_change,
                 correlation_coefficient, news_ids)
                VALUES %s
                ON CONFLICT (date) DO UPDATE SET
                    news_count = EXCLUDED.news_count,
                    avg_sentiment = EXCLUDED.avg_sentiment,
                    colcap_change = EXCLUDED.colcap_change,
                    correlation_coefficient = EXCLUDED.correlation_coefficient
                """,
                batch_data,
                template="(%s, %s, %s, %s, %s, %s)",
                page_size=100,
            )

            conn.commit()
            logger.info(f"✅ BATCH guardadas {len(batch_data)} correlaciones")

        except Exception as e:
            conn.rollback()
            logger.error(f"Error guardando correlaciones: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def get_colcap_from_db(self, days_back: int = 90) -> pd.DataFrame:
        """Obtener datos COLCAP existentes de la base de datos"""
        logger.info(f"Obteniendo datos COLCAP de la BD (últimos {days_back} días)")

        conn = self.get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            cursor.execute(
                """
                SELECT date, open_price, high_price, low_price,
                       close_price, volume, daily_change
                FROM colcap_data
                ORDER BY date DESC
                LIMIT %s
            """,
                (days_back,),
            )

            rows = cursor.fetchall()

            if not rows:
                logger.warning("No hay datos COLCAP en la BD")
                return pd.DataFrame()

            # Convertir a DataFrame
            df = pd.DataFrame(rows)
            df["date"] = pd.to_datetime(df["date"])
            df.set_index("date", inplace=True)
            df.rename(
                columns={
                    "open_price": "Open",
                    "high_price": "High",
                    "low_price": "Low",
                    "close_price": "Close",
                    "volume": "Volume",
                    "daily_change": "Daily_Change",
                },
                inplace=True,
            )

            # Convertir tipos numéricos explícitamente
            for col in ["Open", "High", "Low", "Close", "Daily_Change"]:
                df[col] = df[col].astype(float)

            logger.info(f"✅ Cargados {len(df)} registros COLCAP desde BD")
            return df

        finally:
            cursor.close()
            conn.close()

    def run_analysis(self):
        """Ejecutar análisis completo con ThreadPoolExecutor para I/O paralelo"""
        logger.info("=" * 50)
        logger.info("Iniciando análisis de correlación (PARALELO)")
        logger.info("=" * 50)

        start_time = time.time()

        # 1. Usar ThreadPoolExecutor para operaciones I/O en paralelo
        # Fetch COLCAP y News sentiment simultáneamente
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Lanzar tareas I/O en paralelo
            future_colcap = executor.submit(self.fetch_colcap_data, 365)
            future_news = executor.submit(self.get_daily_news_sentiment, 365)
            future_colcap_db = executor.submit(self.get_colcap_from_db, 365)

            # Recoger resultados
            colcap_df = future_colcap.result()
            news_df = future_news.result()
            colcap_db_df = future_colcap_db.result()

        logger.info(f"⚡ Fetch paralelo completado en {time.time() - start_time:.2f}s")

        # Usar datos de Yahoo Finance, o BD como fallback
        if colcap_df.empty:
            logger.warning("No se pudo descargar de Yahoo Finance, usando datos de BD")
            colcap_df = colcap_db_df

            if colcap_df.empty:
                logger.error("No hay datos del COLCAP (ni en Yahoo ni en BD)")
                return
        else:
            # Guardar datos nuevos de Yahoo Finance
            self.save_colcap_data(colcap_df)

        # 2. Verificar datos de noticias
        if news_df.empty:
            logger.warning("No hay datos de noticias para analizar")
            return

        logger.info(
            f"Datos para análisis: {len(news_df)} días de noticias, {len(colcap_df)} días COLCAP"
        )

        # 3. Calcular correlación y guardar en paralelo
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_corr = executor.submit(
                self.calculate_correlation, news_df, colcap_df
            )
            future_save = executor.submit(self.save_correlations, news_df, colcap_df)

            correlation_stats = future_corr.result()
            future_save.result()  # Esperar que termine

        if correlation_stats:
            # Guardar en Redis para la API
            self.redis_client.setex(
                "latest_correlation_stats",
                86400,  # 24 horas
                json.dumps(correlation_stats),
            )
            logger.info("✅ Estadísticas de correlación guardadas en Redis")

        elapsed = time.time() - start_time
        logger.info(f"✅ Análisis completado exitosamente en {elapsed:.2f}s (PARALELO)")
        logger.info("=" * 50)

    def run(self):
        """Ejecutar servicio"""
        logger.info("🚀 Iniciando COLCAP Analyzer Service")

        # Ejecutar análisis al iniciar
        self.run_analysis()

        # Ejecutar análisis cada 12 horas
        while True:
            try:
                time.sleep(43200)  # 12 horas
                self.run_analysis()

            except KeyboardInterrupt:
                logger.info("Deteniendo analizador...")
                break
            except Exception as e:
                logger.error(f"Error en loop principal: {str(e)}")
                time.sleep(3600)  # Esperar 1 hora en caso de error


if __name__ == "__main__":
    analyzer = COLCAPAnalyzer()
    analyzer.run()
