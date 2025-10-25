# Guía de Deployment en Render

Esta guía detalla los pasos para desplegar el proyecto Full-Stack (FastAPI + React) en Render utilizando el archivo `render.yaml`.

## 1. Requisitos Previos

- Una cuenta en [Render](https://render.com/).
- El código del proyecto subido a un repositorio de GitHub o GitLab.
- [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) configurado con una base de datos y un usuario.

## 2. Configuración de MongoDB Atlas

1.  **Permitir acceso desde cualquier IP:**
    - En tu clúster de Atlas, ve a `Network Access`.
    - Haz clic en `Add IP Address`.
    - Selecciona `Allow Access from Anywhere` (0.0.0.0/0).
    - **Nota:** Esto es necesario para el plan gratuito de Render, que no tiene IPs estáticas.

2.  **Obtener la URI de Conexión:**
    - Ve a `Database` y haz clic en `Connect` en tu clúster.
    - Selecciona `Drivers`.
    - Copia la `Connection String`. Asegúrate de reemplazar `<password>` con la contraseña de tu usuario de la base de datos.

## 3. Proceso de Deployment en Render

Render utilizará el archivo `render.yaml` para configurar y desplegar automáticamente los servicios.

1.  **Crear un "Blueprint Instance":**
    - En el dashboard de Render, ve a la sección `Blueprints`.
    - Haz clic en `New Blueprint Instance`.
    - Conecta el repositorio de tu proyecto.
    - Render leerá el `render.yaml` y te mostrará los servicios que va a crear (`elden-ring-backend` y `elden-ring-frontend`).

2.  **Configurar Variables de Entorno:**
    - Antes de aprobar la creación, Render te pedirá que introduzcas los valores para las variables de entorno que marcaste con `sync: false`.
    - Para el servicio `elden-ring-backend`, configura lo siguiente:
      - **`MONGO_URI`**: Pega la URI de conexión de MongoDB Atlas que obtuviste en el paso anterior.
      - **`CORS_ORIGINS`**: Render autocompletará la URL del servicio frontend. Debería ser algo como `https://elden-ring-frontend.onrender.com`. Asegúrate de que no tenga una barra (`/`) al final.

    - Para el servicio `elden-ring-frontend`, añade la siguiente variable:
      - **`VITE_API_BASE_URL`**: Render autocompletará la URL del servicio backend. Debería ser algo como `https://elden-ring-backend.onrender.com`.

3.  **Lanzar el Deployment:**
    - Haz clic en `Apply` para que Render comience a construir y desplegar tus servicios.
    - Puedes monitorear el progreso en los logs de cada servicio.

## 4. Verificación Post-Deployment

Una vez que Render indique que los servicios están "Live", realiza las siguientes verificaciones:

- **URLs Esperadas:**
  - **Backend:** `https://elden-ring-backend.onrender.com`
  - **Frontend:** `https://elden-ring-frontend.onrender.com`

- **Comandos de Verificación:**

  1.  **Verificar el Backend:**
      - Abre tu navegador y visita la URL de tu backend. Deberías ver el mensaje de bienvenida de la API.
      - Visita el endpoint de health check: `https://elden-ring-backend.onrender.com/api/v1/health`. Debería mostrar `{"status":"healthy"}`.

  2.  **Verificar el Frontend:**
      - Abre la URL de tu frontend en el navegador.
      - La aplicación debería cargar y mostrar los datos de Elden Ring.
      - Abre la consola del desarrollador (F12) y comprueba que no haya errores de CORS o de red (4xx/5xx).

## 5. Rollback (Reversión)

Si un nuevo deployment introduce un bug, puedes revertir a una versión anterior fácilmente:

1.  Ve al dashboard de tu servicio en Render.
2.  Haz clic en la pestaña `Deploys`.
3.  Encontrarás una lista de todos los deployments anteriores.
4.  Haz clic en `Rollback to this deploy` en el deployment al que deseas volver.

Render redesplegará la versión anterior del código sin necesidad de hacer un `git revert`.
