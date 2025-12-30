# Comandos para correr los servicios con Kubernetes:

minikube start

# Configurar minikube para que tome las imágenes locales

eval $(minikube docker-env)

# A partir de aquí se corre todo desde la raíz del proyecto
# Construir las imágenes

docker build -t news-colcap/analyzer:latest ./services/analyzer
docker build -t news-colcap/collector:latest ./services/collector
docker build -t news-colcap/api:latest ./services/api
docker build -t news-colcap/processor:latest ./services/processor

# Ejecutar los .yaml
kubectl apply -f k8s/

# Ver los pods
kubectl get pods -n news-colcap
