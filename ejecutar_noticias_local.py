#!/usr/bin/env python3
"""
Script maestro para ejecutar el pipeline completo de noticias en modo local (sin Docker).

Este script ejecuta secuencialmente:
1. Setup de NLTK (si es necesario)
2. Descarga de datos COLCAP
3. Collector - Recolección de noticias
4. Processor - Análisis de sentimiento
5. Analyzer - Cálculo de correlaciones
6. Generación de conclusiones
7. Dashboard API

Requisitos previos:
- PostgreSQL corriendo localmente (localhost:5432)
- Redis corriendo localmente (localhost:6379)
- Base de datos 'news_colcap' creada
- Usuario 'newsuser' con contraseña 'newspass123'

Uso:
    python ejecutar_noticias_local.py
    
    # O con argumentos opcionales:
    python ejecutar_noticias_local.py --skip-nltk --skip-colcap --skip-dashboard
"""

import sys
import os
import subprocess
import time
import argparse
from pathlib import Path

# Colores para output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_step(step_num, step_name):
    """Imprime header de paso"""
    print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKCYAN}PASO {step_num}: {step_name}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}\n")

def run_script(script_path, description):
    """Ejecuta un script Python y muestra su output"""
    print(f"{Colors.OKBLUE}► Ejecutando: {description}{Colors.ENDC}")
    print(f"  Script: {script_path}\n")
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            check=True,
            capture_output=False,
            text=True
        )
        print(f"\n{Colors.OKGREEN}✓ {description} completado exitosamente{Colors.ENDC}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n{Colors.FAIL}✗ Error en {description}{Colors.ENDC}")
        print(f"{Colors.FAIL}Código de salida: {e.returncode}{Colors.ENDC}")
        return False
    except FileNotFoundError:
        print(f"\n{Colors.FAIL}✗ Script no encontrado: {script_path}{Colors.ENDC}")
        return False

def check_prerequisites():
    """Verifica que PostgreSQL y Redis estén disponibles"""
    print_step(0, "VERIFICACIÓN DE PREREQUISITOS")
    
    # Verificar PostgreSQL
    print(f"{Colors.OKBLUE}Verificando PostgreSQL...{Colors.ENDC}")
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="news_colcap",
            user="newsuser",
            password="newspass123"
        )
        conn.close()
        print(f"{Colors.OKGREEN}✓ PostgreSQL disponible{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.FAIL}✗ PostgreSQL no disponible: {e}{Colors.ENDC}")
        print(f"{Colors.WARNING}Asegúrate de tener PostgreSQL corriendo en localhost:5432{Colors.ENDC}")
        return False
    
    # Verificar Redis
    print(f"\n{Colors.OKBLUE}Verificando Redis...{Colors.ENDC}")
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print(f"{Colors.OKGREEN}✓ Redis disponible{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.FAIL}✗ Redis no disponible: {e}{Colors.ENDC}")
        print(f"{Colors.WARNING}Asegúrate de tener Redis corriendo en localhost:6379{Colors.ENDC}")
        return False
    
    print(f"\n{Colors.OKGREEN}✓ Todos los prerequisitos están listos{Colors.ENDC}")
    return True

