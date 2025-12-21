# Script para desplegar en Kubernetes
# Ejecutar desde la raíz del proyecto

Write-Host "☸️ Desplegando en Kubernetes..." -ForegroundColor Cyan

# Aplicar manifiestos en orden
$manifests = @(
    "k8s/00-namespace.yaml",
    "k8s/01-configmap.yaml",
    "k8s/02-secrets.yaml",
    "k8s/03-postgres-pvc.yaml",
    "k8s/04-postgres.yaml",
    "k8s/05-redis.yaml",
    "k8s/06-collector.yaml",
    "k8s/07-processor.yaml",
    "k8s/08-analyzer.yaml",
    "k8s/09-api.yaml"
)

foreach ($manifest in $manifests) {
    Write-Host "`n📋 Aplicando $manifest..." -ForegroundColor Yellow
    kubectl apply -f $manifest
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Error aplicando $manifest" -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n✅ Despliegue completado!" -ForegroundColor Green
Write-Host "`nEsperando a que los pods estén listos..." -ForegroundColor Cyan
kubectl wait --for=condition=ready pod --all -n news-colcap --timeout=300s

Write-Host "`n📊 Estado de los pods:" -ForegroundColor Cyan
kubectl get pods -n news-colcap

Write-Host "`n🌐 Servicios:" -ForegroundColor Cyan
kubectl get services -n news-colcap

Write-Host "`n🔗 Para acceder a la API:" -ForegroundColor Yellow
Write-Host "  kubectl port-forward -n news-colcap service/api-service 8000:8000" -ForegroundColor White
Write-Host "  Luego visita: http://localhost:8000" -ForegroundColor White
