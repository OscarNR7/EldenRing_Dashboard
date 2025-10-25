# Guía de Solución de Problemas (Troubleshooting)

Esta guía te ayudará a diagnosticar y resolver problemas comunes durante el deployment y la operación de la aplicación en Render.

## 🚨 Problema: Errores de CORS

**Síntomas:**
- El frontend no puede obtener datos del backend.
- En la consola del navegador aparecen errores como `Access to fetch at 'https://elden-ring-backend.onrender.com/api/v1/weapons' from origin 'https://elden-ring-frontend.onrender.com' has been blocked by CORS policy.`

**Causas y Soluciones:**

1.  **`CORS_ORIGINS` mal configurada en Render:**
    - **Verificación:** Ve al dashboard de Render -> `elden-ring-backend` -> `Environment`.
    - **Solución:** Asegúrate de que la variable `CORS_ORIGINS` contenga la URL **exacta** de tu frontend desplegado. 
      - **Correcto:** `https://elden-ring-frontend.onrender.com`
      - **Incorrecto:** `https://elden-ring-frontend.onrender.com/` (con una barra al final).
      - Si necesitas múltiples orígenes, sepáralos por comas: `https://url1.com,https://url2.com`.

2.  **El backend no está usando la configuración de CORS:**
    - **Verificación:** Revisa `backend/app/main.py` y asegúrate de que el middleware de CORS esté configurado y use `settings.get_cors_origins()`.
    - **Solución:** El código debería verse así:
      ```python
      app.add_middleware(
          CORSMiddleware,
          allow_origins=settings.get_cors_origins(),
          allow_credentials=True,
          allow_methods=["*"],
          allow_headers=["*"],
      )
      ```

## 🔌 Problema: El Backend no conecta a MongoDB

**Síntomas:**
- El backend se reinicia constantemente o muestra errores `502 Bad Gateway`.
- Los logs del backend en Render muestran `ConnectionFailure` o `ServerSelectionTimeoutError`.

**Causas y Soluciones:**

1.  **`MONGO_URI` incorrecta:**
    - **Verificación:** Revisa la variable de entorno `MONGO_URI` en Render.
    - **Solución:** Asegúrate de que la URI de conexión sea la correcta de MongoDB Atlas. Debe incluir tu usuario, contraseña y el nombre de la base de datos. Reemplaza `<password>` con tu contraseña real.

2.  **IP no autorizada en MongoDB Atlas:**
    - **Verificación:** Render usa IPs dinámicas para los servicios del plan gratuito.
    - **Solución:** En MongoDB Atlas, ve a `Network Access` y añade una regla que permita el acceso desde cualquier IP (`0.0.0.0/0`). **Nota:** Esto es menos seguro. Para producción seria, considera usar un plan de pago en Render con IPs estáticas.

3.  **Timeouts por Cold Starts:**
    - **Verificación:** Revisa `backend/app/database.py`.
    - **Solución:** Asegúrate de que `serverSelectionTimeoutMS` esté configurado en `30000` (30 segundos) para dar tiempo a que el servicio se "despierte".

## 🌐 Problema: El Frontend no conecta con el Backend

**Síntomas:**
- La aplicación carga, pero no muestra datos (ej. se queda en un estado de "cargando").
- Errores de red en la consola del navegador (ej. `404 Not Found` o `502 Bad Gateway` al intentar llamar a la API).

**Causas y Soluciones:**

1.  **`VITE_API_BASE_URL` no configurada en el Frontend:**
    - **Verificación:** En Render, ve a la configuración del servicio `elden-ring-frontend` -> `Environment`.
    - **Solución:** Añade una variable de entorno `VITE_API_BASE_URL` con la URL de tu backend desplegado (ej. `https://elden-ring-backend.onrender.com`).

2.  **El backend no está desplegado o tiene errores:**
    - **Verificación:** Accede directamente a la URL de tu backend. Deberías ver el mensaje de bienvenida de la API.
    - **Solución:** Si el backend no responde, revisa sus logs en Render para diagnosticar el problema (sigue los pasos de "El Backend no conecta a MongoDB").

## ⏳ Problema: Delays por Cold Starts

**Síntomas:**
- La primera visita a la aplicación tarda mucho en cargar (15-30 segundos).
- Después de un período de inactividad, la aplicación vuelve a ser lenta.

**Causas y Soluciones:**

1.  **Naturaleza del Plan Gratuito de Render:**
    - **Explicación:** Los servicios del plan gratuito se "duermen" después de 15 minutos de inactividad para ahorrar recursos. El "cold start" es el tiempo que tarda el servicio en despertarse.
    - **Solución (Mitigación):**
      - Asegúrate de que los timeouts en `database.py` sean lo suficientemente altos.
      - Informa a los usuarios de que la primera carga puede ser lenta.
    - **Solución (Completa):**
      - Actualiza a un plan de pago en Render para evitar que los servicios se duerman.

## 📦 Problema: Fallos en el Build

**Síntomas:**
- El deployment falla en el paso de `buildCommand`.
- Los logs de build en Render muestran errores.

**Causas y Soluciones:**

1.  **Dependencias faltantes o incorrectas:**
    - **Verificación (Backend):** Asegúrate de que `backend/requirements.txt` esté actualizado. Puedes regenerarlo con `pip freeze > requirements.txt` en tu entorno virtual.
    - **Verificación (Frontend):** Asegúrate de que `frontend/package.json` contenga todas las dependencias necesarias.

2.  **Versiones de Node.js o Python incorrectas:**
    - **Verificación:** En `render.yaml`, puedes especificar las versiones, aunque Render suele usar versiones LTS razonables por defecto.
    - **Solución:** Si necesitas una versión específica, añádela a `render.yaml`:
      ```yaml
      services:
        - type: web
          name: elden-ring-backend
          env: python
          pythonVersion: "3.11" # Ejemplo
        - type: web
          name: elden-ring-frontend
          env: static
          nodeVersion: "20" # Ejemplo
      ```

3.  **Comandos de build incorrectos:**
    - **Verificación:** Revisa los `buildCommand` en `render.yaml`.
      - **Backend:** `pip install -r requirements.txt`
      - **Frontend:** `npm install && npm run build`
    - **Solución:** Asegúrate de que estos comandos funcionen correctamente en tu entorno local.
