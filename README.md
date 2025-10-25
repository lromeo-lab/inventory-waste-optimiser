# 📦 Optimizador de Cajas "Too Good To Go"

Este proyecto es una aplicación web creada con Streamlit para ayudar a pequeños negocios, como cafeterías o pastelerías, a optimizar la creación de "cajas sorpresa" (como las de la app *Too Good To Go*).

El objetivo principal es **minimizar las pérdidas** por productos que van a caducar, agrupándolos inteligentemente en cajas que cumplan con un valor retail mínimo.

<!-- [![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://tu-app.streamlit.app) -->

---

## 🚀 Características Principales

* **Optimización Inteligente:** Utiliza un modelo de optimización lineal (a través de PuLP) para encontrar la combinación de productos que minimiza la pérdida neta (Coste Total - Ingreso Total).
* **Gestión de Catálogo (Admin):** Permite añadir, editar y eliminar productos "maestros" (nombre, coste, precio retail, etc.) que se guardan en la sesión de la app.
* **Interfaz de Uso Diario:** Una pestaña simple donde el usuario solo necesita introducir las cantidades del día y marcar qué productos caducan hoy.
* **Reglas de Negocio Flexibles:** Permite configurar:
    * El precio de venta de la caja.
    * El valor retail mínimo requerido por caja.
    * El número máximo de cajas a crear.
    * Restricciones por producto (si se pueden repetir o no en una misma caja).
* **Resultados Claros:** Muestra un resumen de la operación (pérdida neta, cajas creadas) y la composición detallada de cada caja recomendada.

## 🛠️ Tecnologías Utilizadas

* **Python:** Lenguaje principal.
* **Streamlit:** Para construir la interfaz de usuario web interactiva.
* **PuLP:** Para modelar y resolver el problema de optimización lineal.
* **Pandas:** Para la manipulación de datos entre la UI y el modelo.

## 🏃‍♂️ Cómo Ejecutar Localmente

Sigue estos pasos para ejecutar la aplicación en tu propio ordenador.

**1. Clona el repositorio:**

```bash
git clone [https://github.com/tu-usuario/optimizador-cafeteria.git](https://github.com/tu-usuario/optimizador-cafeteria.git)
cd optimizador-cafeteria
```

**2. Crea y activa un entorno virtual:**

```bash
# Crear el entorno
python3 -m venv env

# Activar en macOS/Linux
source env/bin/activate

# Activar en Windows
.\env\Scripts\activate
```

**3. Instala las dependencias:**

El archivo `requirements.txt` contiene todas las librerías necesarias.

```bash
pip install -r requirements.txt
```

**4. Ejecuta la aplicación Streamlit:**

```bash
streamlit run app.py
```

¡Se abrirá una pestaña en tu navegador con la aplicación funcionando!

## 📂 Estructura del Proyecto

El proyecto está separado en lógica de negocio y presentación para un mantenimiento más sencillo.

```plaintext
optimizador-cafeteria/
│
├── 📄 app.py           # Contiene toda la lógica de la UI (Streamlit)
├── 🧠 model.py         # Contiene solo la función de optimización (PuLP)
├── 📋 requirements.txt # Lista de dependencias de Python
└── 📖 README.md        # Este archivo
```

## ☁️ Despliegue (Deployment)

Esta aplicación está diseñada para ser desplegada fácilmente usando **Streamlit Community Cloud**.

1.  Sube este repositorio a tu cuenta de GitHub.
2.  Conecta tu cuenta de GitHub a [Streamlit Community Cloud](https://share.streamlit.io/).
3.  Crea una "New App", selecciona el repositorio y usa `app.py` como el archivo principal.
4.  ¡Despliega!

Recuerda **configurar una contraseña** desde el panel de control de Streamlit para proteger tus datos de costes.