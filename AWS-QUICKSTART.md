# 🚀 Guía Rápida AWS - News-COLCAP Project

## ⚡ Despliegue en AWS EKS (30 minutos)

### ✅ Prerequisitos

Antes de empezar, asegúrate de tener:
- [ ] Cuenta AWS con $200 crédito activado
- [ ] AWS CLI instalado (`aws --version`)
- [ ] kubectl instalado (`kubectl version`)
- [ ] eksctl instalado (`eksctl version`)
- [ ] Docker Desktop corriendo
- [ ] Git Bash o PowerShell

---

## 📋 Paso a Paso

### 1️⃣ Configurar AWS CLI (2 min)

```powershell
# Configurar credenciales
aws configure

# Ingresar:
# AWS Access Key ID: <tu-access-key>
# AWS Secret Access Key: <tu-secret-key>
# Default region: us-east-1
# Default output format: json

# Verificar
aws sts get-caller-identity
```

### 2️⃣ Crear Cluster EKS (20 min)

```powershell
# Opción A: Script automático (RECOMENDADO)
.\scripts\create-eks-cluster.ps1

# Opción B: Manual
eksctl create cluster \
  --name news-colcap-cluster \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 2 \
  --nodes-min 2 \
  --nodes-max 4 \
  --managed
```

**☕ Toma un café - esto tarda ~15-20 minutos**

### 3️⃣ Crear Repositorios ECR (1 min)

```powershell
.\scripts\create-ecr-repos.ps1
```

### 4️⃣ Construir y Subir Imágenes (5 min)

```powershell
.\scripts\build-and-push-ecr.ps1
```

### 5️⃣ Actualizar Manifiestos K8s (2 min)

```powershell
# Obtener tu Account ID
$ACCOUNT_ID = (aws sts get-caller-identity --query Account --output text)

# Actualizar en cada archivo k8s\06-collector.yaml, 07-processor.yaml, 08-analyzer.yaml, 09-api.yaml
# Cambiar:
image: newscolcap/collector:latest

# Por:
image: <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/news-colcap/collector:latest
```

### 6️⃣ Desplegar Aplicación (3 min)

```powershell
.\scripts\deploy-eks.ps1
```

### 7️⃣ Acceder al Dashboard

```bash
# Obtener URL del Load Balancer
kubectl get service api-service -n news-colcap

# Esperar a que aparezca EXTERNAL-IP (2-3 minutos)
# Acceder en navegador: http://<EXTERNAL-IP>:8000
```

---

## 💰 Gestión de Costos

### Costo Estimado por Día

| Recurso | Costo/día |
|---------|-----------|
| EKS Control Plane | $2.50 |
| EC2 (2x t3.medium) | $2.00 |
| Load Balancer | $0.60 |
| EBS + Transfer | $0.50 |
| **TOTAL** | **~$5.60/día** |

**Con $200 crédito = ~35 días** ✅

### Optimizaciones

**1. Usar Spot Instances (Ahorra 70%)**
```bash
eksctl create nodegroup \
  --cluster=news-colcap-cluster \
  --name=spot-workers \
  --spot \
  --instance-types=t3.medium \
  --nodes-min=2 \
  --nodes-max=4
```

**2. Detener cuando no uses**
```bash
# Detener (elimina nodos, mantiene configuración)
eksctl scale nodegroup --cluster=news-colcap-cluster --name=standard-workers --nodes=0

# Reactivar
eksctl scale nodegroup --cluster=news-colcap-cluster --name=standard-workers --nodes=2
```

**3. Eliminar completamente**
```bash
.\scripts\cleanup-aws.ps1
```

---

## 🔍 Monitoreo y Debug

### Ver estado
```bash
# Pods
kubectl get pods -n news-colcap

# HPA (auto-scaling)
kubectl get hpa -n news-colcap

# Uso de recursos
kubectl top nodes
kubectl top pods -n news-colcap
```

### Ver logs
```bash
# Logs en tiempo real
kubectl logs -f deployment/collector -n news-colcap
kubectl logs -f deployment/processor -n news-colcap
kubectl logs -f deployment/analyzer -n news-colcap
kubectl logs -f deployment/api -n news-colcap
```

### Problemas comunes

**1. Pods en Pending**
```bash
# Ver por qué
kubectl describe pod <pod-name> -n news-colcap

# Solución: Escalar nodos
eksctl scale nodegroup --cluster=news-colcap-cluster --nodes=3
```

**2. Load Balancer sin IP**
```bash
# Esperar 2-3 minutos más
kubectl get service api-service -n news-colcap --watch
```

**3. Imágenes no se descargan**
```bash
# Verificar que pusheaste a ECR
aws ecr describe-images --repository-name news-colcap/collector --region us-east-1
```

---

## 🧹 Limpieza Total

```powershell
# Script automatizado
.\scripts\cleanup-aws.ps1

# O manual:
kubectl delete namespace news-colcap
eksctl delete cluster --name news-colcap-cluster
aws ecr delete-repository --repository-name news-colcap/collector --force
aws ecr delete-repository --repository-name news-colcap/processor --force
aws ecr delete-repository --repository-name news-colcap/analyzer --force
aws ecr delete-repository --repository-name news-colcap/api --force
```

---

## 🎯 Checklist de Deployment

- [ ] AWS CLI configurado
- [ ] Cluster EKS creado
- [ ] Repositorios ECR creados
- [ ] Imágenes construidas y pusheadas
- [ ] Manifiestos actualizados con URIs de ECR
- [ ] Aplicación desplegada
- [ ] Load Balancer tiene IP
- [ ] Dashboard accesible
- [ ] Datos recolectándose

---

## 🎥 Para el Video

**Demostrar:**

1. ✅ Cluster EKS corriendo: `kubectl get nodes`
2. ✅ Pods distribuidos: `kubectl get pods -n news-colcap -o wide`
3. ✅ HPA funcionando: `kubectl get hpa -n news-colcap`
4. ✅ Dashboard web funcionando
5. ✅ Noticias recolectándose en tiempo real
6. ✅ Correlaciones con COLCAP
7. ✅ Escalabilidad automática

---

## 📊 Métricas de AWS

```bash
# Ver consumo de recursos
aws cloudwatch get-metric-statistics \
  --namespace AWS/EKS \
  --metric-name cluster_failed_node_count \
  --dimensions Name=ClusterName,Value=news-colcap-cluster \
  --start-time 2025-12-20T00:00:00Z \
  --end-time 2025-12-21T00:00:00Z \
  --period 3600 \
  --statistics Average
```

---

## 🆘 Soporte

**Documentación oficial:**
- [AWS EKS](https://docs.aws.amazon.com/eks/)
- [eksctl](https://eksctl.io/)
- [AWS ECR](https://docs.aws.amazon.com/ecr/)

**Comunidad:**
- [AWS Forums](https://forums.aws.amazon.com/)
- [Kubernetes Slack](https://kubernetes.slack.com/)

---

## ✨ Ventajas de AWS vs Otras Opciones

✅ **Servicio gestionado** - AWS gestiona el control plane de K8s
✅ **Integración nativa** - ECR, CloudWatch, IAM, VPC
✅ **Auto-scaling robusto** - Cluster Autoscaler nativo
✅ **Load Balancer enterprise** - Application Load Balancer incluido
✅ **Monitoreo incluido** - CloudWatch Logs and Metrics
✅ **$200 de crédito** - Suficiente para más de un mes

---

**¡Listo para empezar! 🚀**

Ejecuta: `.\scripts\create-eks-cluster.ps1`
