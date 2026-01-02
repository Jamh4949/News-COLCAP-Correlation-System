# News-COLCAP Correlation System

Sistema distribuido para analizar correlaciones entre noticias y el índice bursátil COLCAP utilizando tecnologías de contenedores y Kubernetes.

## Estructura del Proyecto

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

## Instalación y Uso

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

## Servicios

### 1. Collector Service
- Recolecta noticias de GDELT
- Filtra noticias relacionadas con Colombia

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
