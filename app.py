import streamlit as st
import pandas as pd
from model import solve_box_problem
import db_manager  # Importamos nuestro gestor de base de datos

# ----------------------------------------------------------------------
# APLICACIÓN STREAMLIT
# ----------------------------------------------------------------------

# --- 1. Configuración de la Página y Título ---
st.set_page_config(page_title="Optimizador TGTG", layout="wide")
st.title("📦 Optimizador de Cajas 'Too Good To Go'")
st.write("Esta app te ayuda a decidir la composición óptima de tus cajas para minimizar pérdidas.")

# --- 2. Conexión a la Base de Datos ---
try:
    # Obtenemos la conexión a la BD (cacheada por Streamlit)
    db = db_manager.get_db()
    # Cargamos el catálogo desde la BD
    if 'product_catalog_df' not in st.session_state:
        st.session_state.product_catalog_df = db_manager.get_catalog_df(db)

except Exception as e:
    # --- ¡SECCIÓN MODIFICADA! ---
    # Si get_db() lanza la Excepción que creamos, la mostramos.
    st.error(f"""
        **Error fatal al conectar con Firebase:**
        {e}
    """)
    st.stop() # Detenemos la app si no hay BD

# --- 3. Definición de Pestañas ---
tab1, tab2 = st.tabs(["🛒 Optimizar Cajas (Diario)", "📚 Gestionar Catálogo (Admin)"])

# --- Pestaña 1: Optimización Diaria ---
with tab1:
    st.header("Paso 1: Define las reglas del día")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        box_sale_price = st.number_input("Precio de Venta de la Caja (€)", min_value=0.0, value=4.0, step=0.5)
    with col2:
        box_retail_min = st.number_input("Valor Retail Mínimo (€)", min_value=0.0, value=12.0, step=1.0)
    with col3:
        max_boxes = st.number_input("Nº Máximo de Cajas a crear", min_value=1, value=5, step=1)

    st.header("Paso 2: Introduce tu inventario de hoy")
    st.info("Rellena solo las cantidades de los productos que tienes hoy. Marca los que caducan.")

    # Usamos el catálogo de la base de datos
    catalog_df = st.session_state.product_catalog_df.copy()
    
    # Añadimos las columnas 'Cantidad Hoy' y 'Caduca Hoy?'
    catalog_df['Cantidad Hoy'] = 0
    catalog_df['Caduca Hoy?'] = False
    
    # Creamos la tabla editable
    edited_df = st.data_editor(catalog_df,
        column_config={
            "id": None, # Ocultamos la columna ID
            "Nombre": st.column_config.TextColumn("Producto", disabled=True),
            "Coste (€)": st.column_config.NumberColumn("Coste", disabled=True, format="€%.2f"),
            "Precio Retail (€)": st.column_config.NumberColumn("Retail", disabled=True, format="€%.2f"),
            "Permite Repetir?": st.column_config.CheckboxColumn("Repetible?", disabled=True),
            "Cantidad Hoy": st.column_config.NumberColumn("Cantidad Hoy", min_value=0, step=1),
            "Caduca Hoy?": st.column_config.CheckboxColumn("Caduca Hoy?")
        },
        use_container_width=True,
        hide_index=True
    )

    st.header("Paso 3: Calcular Cajas")
    
    if st.button("🚀 Optimizar mis cajas", type="primary", use_container_width=True):
        # Filtramos solo los productos con cantidad
        inventory_df = edited_df[edited_df['Cantidad Hoy'] > 0].copy()
        
        if inventory_df.empty:
            st.warning("No has introducido ningún producto.")
        elif inventory_df[inventory_df['Caduca Hoy?'] == True].empty:
            st.warning("No has marcado ningún producto como 'Caduca Hoy?'. No es necesario crear cajas.")
        else:
            with st.spinner("Buscando la solución óptima..."):
                # Renombramos columnas para el modelo
                inventory_df.rename(columns={
                    'Nombre': 'Product Name',
                    'Coste (€)': 'Purchase Cost',
                    'Precio Retail (€)': 'Retail Price',
                    'Permite Repetir?': 'Allow Repeats?',
                    'Cantidad Hoy': 'Quantity',
                    'Caduca Hoy?': 'Expires Today'
                }, inplace=True)

                # Llamamos al solver
                boxes, net_loss, status = solve_box_problem(
                    inventory_df,
                    box_retail_min,
                    box_sale_price,
                    max_boxes
                )

                if status == 'Optimal':
                    st.success(f"¡Solución Óptima Encontrada! **Pérdida Neta Total: €{net_loss:.2f}**")
                    
                    if not boxes:
                        st.info("La solución óptima es no crear ninguna caja con los productos que caducan.")
                    
                    for i, box in enumerate(boxes):
                        total_cost = box['Total Cost']
                        net_result = box_sale_price - total_cost
                        
                        box_color = "green" if net_result >= 0 else "red"
                        
                        with st.container(border=True):
                            st.subheader(f"Caja {i+1} (Valor Retail: €{box['Total Retail']:.2f})")
                            st.markdown(f"**Coste Total:** €{total_cost:.2f} | **Venta:** €{box_sale_price:.2f} | **Resultado: <span style='color:{box_color};'>€{net_result:.2f}</span>**", unsafe_allow_html=True)
                            
                            box_df = pd.DataFrame(box['Items'])
                            st.dataframe(box_df, use_container_width=True, hide_index=True)

                else:
                    st.error("No se pudo encontrar una solución óptima. Posibles razones: \n"
                             "- Es imposible cumplir el valor retail mínimo de €{box_retail_min} con los productos que caducan. \n"
                             "- Has puesto un número máximo de cajas muy bajo.")