def main():
    parser = argparse.ArgumentParser(description='Ejecutar pipeline completo de noticias en local')
    parser.add_argument('--skip-nltk', action='store_true', help='Saltar configuración de NLTK')
    parser.add_argument('--skip-colcap', action='store_true', help='Saltar descarga de datos COLCAP')
    parser.add_argument('--skip-dashboard', action='store_true', help='No levantar dashboard al final')
    parser.add_argument('--skip-prerequisites', action='store_true', help='Saltar verificación de prerequisitos')
    
    args = parser.parse_args()
    
    # Rutas de scripts
    project_root = Path(__file__).parent
    local_scripts = project_root / "local-scripts"
    
    scripts = {
        'setup_nltk': local_scripts / "setup_nltk.py",
        'get_colcap': local_scripts / "get_colcap.py",
        'collector': local_scripts / "1_run_collector.py",
        'processor': local_scripts / "2_run_processor.py",
        'analyzer': local_scripts / "3_run_analyzer.py",
        'conclusiones': local_scripts / "generar_conclusiones.py",
        'dashboard': local_scripts / "4_run_dashboard.py"
    }
    
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║   PIPELINE COMPLETO DE NOTICIAS - MODO LOCAL (Sin Docker) ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}")
    
    start_time = time.time()
    
    # Verificar prerequisitos
    if not args.skip_prerequisites:
        if not check_prerequisites():
            print(f"\n{Colors.FAIL}Pipeline abortado. Corrige los prerequisitos primero.{Colors.ENDC}")
            return 1
    
    # PASO 1: Setup NLTK
    if not args.skip_nltk:
        print_step(1, "CONFIGURACIÓN DE NLTK")
        if not run_script(scripts['setup_nltk'], "Setup de recursos NLTK"):
            print(f"{Colors.WARNING}Continuando de todas formas...{Colors.ENDC}")
    
    # PASO 2: Descargar COLCAP
    if not args.skip_colcap:
        print_step(2, "DESCARGA DE DATOS COLCAP")
        if not run_script(scripts['get_colcap'], "Descarga de datos COLCAP desde Yahoo Finance"):
            print(f"{Colors.FAIL}Error crítico. Abortando pipeline.{Colors.ENDC}")
            return 1
    
    # PASO 3: Collector
    print_step(3, "RECOLECCIÓN DE NOTICIAS")
    if not run_script(scripts['collector'], "Recolección de noticias desde GDELT"):
        print(f"{Colors.FAIL}Error crítico. Abortando pipeline.{Colors.ENDC}")
        return 1
    
    # PASO 4: Processor
    print_step(4, "ANÁLISIS DE SENTIMIENTO")
    if not run_script(scripts['processor'], "Procesamiento y análisis de sentimiento"):
        print(f"{Colors.FAIL}Error crítico. Abortando pipeline.{Colors.ENDC}")
        return 1
    
    # PASO 5: Analyzer
    print_step(5, "CÁLCULO DE CORRELACIONES")
    if not run_script(scripts['analyzer'], "Análisis de correlación con COLCAP"):
        print(f"{Colors.FAIL}Error crítico. Abortando pipeline.{Colors.ENDC}")
        return 1
    
    # PASO 6: Conclusiones
    print_step(6, "GENERACIÓN DE CONCLUSIONES")
    if not run_script(scripts['conclusiones'], "Generación de conclusiones y análisis"):
        print(f"{Colors.WARNING}Continuando de todas formas...{Colors.ENDC}")
    
    # PASO 7: Dashboard (opcional)
    if not args.skip_dashboard:
        print_step(7, "INICIANDO DASHBOARD")
        print(f"{Colors.OKBLUE}El dashboard se abrirá en: http://localhost:8000{Colors.ENDC}")
        print(f"{Colors.WARNING}Presiona Ctrl+C para detener el dashboard{Colors.ENDC}\n")
        
        try:
            subprocess.run([sys.executable, scripts['dashboard']])
        except KeyboardInterrupt:
            print(f"\n{Colors.OKGREEN}Dashboard detenido por el usuario{Colors.ENDC}")
    
    # Resumen final
    elapsed_time = time.time() - start_time
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)
    
    print(f"\n{Colors.BOLD}{Colors.OKGREEN}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║           ✓ PIPELINE COMPLETADO EXITOSAMENTE              ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}")
    print(f"{Colors.OKGREEN}Tiempo total: {minutes}m {seconds}s{Colors.ENDC}\n")
    
    if args.skip_dashboard:
        print(f"{Colors.OKCYAN}Para ver el dashboard ejecuta:{Colors.ENDC}")
        print(f"  python {scripts['dashboard']}\n")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
