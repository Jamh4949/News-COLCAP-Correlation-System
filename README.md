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
- **Docker Desktop** (con Docker Compose incluido)
- **Minikube** (para Kubernetes local) - [Instalar aquí](https://minikube.sigs.k8s.io/docs/start/)
- **kubectl** - [Instalar aquí](https://kubernetes.io/docs/tasks/tools/)

---

## 🐳 OPCIÓN 1: Ejecución Local con Docker Compose (Más Fácil)

Esta opción demuestra la **paralelización** con múltiples processors.

### Paso 1: Clonar el repositorio
```powershell
git clone -b final_ver https://github.com/Jamh4949/News-COLCAP-Correlation-System.git
cd News-COLCAP-Correlation-System
```

### Paso 2: Construir las imágenes Docker
```powershell
docker-compose build
```

### Paso 3: Levantar con 3 processors paralelos
```powershell
docker-compose up -d --scale processor=3
```

### Paso 4: Verificar que todo está corriendo
```powershell
docker-compose ps
```
Deberías ver algo como:
```
NAME                    STATUS    PORTS
proyecto-api-1          running   0.0.0.0:8000->8000/tcp
proyecto-collector-1    running
proyecto-processor-1    running
proyecto-processor-2    running
proyecto-processor-3    running   <-- ¡3 processors paralelos!
proyecto-analyzer-1     running
proyecto-postgres-1     running   0.0.0.0:5432->5432/tcp
proyecto-redis-1        running   0.0.0.0:6379->6379/tcp
```

### Paso 5: Ver la paralelización en acción
```powershell
# Ver logs de los 3 processors procesando simultáneamente
docker-compose logs -f processor
```
Deberías ver logs de `processor-1`, `processor-2`, `processor-3` procesando artículos al mismo tiempo con mensajes como:
- `🔒 Obtenidos X artículos (con bloqueo distribuido)`
- `✅ Batch de X artículos procesado en X.XXs`

### Paso 6: Acceder al Dashboard y Métricas
```powershell
# Abrir Dashboard
start http://localhost:8000

# Ver métricas Prometheus
start http://localhost:8000/metrics
```

### Paso 7: Detener todo
```powershell
docker-compose down
```

---

## ☸️ OPCIÓN 2: Ejecución con Kubernetes (Minikube)

Esta opción demuestra **Kubernetes completo**: HPA, PDB, CronJobs, múltiples réplicas.

### Paso 1: Clonar el repositorio
```powershell
git clone -b final_ver https://github.com/Jamh4949/News-COLCAP-Correlation-System.git
cd News-COLCAP-Correlation-System
```

### Paso 2: Iniciar Minikube
```powershell
minikube start --memory=4096 --cpus=2
```

### Paso 3: Configurar Docker para usar el de Minikube
```powershell
# Esto hace que las imágenes se construyan dentro de Minikube
minikube docker-env --shell powershell | Invoke-Expression
```

### Paso 4: Construir las imágenes
```powershell
docker build -t newscolcap/collector:latest ./services/collector
docker build -t newscolcap/processor:latest ./services/processor
docker build -t newscolcap/analyzer:latest ./services/analyzer
docker build -t newscolcap/api:latest ./services/api
```

### Paso 5: Crear el PVC con StorageClass correcto
```powershell
# El PVC necesita StorageClass "standard" en Minikube
@"
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: news-colcap
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: standard
"@ | Set-Content -Path k8s/03-postgres-pvc-minikube.yaml

# Aplicar namespace primero
kubectl apply -f k8s/00-namespace.yaml

# Aplicar PVC para minikube
kubectl apply -f k8s/03-postgres-pvc-minikube.yaml
```

### Paso 6: Desplegar todos los servicios
```powershell
kubectl apply -f k8s/01-configmap.yaml
kubectl apply -f k8s/02-secrets.yaml
kubectl apply -f k8s/04-postgres.yaml
kubectl apply -f k8s/05-redis.yaml
kubectl apply -f k8s/06-collector.yaml
kubectl apply -f k8s/07-processor.yaml
kubectl apply -f k8s/08-analyzer.yaml
kubectl apply -f k8s/09-api.yaml
```

### Paso 7: Verificar que todo está corriendo
```powershell
kubectl get pods -n news-colcap
```
Deberías ver:
```
NAME                         READY   STATUS    
analyzer-xxx                 1/1     Running
api-xxx                      1/1     Running
api-yyy                      1/1     Running   <-- 2 réplicas (HPA)
collector-xxx                1/1     Running
postgres-xxx                 1/1     Running
processor-xxx                1/1     Running
processor-yyy                1/1     Running
processor-zzz                1/1     Running   <-- 3 réplicas paralelas
redis-xxx                    1/1     Running
```

### Paso 8: Ver HPA y PDB
```powershell
# HorizontalPodAutoscaler - escala automáticamente
kubectl get hpa -n news-colcap

# PodDisruptionBudget - alta disponibilidad
kubectl get pdb -n news-colcap
```

### Paso 9: Ver logs de processors paralelos
```powershell
kubectl logs -n news-colcap -l app=processor --tail=20
```

### Paso 10: Acceder al Dashboard
```powershell
# En una terminal separada, mantener corriendo:
kubectl port-forward svc/api-service 8080:8000 -n news-colcap

# Luego abrir en el navegador:
start http://localhost:8080
start http://localhost:8080/metrics
```

### Paso 11: Detener Minikube
```powershell
minikube stop

# O eliminar completamente:
minikube delete
```

---

## 📊 Verificación de Características

### ✅ Paralelización (verificar en logs)
| Característica | Dónde verlo | Qué buscar |
|---------------|-------------|------------|
| **3 Processors paralelos** | `docker-compose ps` o `kubectl get pods` | 3 instancias de processor |
| **ThreadPoolExecutor** | Logs del processor | `ThreadPoolExecutor con X workers` |
| **Bloqueo distribuido** | Logs del processor | `🔒 Obtenidos X artículos (con bloqueo distribuido)` |
| **Batch Inserts** | Logs del collector | `✅ Batch de X noticias guardadas` |

### ✅ Kubernetes (verificar con kubectl)
| Característica | Comando | Qué ver |
|---------------|---------|---------|
| **HPA** | `kubectl get hpa -n news-colcap` | processor-hpa, api-hpa |
| **PDB** | `kubectl get pdb -n news-colcap` | processor-pdb, api-pdb |
| **CronJob** | `kubectl get cronjob -n news-colcap` | analyzer-cron |
| **Múltiples réplicas** | `kubectl get pods -n news-colcap` | 3 processors, 2 APIs |

---

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

---

## 📈 Métricas Prometheus

Accede a `http://localhost:8000/metrics` (Docker) o `http://localhost:8080/metrics` (K8s) para ver:
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

---

## 🔧 Comandos Útiles

### Docker Compose
```powershell
docker-compose ps              # Ver servicios
docker-compose logs -f         # Ver todos los logs
docker-compose logs -f processor  # Solo logs de processors
docker-compose down            # Apagar todo
```

### Kubernetes
```powershell
kubectl get all -n news-colcap           # Ver todos los recursos
kubectl get pods -n news-colcap          # Ver pods
kubectl get hpa -n news-colcap           # Ver autoescalado
kubectl logs -l app=processor -n news-colcap  # Logs de processors
kubectl scale deployment processor --replicas=5 -n news-colcap  # Escalar manualmente
```

---

## 👥 Equipo

- Jose Armando Martínez Hernández - 2325365

## 📄 License

This project is **dual-licensed**:

- **Non-commercial use** is allowed with attribution.
- **Commercial use** requires a separate license and may be subject to fees or royalties.

See the [LICENSE](./LICENSE) file for details.
