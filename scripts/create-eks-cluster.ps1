# Script para crear cluster EKS en AWS

Write-Host "Creando cluster EKS en AWS..." -ForegroundColor Cyan

$CLUSTER_NAME = "news-colcap-cluster"
$REGION = "us-east-1"
$NODE_TYPE = "t3.medium"
$NODES = 2
$NODES_MIN = 2
$NODES_MAX = 4

Write-Host "`n[INFO] Configuracion del cluster:" -ForegroundColor Yellow
Write-Host "  Nombre: $CLUSTER_NAME" -ForegroundColor White
Write-Host "  Region: $REGION" -ForegroundColor White
Write-Host "  Tipo de nodo: $NODE_TYPE" -ForegroundColor White
Write-Host "  Nodos: $NODES (min: $NODES_MIN, max: $NODES_MAX)" -ForegroundColor White

Write-Host "`n[WARN] Esto tomara aproximadamente 15-20 minutos..." -ForegroundColor Yellow
Write-Host "[WARN] Costo estimado: ~$167/mes (cubierto por credito de $200)" -ForegroundColor Yellow

$confirmation = Read-Host "`nContinuar? (s/n)"
if ($confirmation -ne 's') {
    Write-Host "[INFO] Cancelado por el usuario" -ForegroundColor Gray
    exit 0
}

Write-Host "`n[1/3] Creando cluster EKS..." -ForegroundColor Yellow

eksctl create cluster `
  --name $CLUSTER_NAME `
  --region $REGION `
  --nodegroup-name standard-workers `
  --node-type $NODE_TYPE `
  --nodes $NODES `
  --nodes-min $NODES_MIN `
  --nodes-max $NODES_MAX `
  --managed

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Fallo la creacion del cluster" -ForegroundColor Red
    exit 1
}

Write-Host "`n[2/3] Configurando kubectl..." -ForegroundColor Yellow
aws eks update-kubeconfig --region $REGION --name $CLUSTER_NAME

Write-Host "`n[3/3] Verificando cluster..." -ForegroundColor Yellow
kubectl get nodes

Write-Host "`n[OK] Cluster EKS creado exitosamente!" -ForegroundColor Green
Write-Host "`nProximos pasos:" -ForegroundColor Cyan
Write-Host "  1. Crear repositorios ECR: .\scripts\create-ecr-repos.ps1" -ForegroundColor White
Write-Host "  2. Construir y subir imagenes: .\scripts\build-and-push-ecr.ps1" -ForegroundColor White
Write-Host "  3. Desplegar aplicacion: .\scripts\deploy-eks.ps1" -ForegroundColor White
