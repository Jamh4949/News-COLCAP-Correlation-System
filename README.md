# 📊 News-COLCAP Correlation System

Sistema distribuido para analizar correlaciones entre noticias y el índice bursátil COLCAP utilizando tecnologías de contenedores y Kubernetes.

## 🎯 Objetivos del Proyecto

- Procesamiento distribuido de noticias en tiempo real usando GDELT
- Análisis de correlación con indicadores económicos (COLCAP)
- Despliegue en Kubernetes (EKS/k3s)
- Arquitectura de microservicios escalable
- **Paralelización real** con ProcessPoolExecutor y ThreadPoolExecutor

## ⚡ Características de Paralelización y Distribución

### Procesamiento Paralelo
| Servicio | Técnica | Beneficio |
|----------|---------|-----------|
| **Collector** | Batch Inserts (execute_values) | 10x más rápido en BD |
| **Processor** | ThreadPoolExecutor + Bloqueo Distribuido | Procesamiento multi-thread sin duplicados |
| **Analyzer** | ThreadPoolExecutor | I/O paralelo (Yahoo Finance + BD) |
| **API** | Métricas Prometheus | Observabilidad en tiempo real |

### Kubernetes Distribuido
- **HorizontalPodAutoscaler**: Escala pods automáticamente por CPU/memoria
- **PodDisruptionBudget**: Alta disponibilidad garantizada
- **Jobs Paralelos**: Procesamiento batch con `parallelism` y `completions`
- **CronJobs**: Tareas programadas distribuidas

## 🏗️ Arquitectura

```
┌──────────────────────────────────────────────────────────────────┐
│    Kubernetes Cluster (EKS/k3s)                                   │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────┐   ┌───────────────────┐   ┌─────────────────┐ │
│  │  GDELT       │   │  Processing       │   │  Analysis       │ │
│  │  Collector   │──▶│  Service (x3)     │──▶│  Service        │ │
│  │  Batch Insert│   │  ProcessPool      │   │  ThreadPool     │ │
│  └──────────────┘   │  FOR UPDATE SKIP  │   │  Parallel I/O   │ │
│         │           │  LOCKED           │   └─────────────────┘ │
│         │           └───────────────────┘           │            │
│         └──────────┬────────────────────────────────┘            │
│                    ▼                                              │
│         ┌──────────────────────┐    ┌─────────────────────────┐ │
│         │  Redis (Cache/Queue) │    │  Prometheus (Metrics)   │ │
│         └──────────────────────┘    └─────────────────────────┘ │
│                    │                          ▲                   │
│         ┌──────────┴──────────┐               │                  │
│         ▼                     ▼               │                  │
│  ┌─────────────┐      ┌───────────────┐      │                  │
│  │ PostgreSQL  │      │  FastAPI +    │──────┘                  │
│  │ (Container) │      │  Dashboard    │  /metrics               │
│  └─────────────┘      │  HPA (x2-5)   │                         │
│                       └───────────────┘                          │
└──────────────────────────────────────────────────────────────────┘
```

## 📁 Estructura del Proyecto

```
├── services/
│   ├── collector/          # Servicio recolector GDELT (Batch Insert)
│   ├── processor/          # Servicio ETL (ProcessPoolExecutor)
│   ├── analyzer/           # Servicio análisis (ThreadPoolExecutor)
│   └── api/                # API REST + Dashboard + Prometheus
├── k8s/                    # Manifiestos de Kubernetes
│   ├── 07-processor.yaml   # HPA, PDB, 3 réplicas
│   ├── 08-analyzer.yaml    # CronJob para análisis
│   ├── 09-api.yaml         # HPA, PDB, métricas
│   ├── 10-batch-processing-job.yaml  # Jobs paralelos
│   └── 11-prometheus.yaml  # Observabilidad
├── database/               # Scripts de base de datos
├── scripts/                # Scripts de despliegue
├── data/                   # Datos de referencia COLCAP
├── docker-compose.yml      # Para desarrollo local (USAR ESTO)
└── README.md
```

## 🚀 Stack Tecnológico

- **Cloud**: AWS (EKS) / Oracle Cloud (k3s)
- **Orquestación**: Kubernetes con HPA y PDB
- **Lenguaje**: Python 3.11
- **Paralelización**: ProcessPoolExecutor, ThreadPoolExecutor
- **Web Framework**: FastAPI
- **Base de datos**: PostgreSQL 15 (Batch Operations)
- **Cache/Queue**: Redis 7
- **Observabilidad**: Prometheus + endpoint /metrics
- **Fuente de datos**: GDELT Project + Yahoo Finance

