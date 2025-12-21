# Scripts Locales

Esta carpeta contiene scripts auxiliares para desarrollo y pruebas locales. **No son necesarios para la ejecución normal del proyecto con Docker**.

## Scripts de Ejecución Individual (sin Docker)

- `1_run_collector.py` - Ejecuta solo el servicio collector
- `2_run_processor.py` - Ejecuta solo el servicio processor
- `3_run_analyzer.py` - Ejecuta solo el servicio analyzer
- `4_run_dashboard.py` - Ejecuta solo el dashboard/API

## Scripts de Utilidades

- `generar_conclusiones.py` - Genera análisis estadístico completo de los datos
- `get_colcap.py` - Descarga datos COLCAP desde Yahoo Finance
- `import_colcap.py` - Importa datos COLCAP a la base de datos Docker
- `import_local_data.py` - Importa datos locales a PostgreSQL
- `setup_nltk.py` - Configura las dependencias NLTK necesarias
- `test_gxg.py` - Script de prueba para GDELT API

## Scripts PowerShell

- `docker-demo.ps1` - Demostración del sistema Docker
- `fix-docker-wsl.ps1` - Solución para problemas de Docker Desktop en WSL
- `run-local-no-docker.ps1` - Ejecuta el sistema sin Docker
- `run_analyzer.ps1` - Ejecuta el analyzer en PowerShell
- `run_full_pipeline.ps1` - Ejecuta el pipeline completo

## Uso Recomendado

Para uso normal del proyecto, usa Docker Compose:
```bash
docker-compose up --build
```

Los scripts en esta carpeta son útiles para:
- Desarrollo y debugging de servicios individuales
- Pruebas sin Docker
- Operaciones de mantenimiento de datos
