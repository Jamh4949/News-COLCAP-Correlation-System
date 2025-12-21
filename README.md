# 📊 News-COLCAP Correlation System

Sistema distribuido para analizar correlaciones entre noticias y el índice bursátil COLCAP utilizando tecnologías de contenedores y Kubernetes.

## 🎯 Objetivos del Proyecto

- Procesamiento distribuido de noticias en tiempo real usando GDELT
- Análisis de correlación con indicadores económicos (COLCAP)
- Despliegue en Kubernetes (k3s en Oracle Cloud Always Free)
- Arquitectura de microservicios escalable

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│    AWS Cloud - EKS Kubernetes Cluster                   │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────┐   ┌──────────────┐   ┌─────────────┐ │
│  │  GDELT       │   │  Processing  │   │  Analysis   │ │
│  │  Collector   │──▶│  Service     │──▶│  Service    │ │
│  │  (Python)    │   │  (ETL)       │   │(Correlation)│ │
│  └──────────────┘   └──────────────┘   └─────────────┘ │
│         │                   │                   │        │
│         └──────────┬────────┴───────────────────┘        │
│                    ▼                                      │
│         ┌──────────────────────┐                         │
│         │  Redis (Cache/Queue) │                         │
│         └──────────────────────┘                         │
│                    │                                      │
│         ┌──────────┴──────────┐                          │
│         ▼                     ▼                           │
│  ┌─────────────┐      ┌──────────────┐                  │
│  │ PostgreSQL  │      │  FastAPI +   │                  │
│  │ (Container) │      │  Dashboard   │                  │
│  └─────────────┘      └──────────────┘                  │
└─────────────────────────────────────────────────────────┘
```

## 📁 Estructura del Proyecto

```
├── services/
│   ├── collector/          # Servicio recolector de noticias GDELT
│   ├── processor/          # Servicio de procesamiento ETL
│   ├── analyzer/           # Servicio de análisis y correlación
│   └── api/                # API REST y Dashboard
├── k8s/                    # Manifiestos de Kubernetes
├── database/               # Scripts de base de datos
├── local-scripts/          # Scripts de desarrollo y pruebas
├── scripts/                # Scripts de despliegue AWS/EKS
├── data/                   # Datos generados (COLCAP, conclusiones)
├── docker-compose.yml      # Para desarrollo local
├── LICENSE                 # Licencia dual
└── README.md
```

## 🚀 Stack Tecnológico

- **Cloud**: AWS (Amazon Web Services) - $200 crédito
- **Orquestación**: EKS (Elastic Kubernetes Service)
- **Container Registry**: ECR (Elastic Container Registry)
- **Lenguaje**: Python 3.11
- **Web Framework**: FastAPI
- **Base de datos**: PostgreSQL 15
- **Cache/Queue**: Redis 7
- **Fuente de datos**: GDELT Project + Yahoo Finance
- **Containerización**: Docker

## 📦 Instalación y Uso

### Prerrequisitos
- Docker y Docker Compose
- Python 3.11+
- kubectl
- AWS CLI (para deployment en cloud)
- eksctl (para EKS)

### Desarrollo Local con Docker (Recomendado)
```powershell
# Clonar repositorio
git clone <repo-url>

# Opción 1: Script automático (RECOMENDADO)
.\ejecutar_noticias_docker.ps1

# Opción 2: Manual
docker-compose up -d

# Acceder al dashboard
http://localhost:8000
```

### Desarrollo Local sin Docker
```powershell
# Requiere PostgreSQL y Redis locales
python .\ejecutar_noticias_local.py
```

> 📖 **Ver [SCRIPTS.md](SCRIPTS.md)** para documentación completa de los scripts maestros y opciones avanzadas.

### Despliegue en AWS EKS
```bash
# 1. Crear cluster EKS
.\scripts\create-eks-cluster.ps1

# 2. Crear repositorios ECR
.\scripts\create-ecr-repos.ps1

# 3. Construir y subir imágenes
.\scripts\build-and-push-ecr.ps1

# 4. Actualizar manifiestos con URIs de ECR
# Ver AWS-QUICKSTART.md

# 5. Desplegar
.\scripts\deploy-eks.ps1

# 6. Obtener URL
kubectl get service api-service -n news-colcap
```

## 📊 Servicios

### 1. Collector Service
- Recolecta noticias de GDELT cada 6 horas
- Filtra noticias relacionadas con Colombia
- Envía a cola Redis para procesamiento

### 2. Processor Service
- Limpia y transforma datos
- Realiza análisis de sentimiento
- Clasifica por categorías
- Almacena en PostgreSQL

### 3. Analyzer Service
- Obtiene datos del COLCAP
- Calcula correlaciones temporales
- Genera insights y alertas

### 4. API & Dashboard
- Endpoints REST para consultas
- Visualización de correlaciones
- Métricas del sistema

## 👥 Equipo

- Jose Armando Martínez Hernández - 2325365

## 📄 License

This project is **dual-licensed**:

- **Non-commercial use** is allowed with attribution.
- **Commercial use** requires a separate license and may be subject to fees or royalties.

See the [LICENSE](./LICENSE) file for details.
