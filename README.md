# News-COLCAP Correlation System

Sistema distribuido para analizar correlaciones entre noticias y el índice bursátil COLCAP utilizando tecnologías de contenedores y Kubernetes.

## Estructura del Proyecto

```
├── services/
│   ├── collector/          # Servicio recolector GDELT
│   ├── processor/          # Servicio ETL
│   ├── analyzer/           # Servicio análisis
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
├── docker-compose.yml      # Para desarrollo local
└── README.md
```

## Instalación y Uso

### Prerrequisitos
- **Docker Desktop**
- **Minikube**
- **kubectl**

---

## Ejecución

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
