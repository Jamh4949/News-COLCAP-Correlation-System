# 🚀 Quick Start Guide

## ⚡ Inicio Rápido (5 minutos)

### 🚀 Opción 1: Script Automático (RECOMENDADO)
```powershell
# Ejecuta TODO el pipeline automáticamente
.\ejecutar_noticias_docker.ps1

# El script:
# ✓ Verifica Docker
# ✓ Genera datos COLCAP
# ✓ Construye imágenes
# ✓ Levanta servicios
# ✓ Importa datos
# ✓ Abre el dashboard
# ✓ Muestra logs en tiempo real
```

### 🔧 Opción 2: Manual

#### 1️⃣ Verificar Prerequisitos
```powershell
# Verificar Docker
docker --version

# Verificar Docker Compose
docker-compose --version
```

##### 2️⃣ Levantar Servicios
```powershell
# Desde la raíz del proyecto
docker-compose up -d
```

#### 3️⃣ Verificar Estado
```powershell
# Ver que todos los contenedores están corriendo
docker-compose ps

# Debería mostrar 6 contenedores: postgres, redis, collector, processor, analyzer, api
```

#### 4️⃣ Acceder al Dashboard
Abre tu navegador en: **http://localhost:8000**

#### 5️⃣ Ver Logs (Opcional)
```powershell
# Todos los servicios
docker-compose logs -f

# Solo un servicio específico
docker-compose logs -f collector
```

---

## 🤖 Scripts Maestros

El proyecto incluye scripts maestros que automatizan todo el pipeline:

### 🐳 Docker (Recomendado)
```powershell
# Pipeline completo
.\ejecutar_noticias_docker.ps1

# Con limpieza previa
.\ejecutar_noticias_docker.ps1 -Clean

# Saltar construcción (usar imágenes existentes)
.\ejecutar_noticias_docker.ps1 -SkipBuild

# Sin abrir navegador ni logs
.\ejecutar_noticias_docker.ps1 -NoBrowser -NoLogs
```

### 🐍 Python Local (Sin Docker)
```powershell
# Requiere PostgreSQL y Redis locales
python ejecutar_noticias_local.py

# Saltar pasos opcionales
python ejecutar_noticias_local.py --skip-nltk --skip-dashboard
```

---

## 🎯 ¿Qué Hace Cada Servicio?

| Servicio | Puerto | Función |
|----------|--------|---------|
| **postgres** | 5432 | Base de datos principal |
| **redis** | 6379 | Cache y cola de mensajes |
| **collector** | - | Recolecta noticias de GDELT cada 6h |
| **processor** | - | Analiza sentimiento de noticias |
| **analyzer** | - | Correlaciona con índice COLCAP |
| **api** | 8000 | API REST + Dashboard web |

---

## 📊 Endpoints Útiles

Una vez levantado, puedes acceder a:

- **Dashboard**: http://localhost:8000
- **Health Check**: http://localhost:8000/api/health
- **Estadísticas**: http://localhost:8000/api/stats
- **Documentación API**: http://localhost:8000/docs
- **Noticias Recientes**: http://localhost:8000/api/news/recent
- **Datos COLCAP**: http://localhost:8000/api/colcap/latest
- **Correlaciones**: http://localhost:8000/api/correlations

---

## 🛠️ Comandos Comunes

### Detener todo
```powershell
docker-compose down
```

### Reiniciar todo (con rebuild)
```powershell
docker-compose down
docker-compose up -d --build
```

### Ver uso de recursos
```powershell
docker stats
```

### Conectarse a la base de datos
```powershell
docker-compose exec postgres psql -U newsuser -d news_colcap
```

### Conectarse a Redis
```powershell
docker-compose exec redis redis-cli
```

### Limpiar todo (incluyendo volúmenes)
```powershell
docker-compose down -v
```

---

## 🐛 Troubleshooting Rápido

### ❌ Error: "port is already allocated"
```powershell
# Cambiar puertos en docker-compose.yml o detener el proceso que usa el puerto
netstat -ano | findstr :8000
```

### ❌ Error: "no such image"
```powershell
# Construir imágenes primero
docker-compose build
docker-compose up -d
```

### ❌ Servicio no arranca
```powershell
# Ver logs detallados
docker-compose logs <nombre-servicio>

# Ejemplos:
docker-compose logs collector
docker-compose logs postgres
```

### ❌ Base de datos vacía
```powershell
# Espera ~10 minutos para que el collector recolecte las primeras noticias
# O verifica logs:
docker-compose logs -f collector
```

---

## ✅ Verificación de Funcionamiento

### 1. Verificar que hay datos
```powershell
# Conectarse a PostgreSQL
docker-compose exec postgres psql -U newsuser -d news_colcap -c "SELECT COUNT(*) FROM news;"
```

### 2. Verificar procesamiento
```powershell
# Ver noticias procesadas
docker-compose exec postgres psql -U newsuser -d news_colcap -c "SELECT COUNT(*) FROM news WHERE sentiment_score IS NOT NULL;"
```

### 3. Verificar API
```powershell
# Llamar endpoint de stats
curl http://localhost:8000/api/stats
```

---

## 📖 Próximos Pasos

1. ✅ Servicios corriendo localmente
2. 📚 Leer [AWS-QUICKSTART.md](AWS-QUICKSTART.md) para deployment en AWS EKS
3. 🔍 Explorar [local-scripts/](local-scripts/) para desarrollo sin Docker
4. 🎥 Planear video de demostración

---

## 💡 Tips

- **Primera ejecución**: El collector tarda ~6 horas en ejecutarse la primera vez (configurable)
- **Datos de prueba**: Puedes forzar una recolección reiniciando el collector
- **Dashboard**: Se actualiza automáticamente cada 5 minutos
- **Desarrollo**: Modifica el código y reconstruye con `docker-compose up -d --build`

---

## 🆘 Ayuda

Si algo no funciona:

1. Verifica logs: `docker-compose logs -f`
2. Verifica estado: `docker-compose ps`
3. Reinicia todo: `docker-compose restart`
4. En último caso: `docker-compose down -v && docker-compose up -d --build`

---

**¡Listo! Tu sistema de correlación News-COLCAP está corriendo. 🎉**
