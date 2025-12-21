# Script para limpiar todos los recursos de AWS

Write-Host "Limpiando recursos de AWS..." -ForegroundColor Cyan
Write-Host "[WARN] Esto eliminara TODOS los recursos del proyecto" -ForegroundColor Yellow

$confirmation = Read-Host "`nEstas seguro? (escribe 'SI' para confirmar)"
if ($confirmation -ne 'SI') {
    Write-Host "[INFO] Cancelado" -ForegroundColor Gray
    exit 0
}

$CLUSTER_NAME = "news-colcap-cluster"
$REGION = "us-east-1"

# 1. Eliminar namespace (elimina Load Balancers automaticamente)
Write-Host "`n[1/4] Eliminando namespace de Kubernetes..." -ForegroundColor Yellow
kubectl delete namespace news-colcap 2>$null

# Esperar a que se eliminen los Load Balancers
Write-Host "  Esperando a que se eliminen Load Balancers..." -ForegroundColor Gray
Start-Sleep -Seconds 30

# 2. Eliminar cluster EKS
Write-Host "`n[2/4] Eliminando cluster EKS..." -ForegroundColor Yellow
Write-Host "  [INFO] Esto puede tomar 10-15 minutos..." -ForegroundColor Gray
eksctl delete cluster --name $CLUSTER_NAME --region $REGION

# 3. Eliminar repositorios ECR
Write-Host "`n[3/4] Eliminando repositorios ECR..." -ForegroundColor Yellow
$repos = @("collector", "processor", "analyzer", "api")
foreach ($repo in $repos) {
    Write-Host "  Eliminando news-colcap/$repo..." -ForegroundColor Gray
    aws ecr delete-repository --repository-name "news-colcap/$repo" --force --region $REGION 2>$null
}

# 4. Verificar recursos restantes
Write-Host "`n[4/4] Verificando recursos restantes..." -ForegroundColor Yellow

# Verificar Load Balancers
Write-Host "  Verificando Load Balancers..." -ForegroundColor Gray
$lbs = (aws elbv2 describe-load-balancers --query "LoadBalancers[?contains(LoadBalancerName, 'news-colcap')].LoadBalancerArn" --output text)
if ($lbs) {
    Write-Host "  [WARN] Load Balancers encontrados (pueden tardar en eliminarse):" -ForegroundColor Yellow
    Write-Host "    $lbs" -ForegroundColor Gray
}

# Verificar Security Groups
Write-Host "  Verificando Security Groups..." -ForegroundColor Gray
$sgs = (aws ec2 describe-security-groups --filters "Name=tag:kubernetes.io/cluster/$CLUSTER_NAME,Values=owned" --query "SecurityGroups[].GroupId" --output text)
if ($sgs) {
    Write-Host "  [WARN] Security Groups encontrados (se eliminaran automaticamente):" -ForegroundColor Yellow
    Write-Host "    $sgs" -ForegroundColor Gray
}

Write-Host "`n[OK] Limpieza completada!" -ForegroundColor Green
Write-Host "`n[INFO] Recursos eliminados:" -ForegroundColor Cyan
Write-Host "  - Namespace de Kubernetes" -ForegroundColor White
Write-Host "  - Cluster EKS" -ForegroundColor White
Write-Host "  - Repositorios ECR" -ForegroundColor White
Write-Host "  - Load Balancers (en proceso)" -ForegroundColor White
Write-Host "  - EC2 Instances" -ForegroundColor White
Write-Host "  - EBS Volumes" -ForegroundColor White

Write-Host "`n[INFO] Verifica costos en AWS Console en 5-10 minutos" -ForegroundColor Yellow
Write-Host "  https://console.aws.amazon.com/billing/" -ForegroundColor White
