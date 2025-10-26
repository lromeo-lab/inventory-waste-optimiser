import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import ast # Para forzar la conversión de string a dict

# --- Constantes ---
COLLECTION_NAME = 'products'
# --- Definimos las columnas esperadas ---
EXPECTED_COLS = ['id', 'Nombre', 'Coste (€)', 'Precio Retail (€)', 'Permite Repetir?', 'Vida Útil (días)']

# --- Inicialización de Firebase (Cacheada) ---
@st.cache_resource
def get_db():
    try:
        # 1. Intentar obtener las credenciales de los secretos
        creds_dict = st.secrets["FIREBASE"]
        
        # 2. Comprobar si es un string y convertirlo
        if isinstance(creds_dict, str):
            try:
                creds_dict = ast.literal_eval(creds_dict)
            except Exception as e:
                st.error(f"Error al parsear 'firebase_credentials' (string a dict): {e}")
                return None
        
        # 3. Comprobar si es un diccionario
        if not isinstance(creds_dict, dict):
            st.error(f"Las 'firebase_credentials' no son un diccionario. Tipo encontrado: {type(creds_dict)}")
            return None

        # 4. Inicializar la app
        cred = credentials.Certificate(creds_dict)
        
        # Evitar error de reinicialización
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        
        return firestore.client()

    except Exception as e:
        st.error(f"""
            **Error al conectar con Firebase.**
            Detalle: {e}
            Asegúrate de que tu secreto 'firebase_credentials' en Streamlit Cloud
            es una copia exacta de tu archivo local '.streamlit/secrets.toml'
            (empezando por [firebase_credentials]).
        """)
        return None

# --- Operaciones CRUD ---

@st.cache_data(ttl=60) # Cachear por 60 segundos
def get_catalog_df(_db):
    if _db is None:
        return pd.DataFrame(columns=EXPECTED_COLS) # Devuelve DF vacío si no hay BD
        
    products_ref = _db.collection(COLLECTION_NAME)
    docs = products_ref.stream()
    
    products_list = []
    for doc in docs:
        doc_data = doc.to_dict()
        doc_data['id'] = doc.id
        products_list.append(doc_data)

    if not products_list:
        # Devuelve un DF vacío con las columnas esperadas si no hay datos
        return pd.DataFrame(columns=EXPECTED_COLS)

    df = pd.DataFrame(products_list)
    
    # Asegurar que todas las columnas esperadas existan, añadiendo las que falten
    for col in EXPECTED_COLS:
        if col not in df.columns:
            if col == 'Vida Útil (días)':
                 df[col] = 1
            elif col == 'Permite Repetir?':
                df[col] = True
            elif col != 'id':
                 df[col] = pd.NA
            
    # Reordenar y filtrar columnas para que coincidan exactamente
    df = df[EXPECTED_COLS]
    return df

def add_product(_db, product_data):
    if _db is None: return
    product_data.pop('id', None)
    _db.collection(COLLECTION_NAME).add(product_data)
    get_catalog_df.clear() # Limpiar caché

def update_product(_db, product_id, product_data):
    if _db is None: return
    _db.collection(COLLECTION_NAME).document(product_id).update(product_data)
    get_catalog_df.clear() # Limpiar caché

def delete_product(_db, product_id):
    if _db is None: return
    _db.collection(COLLECTION_NAME).document(product_id).delete()
    get_catalog_df.clear() # Limpiar caché