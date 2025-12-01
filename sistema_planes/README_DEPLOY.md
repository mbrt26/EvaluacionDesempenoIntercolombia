# 📚 Guía de Despliegue en Google Cloud Run

## 🎯 Configuración de Costo Casi Cero

Esta aplicación está configurada para minimizar costos en Google Cloud Run:

- **Escala a cero**: No hay costo cuando no hay tráfico
- **Memoria mínima**: 256MB
- **CPU mínima**: 1 vCPU
- **Máximo 1 instancia**: Evita escalado excesivo
- **Base de datos SQLite**: Sin costos de Cloud SQL

## 📋 Prerequisitos

1. **Cuenta de Google Cloud Platform** con proyecto "appsindunnova"
2. **Google Cloud SDK (gcloud)** instalado
3. **Permisos** de Cloud Run Admin y Cloud Build Editor

## 🚀 Pasos para Desplegar

### 1. Instalar Google Cloud SDK (si no lo tienes)

```bash
# En Mac
brew install google-cloud-sdk

# En Linux/WSL
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

### 2. Autenticarse con Google Cloud

```bash
gcloud auth login
gcloud config set project appsindunnova
```

### 3. Desplegar la Aplicación

#### Opción A: Despliegue Automático (Recomendado)

```bash
# Ejecutar el script de despliegue
./deploy.sh
```

#### Opción B: Despliegue Manual

```bash
# Configurar proyecto
gcloud config set project appsindunnova

# Habilitar APIs necesarias
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com

# Construir y subir imagen
gcloud builds submit --tag gcr.io/appsindunnova/sistema-planes .

# Desplegar a Cloud Run
gcloud run deploy sistema-planes \
    --image gcr.io/appsindunnova/sistema-planes \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 256Mi \
    --cpu 1 \
    --max-instances 1 \
    --min-instances 0 \
    --port 8080 \
    --set-env-vars "DJANGO_SETTINGS_MODULE=config.settings_production"
```

### 4. Configurar Dominio Personalizado (Opcional)

```bash
gcloud run domain-mappings create \
    --service sistema-planes \
    --domain tu-dominio.com \
    --region us-central1
```

## 🔧 Configuración Post-Despliegue

### Crear Superusuario (Primera vez)

1. Conectarse al servicio:
```bash
gcloud run services describe sistema-planes --region us-central1
```

2. Usar Cloud Shell para ejecutar comandos:
```bash
gcloud run deploy sistema-planes \
    --image gcr.io/appsindunnova/sistema-planes \
    --command "/bin/bash" \
    --args "-c" \
    --args "python manage.py createsuperuser"
```

### Actualizar la Aplicación

```bash
# Hacer cambios en el código
# Luego ejecutar:
./deploy.sh
```

## 💰 Estimación de Costos

Con la configuración actual:

- **Sin tráfico**: $0 (escala a cero)
- **Tráfico bajo** (< 2 millones de requests/mes): Gratis (tier gratuito)
- **Tráfico moderado**: ~$5-10/mes

### Tier Gratuito de Cloud Run incluye:
- 2 millones de requests por mes
- 360,000 GB-segundos de memoria
- 180,000 vCPU-segundos

## 🔍 Monitoreo

### Ver logs en tiempo real:
```bash
gcloud run logs read --service sistema-planes --region us-central1
```

### Ver métricas en la consola:
https://console.cloud.google.com/run/detail/us-central1/sistema-planes/metrics

## ⚠️ Consideraciones Importantes

1. **Cold Starts**: Primera request después de inactividad tarda 5-10 segundos
2. **SQLite en producción**: No recomendado para alto tráfico o múltiples instancias
3. **Archivos media**: Se pierden al reiniciar (considerar Cloud Storage)
4. **Sesiones**: Se pierden al escalar a cero (considerar Memorystore)

## 🆘 Solución de Problemas

### Error: "Permission denied"
```bash
gcloud projects add-iam-policy-binding appsindunnova \
    --member="user:tu-email@gmail.com" \
    --role="roles/run.admin"
```

### Error: "Image not found"
```bash
# Verificar que la imagen existe
gcloud container images list --repository=gcr.io/appsindunnova
```

### Error: "Service unavailable"
```bash
# Verificar logs
gcloud run logs read --service sistema-planes --region us-central1 --limit 50
```

## 📝 Variables de Entorno

Puedes configurar variables adicionales:

```bash
gcloud run services update sistema-planes \
    --update-env-vars "KEY=value,ANOTHER_KEY=another_value" \
    --region us-central1
```

## 🔄 Rollback

Si algo sale mal, puedes volver a una versión anterior:

```bash
# Listar revisiones
gcloud run revisions list --service sistema-planes --region us-central1

# Volver a una revisión anterior
gcloud run services update-traffic sistema-planes \
    --to-revisions=sistema-planes-00001-abc=100 \
    --region us-central1
```

## 📊 Optimizaciones Adicionales para Reducir Costos

1. **Usar Cloud Scheduler** para "calentar" el servicio en horarios específicos
2. **Implementar caché** agresivo con Redis (Memorystore)
3. **Optimizar imágenes Docker** (multi-stage builds)
4. **Usar CDN** para archivos estáticos (Cloud CDN)

---

**Contacto**: Para dudas sobre el despliegue, contactar al equipo de DevOps de appsindunnova.