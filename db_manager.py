import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import ast  # --- ¡LÍNEA NUEVA! ---

# ----------------------------------------------------------------------
# GESTOR DE BASE DE DATOS (FIREBASE)
# ----------------------------------------------------------------------

@st.cache_resource
def get_db():
    """
    Inicializa y devuelve la conexión a la base de datos Firestore.
    Usa las credenciales de st.secrets.
    """
    try:
        firebase_admin.get_app()
    except ValueError:
        
        # --- ¡INICIO DE LA NUEVA LÓGICA! ---
        try:
            creds_from_secrets = st.secrets["firebase_credentials"]
            
            # Verificamos si es un string (que es lo que causa el error)
            if isinstance(creds_from_secrets, str):
                # Si es un string, lo convertimos a diccionario de forma segura
                creds_dict = ast.literal_eval(creds_from_secrets)
            else:
                # Si ya es un diccionario (como debería ser), lo usamos
                creds_dict = creds_from_secrets
            
            creds = credentials.Certificate(creds_dict)
            firebase_admin.initialize_app(creds)

        except Exception as e:
            # Si todo falla, lanzamos un error claro
            raise Exception(f"FALLO CRÍTICO AL INICIALIZAR FIREBASE. Error: {e}. Verifica tus 'secrets' en Streamlit Cloud.")
        # --- FIN DE LA NUEVA LÓGICA ---
    
    return firestore.client()

def get_catalog_collection(db):
    """Devuelve la referencia a la colección 'products'."""
    return db.collection('products')

def get_catalog_df(db):
    """
    Obtiene el catálogo de productos de Firestore y lo devuelve como un DataFrame.
    """
    collection_ref = get_catalog_collection(db)
    docs = collection_ref.stream()
    
    products_list = []
    for doc in docs:
        product_data = doc.to_dict()
        product_data['id'] = doc.id
        products_list.append(product_data)
        
    if not products_list:
        return pd.DataFrame(columns=['Nombre', 'Coste (€)', 'Precio Retail (€)', 'Permite Repetir?', 'id'])

    df = pd.DataFrame(products_list)
    column_order = ['id', 'Nombre', 'Coste (€)', 'Precio Retail (€)', 'Permite Repetir?']
    df = df[[col for col in column_order if col in df.columns]]
    return df

def add_product(db, product_data):
    """
    Añade un nuevo producto a la colección 'products'.
    """
    collection_ref = get_catalog_collection(db)
    collection_ref.add(product_data)

def delete_product(db, product_id):
    """
    Elimina un producto de la colección 'products' usando su ID de documento.
    """
    collection_ref = get_catalog_collection(db)
    collection_ref.document(product_id).delete()