## 📦 Instalación y Uso

### Prerrequisitos
- Docker y Docker Compose
- kubectl (para Kubernetes)

### 🚀 Ejecución Local con Docker (PARA COMPAÑEROS)

```powershell
# 1. Clonar el repositorio
git clone <repo-url>
cd news-colcap

# 2. Construir las imágenes Docker
docker-compose build

# 3. Levantar TODOS los servicios con 3 processors paralelos
docker-compose up -d --scale processor=3

# 4. Ver los logs de los processors en paralelo
docker-compose logs -f processor

# 5. Acceder al Dashboard
start http://localhost:8000

# 6. Ver métricas Prometheus
start http://localhost:8000/metrics
```

### ⏹️ Detener el Sistema
```powershell
docker-compose down
```

### 📊 Verificar Paralelización
```powershell
# Ver las 3 instancias del processor corriendo
docker-compose ps

# Ver logs de procesamiento paralelo en tiempo real
docker-compose logs -f processor

# Deberías ver logs de processor-1, processor-2, processor-3
# procesando artículos simultáneamente
```

### Despliegue en Kubernetes

```bash
# 1. Aplicar manifiestos
kubectl apply -f k8s/

# 2. Verificar pods escalados
kubectl get pods -n news-colcap

# 3. Ver HPA en acción
kubectl get hpa -n news-colcap

# 4. Ejecutar Job de procesamiento paralelo
kubectl apply -f k8s/10-batch-processing-job.yaml

# 5. Ver métricas
kubectl port-forward svc/api-service 8000:8000 -n news-colcap
curl http://localhost:8000/metrics
```

## 📊 Servicios

### 1. Collector Service
- Recolecta noticias de GDELT cada 6 horas
- **BATCH INSERT**: Inserta 500 registros por operación
- Filtra noticias relacionadas con Colombia

### 2. Processor Service (Paralelo)
- **ThreadPoolExecutor**: Análisis de sentimiento multi-thread (32+ threads)
- **FOR UPDATE SKIP LOCKED**: Bloqueo distribuido para pods múltiples
- **BATCH UPDATE**: Actualiza 100 registros por operación
- Escala automáticamente de 2 a 6 pods (HPA)

### 3. Analyzer Service (Paralelo)
- **ThreadPoolExecutor**: Fetch paralelo Yahoo Finance + BD
- Calcula correlaciones Pearson/Spearman
- CronJob para análisis programado cada 6 horas

### 4. API & Dashboard
- Endpoints REST para consultas
- **Endpoint /metrics**: Formato Prometheus
- Visualización de correlaciones
- Escala automáticamente de 2 a 5 pods (HPA)

## 📈 Métricas y Observabilidad

### Endpoint Prometheus `/metrics`
```
news_colcap_news_total          # Total de noticias recolectadas
news_colcap_news_processed      # Noticias con análisis de sentimiento
news_colcap_news_pending        # Noticias pendientes de procesar
news_colcap_sentiment_positive  # Noticias positivas
news_colcap_sentiment_negative  # Noticias negativas
news_colcap_sentiment_average   # Sentimiento promedio
news_colcap_colcap_price        # Precio COLCAP actual
news_colcap_redis_up            # Estado de Redis
```

### Prueba de Rendimiento
```powershell
# Ejecutar prueba de procesamiento paralelo
python test_parallel_processing.py

# Resultado esperado:
# - 50 artículos procesados
# - Tiempo: ~5-10 segundos
# - Velocidad: 5-10 artículos/segundo
```

## 🔧 Escalabilidad Kubernetes

### Escalar Manualmente
```bash
# Escalar processors a 5 réplicas
kubectl scale deployment processor --replicas=5 -n news-colcap

# Ver autoescalado
kubectl get hpa -n news-colcap -w
```

### Ejecutar Job Paralelo
```bash
# Job con 5 completions y 3 en paralelo
kubectl apply -f k8s/10-batch-processing-job.yaml

# Ver progreso
kubectl get jobs -n news-colcap
kubectl logs -f job/news-batch-processor -n news-colcap
```

### Tolerancia a Fallos
```bash
# Matar un pod y ver recuperación
kubectl delete pod processor-xxxxx -n news-colcap

# El HPA y el Deployment recrean el pod automáticamente
kubectl get pods -n news-colcap -w
```

## 👥 Equipo

- Jose Armando Martínez Hernández - 2325365

## 📄 License

This project is **dual-licensed**:

- **Non-commercial use** is allowed with attribution.
- **Commercial use** requires a separate license and may be subject to fees or royalties.

See the [LICENSE](./LICENSE) file for details.
