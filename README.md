# 📦 Optimizador de Packs "Too Good To Go"

Esta es una aplicación web construida con Streamlit y Python para ayudar a cafeterías y pequeños negocios a optimizar la creación de "cajas sorpresa" (como las de "Too Good To Go"), minimizando las pérdidas de producto y maximizando el resultado neto.

La aplicación utiliza un modelo de optimización lineal (PuLP) para encontrar la combinación perfecta de productos, respetando un valor de retail mínimo y priorizando los productos que caducan.

## ✨ Características Principales

* **Optimización Inteligente:** Utiliza `model.py` para resolver el "problema de la mochila" (bin packing) y encontrar la mejor combinación de productos.
* **Gestión de Catálogo:** Una pestaña de "Admin" (`app.py`) permite añadir, editar y eliminar productos del inventario maestro.
* **Base de Datos en la Nube:** Todos los productos del catálogo se guardan de forma persistente en **Google Firebase Firestore** (`db_manager.py`).
* **Interfaz Diaria Sencilla:** El usuario solo introduce las cantidades del día. La app marca automáticamente los productos que caducan basándose en su "Vida Útil".
* **Lógica de Resultados Clara:** Muestra el "Resultado Neto" (Ganancia o Pérdida) de forma intuitiva (positivo = bueno, negativo = malo).

## 🚀 Cómo Empezar (Localmente)

Sigue estos pasos para ejecutar la aplicación en tu máquina local.

### 1. Prerrequisitos

* Python 3.8 o superior
* Una cuenta de [Google Firebase](https://console.firebase.google.com/)
* Git

### 2. Clonar el Repositorio

```bash
git clone [https://github.com/tu-usuario/tu-repositorio.git](https://github.com/tu-usuario/tu-repositorio.git)
cd tu-repositorio
```

### 3. Configurar el Entorno Virtual

Es vital crear un entorno virtual para aislar las dependencias.

```bash
# Crear el entorno (ej. 'env')
python3 -m venv env

# Activar el entorno
# En macOS/Linux:
source env/bin/activate
# En Windows:
# .\\env\\Scripts\\activate
```

### 4. Instalar Dependencias

Todas las librerías necesarias están en `requirements.txt`.

```bash
# Asegúrate de que tu entorno esté activo
pip install -r requirements.txt
```

### 5. Configurar Firebase (El Paso Crítico)

La app necesita credenciales para conectarse a tu base de datos.

1.  **Crea un Proyecto en Firebase:** Ve a la [Consola de Firebase](https://console.firebase.google.com/) y crea un nuevo proyecto.
2.  **Habilita Firestore:** En el menú "Compilación", activa "Firestore Database" (inicia en **modo de producción**).
3.  **Obtén tu Clave de Servicio:**
    * En Firebase, ve a "Configuración del proyecto" (el engranaje).
    * Ve a la pestaña "Cuentas de servicio".
    * Haz clic en "Generar nueva clave privada". Se descargará un archivo `.json`.
4.  **Crea el Archivo `secrets.toml`:**
    * En la raíz de tu proyecto, crea una carpeta: `mkdir .streamlit`
    * Dentro de esa carpeta, crea un archivo: `touch .streamlit/secrets.toml`
5.  **Copia tus Credenciales:**
    * Abre el archivo `.json` que descargaste.
    * Abre tu archivo `.streamlit/secrets.toml`.
    * Copia el contenido del `.json` al `.toml` usando el siguiente formato. **¡Este formato es crucial!**

```toml
# .streamlit/secrets.toml

[firebase_credentials]
type = "service_account"
project_id = "el-id-de-tu-proyecto-json"
private_key_id = "el-key-id-de-tu-json"

# IMPORTANTE
# Usa COMILLAS TRIPLES (""") para la clave privada.
private_key = \"\"\"-----BEGIN PRIVATE KEY-----\\n...TU CLAVE LARGA...\\n-----END PRIVATE KEY-----\\n\"\"\"

client_email = "firebase-adminsdk-....@....iam.gserviceaccount.com"
client_id = "..."
auth_uri = "[https://accounts.google.com/o/oauth2/auth](https://accounts.google.com/o/oauth2/auth)"
token_uri = "[https://oauth2.googleapis.com/token](https://oauth2.googleapis.com/token)"
auth_provider_x509_cert_url = "[https://www.googleapis.com/oauth2/v1/certs](https://www.googleapis.com/oauth2/v1/certs)"
client_x509_cert_url = "[https://www.googleapis.com/](https://www.googleapis.com/)..."
universe_domain = "googleapis.com"
```

### 6. Ejecutar la App Localmente

Debido a los conflictos de rutas que descubrimos, usa este comando para ejecutar la app:

```bash
# (Asegúrate de que tu entorno esté activo)
python -m streamlit run app.py
```

## ☁️ Despliegue en Streamlit Cloud

1.  **Sube tu proyecto a GitHub:** Asegúrate de que tu `README.md`, `app.py`, `model.py`, `db_manager.py` y `requirements.txt` estén subidos.
2.  **Crea una App en Streamlit:** Ve a [share.streamlit.io](https://share.streamlit.io/), conecta tu repositorio de GitHub y selecciona `app.py` como el archivo principal.
3.  **Configura los "Secrets":**
    * En el panel de tu app en Streamlit, ve a "Settings" > "Secrets".
    * Abre tu archivo **local** `.streamlit/secrets.toml`.
    * **Copia todo el contenido** de ese archivo (empezando por `[firebase_credentials]...`).
    * **Pégalo** en la caja de texto de "Secrets" en Streamlit Cloud.
    * Guarda. La app se reiniciará y se conectará a tu Firebase.

## 📂 Estructura del Proyecto

```
tu-repositorio/
├── .streamlit/
│   └── secrets.toml    # (Credenciales locales, NO subir a GitHub)
├── env/                # (Carpeta del entorno virtual, ignorada por git)
├── .gitignore          # (Recomendado, para ignorar 'env/', '*.pyc', etc.)
├── app.py              # (La interfaz de usuario de Streamlit)
├── db_manager.py       # (Lógica para conectar y hablar con Firebase)
├── model.py            # (El modelo de optimización PuLP)
├── requirements.txt    # (Las dependencias de Python)
└── README.md           # (Este archivo)
```