# --- Pestaña 2: Gestión del Catálogo ---
with tab2:
    st.header("Gestionar Catálogo de Productos")
    st.info("Aquí puedes añadir o eliminar productos de tu lista maestra. Estos productos aparecerán en la pestaña principal.")

    with st.form("new_product_form", clear_on_submit=True):
        st.subheader("Añadir Nuevo Producto")
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre del Producto")
            coste = st.number_input("Coste de Compra (€)", min_value=0.0, step=0.1)
        with col2:
            precio_retail = st.number_input("Precio de Venta Retail (€)", min_value=0.0, step=0.1)
            permite_repetir = st.checkbox("¿Permitir repetir en la misma caja?", value=True)
        
        submitted = st.form_submit_button("Añadir Producto")
        
        if submitted:
            if not nombre:
                st.warning("El nombre del producto no puede estar vacío.")
            else:
                new_product = {
                    "Nombre": nombre,
                    "Coste (€)": coste,
                    "Precio Retail (€)": precio_retail,
                    "Permite Repetir?": permite_repetir
                }
                try:
                    db_manager.add_product(db, new_product)
                    # Actualizamos el catálogo en el estado de la sesión
                    st.session_state.product_catalog_df = db_manager.get_catalog_df(db)
                    st.success(f"¡Producto '{nombre}' añadido con éxito!")
                except Exception as e:
                    st.error(f"No se pudo añadir el producto: {e}")

    st.divider()

    st.subheader("Catálogo Actual")
    
    if st.session_state.product_catalog_df.empty:
        st.info("Tu catálogo está vacío. Añade tu primer producto usando el formulario de arriba.")
    else:
        catalog_to_display = st.session_state.product_catalog_df.copy()
        
        # Añadimos una columna 'Eliminar'
        catalog_to_display['Eliminar'] = False
        
        deleted_df = st.data_editor(catalog_to_display,
            column_config={
                "id": None, # Ocultamos la columna ID
                "Nombre": st.column_config.TextColumn("Producto", disabled=True),
                "Coste (€)": st.column_config.NumberColumn("Coste", disabled=True, format="€%.2f"),
                "Precio Retail (€)": st.column_config.NumberColumn("Retail", disabled=True, format="€%.2f"),
                "Permite Repetir?": st.column_config.CheckboxColumn("Repetible?", disabled=True),
                "Eliminar": st.column_config.CheckboxColumn("Eliminar")
            },
            use_container_width=True,
            hide_index=True
        )

        # Buscamos qué productos se marcaron para eliminar
        products_to_delete = deleted_df[deleted_df['Eliminar'] == True]
        
        if not products_to_delete.empty:
            if st.button("Confirmar Eliminación", type="primary", use_container_width=True):
                try:
                    for product_id in products_to_delete['id']:
                        db_manager.delete_product(db, product_id)
                    
                    # Recargamos el catálogo y forzamos el refresco de la app
                    st.session_state.product_catalog_df = db_manager.get_catalog_df(db)
                    st.success("¡Productos eliminados! Recargando...")
                    st.rerun()
                except Exception as e:
                    st.error(f"No se pudo eliminar: {e}")