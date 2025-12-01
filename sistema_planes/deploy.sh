#!/bin/bash

# Script de despliegue manual para Google Cloud Run
# Configuración de costo mínimo

# Variables de configuración
PROJECT_ID="appsindunnova"  # Cambia esto por tu Project ID real
SERVICE_NAME="sistema-planes"
REGION="us-central1"  # us-central1 suele ser más económico
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Iniciando despliegue a Google Cloud Run..."
echo "📦 Proyecto: ${PROJECT_ID}"
echo "🌍 Región: ${REGION}"
echo "📝 Servicio: ${SERVICE_NAME}"

# Verificar que gcloud esté instalado
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI no está instalado. Por favor, instálalo primero."
    echo "   Visita: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Configurar el proyecto
echo "⚙️ Configurando proyecto ${PROJECT_ID}..."
gcloud config set project ${PROJECT_ID}

# Habilitar APIs necesarias
echo "🔧 Habilitando APIs necesarias..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Construir la imagen con Cloud Build
echo "🏗️ Construyendo imagen Docker..."
gcloud builds submit --tag ${IMAGE_NAME} .

# Desplegar a Cloud Run con configuración de costo mínimo
echo "🚀 Desplegando a Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --memory 256Mi \
    --cpu 1 \
    --max-instances 1 \
    --min-instances 0 \
    --port 8080 \
    --set-env-vars "DJANGO_SETTINGS_MODULE=config.settings_production,SECRET_KEY=$(openssl rand -base64 32)"

# Obtener la URL del servicio
echo "✅ Despliegue completado!"
echo "🌐 URL del servicio:"
gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)'

echo ""
echo "📊 Configuración de costo mínimo aplicada:"
echo "   - Memoria: 256Mi (mínimo)"
echo "   - CPU: 1 vCPU"
echo "   - Instancias mínimas: 0 (escala a cero - sin costo cuando no hay tráfico)"
echo "   - Instancias máximas: 1 (evita escalado excesivo)"
echo ""
echo "💡 Consejos para mantener costos bajos:"
echo "   1. El servicio escalará a 0 cuando no haya tráfico (sin costo)"
echo "   2. Primera solicitud después de inactividad tardará ~5-10 segundos (cold start)"
echo "   3. Para tráfico bajo, los costos serán mínimos o gratuitos dentro del tier gratuito"
echo "   4. Monitorea el uso en: https://console.cloud.google.com/run"