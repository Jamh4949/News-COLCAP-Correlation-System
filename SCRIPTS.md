# 🚀 Scripts de Ejecución Rápida

Este directorio contiene dos scripts maestros que automatizan completamente el pipeline de noticias:

## 🐳 `ejecutar_noticias_docker.ps1` (RECOMENDADO)

Script PowerShell que ejecuta todo el pipeline con Docker.

**Requisitos:**
- Docker Desktop instalado y corriendo
- PowerShell 5.0+

**Uso básico:**
```powershell
.\ejecutar_noticias_docker.ps1
```

**Opciones avanzadas:**
```powershell
# Con limpieza previa de contenedores
.\ejecutar_noticias_docker.ps1 -Clean

# Usar imágenes existentes (no reconstruir)
.\ejecutar_noticias_docker.ps1 -SkipBuild

# Saltar generación de datos COLCAP
.\ejecutar_noticias_docker.ps1 -SkipColcap

# Sin abrir navegador automáticamente
.\ejecutar_noticias_docker.ps1 -NoBrowser

# Sin mostrar logs al final
.\ejecutar_noticias_docker.ps1 -NoLogs

# Combinando opciones
.\ejecutar_noticias_docker.ps1 -Clean -NoBrowser -NoLogs
```

**Lo que hace:**
1. ✅ Verifica que Docker esté corriendo
2. 🧹 Limpia contenedores anteriores (si se usa `-Clean`)
3. 📊 Genera datos COLCAP desde Yahoo Finance
4. 🏗️ Construye imágenes Docker
5. 🚀 Levanta todos los servicios con docker-compose
6. 📥 Importa datos COLCAP a PostgreSQL
7. ✔️ Verifica que todos los servicios estén corriendo
8. 🌐 Abre el dashboard en el navegador
9. 📜 Muestra logs en tiempo real

---

## 🐍 `ejecutar_noticias_local.py`

Script Python que ejecuta todo el pipeline sin Docker (modo desarrollo).

**Requisitos:**
- Python 3.11+
- PostgreSQL corriendo en `localhost:5432`
- Redis corriendo en `localhost:6379`
- Base de datos `news_colcap` creada
- Usuario `newsuser` con contraseña `newspass123`

**Uso básico:**
```bash
python ejecutar_noticias_local.py
```

**Opciones avanzadas:**
```bash
# Saltar configuración de NLTK
python ejecutar_noticias_local.py --skip-nltk

# Saltar descarga de datos COLCAP
python ejecutar_noticias_local.py --skip-colcap

# No levantar dashboard al final
python ejecutar_noticias_local.py --skip-dashboard

# Saltar verificación de prerequisitos
python ejecutar_noticias_local.py --skip-prerequisites

# Combinando opciones
python ejecutar_noticias_local.py --skip-nltk --skip-dashboard
```

**Lo que hace:**
1. ✅ Verifica prerequisitos (PostgreSQL, Redis)
2. 📦 Configura recursos NLTK
3. 📊 Descarga datos COLCAP
4. 📰 Ejecuta collector (recolección de noticias)
5. 🧠 Ejecuta processor (análisis de sentimiento)
6. 📈 Ejecuta analyzer (cálculo de correlaciones)
7. 📝 Genera conclusiones
8. 🌐 Levanta dashboard (opcional)

---

## 📁 Scripts Individuales

Si necesitas ejecutar servicios individuales, todos los scripts están en [`local-scripts/`](local-scripts/):

- `1_run_collector.py` - Solo recolección de noticias
- `2_run_processor.py` - Solo análisis de sentimiento
- `3_run_analyzer.py` - Solo cálculo de correlaciones
- `4_run_dashboard.py` - Solo dashboard
- `get_colcap.py` - Solo descarga de datos COLCAP
- `import_colcap.py` - Solo importación a Docker
- `generar_conclusiones.py` - Solo generación de análisis

Ver [local-scripts/README.md](local-scripts/README.md) para más detalles.

---

## 🎯 ¿Cuál usar?

| Situación | Script Recomendado |
|-----------|-------------------|
| **Primera vez / Producción** | `ejecutar_noticias_docker.ps1` |
| **Desarrollo activo** | `ejecutar_noticias_local.py` |
| **Testing rápido** | Scripts individuales en `local-scripts/` |
| **Debugging específico** | Scripts individuales en `local-scripts/` |

---

## 🔍 Verificación Post-Ejecución

Después de ejecutar cualquiera de los scripts, verifica que todo funcione:

```powershell
# Dashboard
http://localhost:8000

# API Health
curl http://localhost:8000/api/health

# Estadísticas
curl http://localhost:8000/api/stats

# Ver datos en PostgreSQL (Docker)
docker-compose exec postgres psql -U newsuser -d news_colcap -c "SELECT COUNT(*) FROM news;"
```

---

## 📞 Soporte

Si encuentras errores:

1. Revisa los logs: `docker-compose logs -f` (Docker) o output del script (local)
2. Verifica prerequisitos: Docker corriendo, PostgreSQL accesible, Redis activo
3. Consulta [QUICKSTART.md](QUICKSTART.md) para troubleshooting
