import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd

# ----------------------------------------------------------------------
# GESTOR DE BASE DE DATOS (FIREBASE)
# ----------------------------------------------------------------------

# Usamos st.cache_resource para inicializar la conexión una sola vez.
@st.cache_resource
def get_db():
    """
    Inicializa y devuelve la conexión a la base de datos Firestore.
    Usa las credenciales de st.secrets.
    """
    try:
        # Intenta obtener la app de Firebase por defecto (si ya está inicializada)
        firebase_admin.get_app()
    except ValueError:
        # Si no está inicializada, la configura
        # Carga las credenciales desde el archivo secrets.toml
        creds_dict = st.secrets["firebase_credentials"]
        creds = credentials.Certificate(creds_dict)
        firebase_admin.initialize_app(creds)
    
    # Devuelve el cliente de Firestore
    return firestore.client()

def get_catalog_collection(db):
    """Devuelve la referencia a la colección 'products'."""
    # IMPORTANTE: Esta es la ruta de la colección en Firestore.
    # Puedes cambiar 'products' si la nombraste de otra forma.
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
        product_data['id'] = doc.id  # Añadimos el ID del documento
        products_list.append(product_data)
        
    if not products_list:
        # Si la base de datos está vacía, devuelve un DataFrame vacío
        return pd.DataFrame(columns=['Nombre', 'Coste (€)', 'Precio Retail (€)', 'Permite Repetir?', 'id'])

    df = pd.DataFrame(products_list)
    # Reordenamos las columnas para que sea más legible
    column_order = ['id', 'Nombre', 'Coste (€)', 'Precio Retail (€)', 'Permite Repetir?']
    # Filtramos para asegurarnos de que solo incluimos columnas que existen
    df = df[[col for col in column_order if col in df.columns]]
    return df

def add_product(db, product_data):
    """
    Añade un nuevo producto a la colección 'products'.
    product_data debe ser un diccionario.
    """
    collection_ref = get_catalog_collection(db)
    collection_ref.add(product_data)

def delete_product(db, product_id):
    """
    Elimina un producto de la colección 'products' usando su ID de documento.
    """
    collection_ref = get_catalog_collection(db)
    collection_ref.document(product_id).delete()