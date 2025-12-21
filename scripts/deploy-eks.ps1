# Script para desplegar en EKS

Write-Host "Desplegando aplicacion en EKS..." -ForegroundColor Cyan

# Verificar que kubectl este configurado
Write-Host "`n[1/4] Verificando conexion con EKS..." -ForegroundColor Yellow
kubectl cluster-info

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] No hay conexion con cluster EKS" -ForegroundColor Red
    Write-Host "Ejecuta: aws eks update-kubeconfig --region us-east-1 --name news-colcap-cluster" -ForegroundColor Yellow
    exit 1
}

# Aplicar manifiestos
Write-Host "`n[2/4] Aplicando manifiestos de Kubernetes..." -ForegroundColor Yellow

$manifests = @(
    "k8s\00-namespace.yaml",
    "k8s\01-configmap.yaml",
    "k8s\02-secrets.yaml",
    "k8s\03-postgres-pvc.yaml",
    "k8s\04-postgres.yaml",
    "k8s\05-redis.yaml",
    "k8s\06-collector.yaml",
    "k8s\07-processor.yaml",
    "k8s\08-analyzer.yaml",
    "k8s\09-api.yaml"
)

foreach ($manifest in $manifests) {
    Write-Host "  Aplicando $manifest..." -ForegroundColor Gray
    kubectl apply -f $manifest
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Fallo al aplicar $manifest" -ForegroundColor Red
        exit 1
    }
}

# Esperar a que pods esten listos
Write-Host "`n[3/4] Esperando a que pods esten listos..." -ForegroundColor Yellow
kubectl wait --for=condition=ready pod --all -n news-colcap --timeout=600s

# Mostrar estado
Write-Host "`n[4/4] Estado del deployment:" -ForegroundColor Yellow
Write-Host "`nPods:" -ForegroundColor Cyan
kubectl get pods -n news-colcap

Write-Host "`nServicios:" -ForegroundColor Cyan
kubectl get services -n news-colcap

# Obtener URL del Load Balancer
Write-Host "`n[INFO] Obteniendo URL del Load Balancer..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

$LB_URL = (kubectl get service api-service -n news-colcap -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>$null)

if ($LB_URL) {
    Write-Host "`n[OK] Deployment completado!" -ForegroundColor Green
    Write-Host "`nDashboard disponible en:" -ForegroundColor Cyan
    Write-Host "  http://$LB_URL:8000" -ForegroundColor White
    Write-Host "`n[INFO] El Load Balancer puede tardar 2-3 minutos en estar listo" -ForegroundColor Yellow
} else {
    Write-Host "`n[WARN] Load Balancer aun no tiene IP asignada" -ForegroundColor Yellow
    Write-Host "Espera unos minutos y ejecuta:" -ForegroundColor White
    Write-Host "  kubectl get service api-service -n news-colcap" -ForegroundColor White
}

Write-Host "`nComandos utiles:" -ForegroundColor Cyan
Write-Host "  Ver logs: kubectl logs -f <pod-name> -n news-colcap" -ForegroundColor White
Write-Host "  Ver HPA: kubectl get hpa -n news-colcap" -ForegroundColor White
Write-Host "  Escalar: kubectl scale deployment processor --replicas=3 -n news-colcap" -ForegroundColor White
