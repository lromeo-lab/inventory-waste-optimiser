import streamlit as st
import pandas as pd
from model import solve_box_problem
import db_manager

# ----------------------------------------------------------------------
# APLICACIÓN STREAMLIT
# ----------------------------------------------------------------------

# --- 1. Configuración de la Página y Título ---
st.set_page_config(page_title="Optimizador TGTG", layout="wide")
st.title("📦 Optimizador de Packs 'Too Good To Go'")
st.write("Esta app te ayuda a decidir la composición óptima de tus cajas para minimizar pérdidas.")

# --- 2. Conexión a la Base de Datos ---
# Obtenemos la conexión a la BD (cacheada por Streamlit)
try:
    db = db_manager.get_db()
except Exception as e:
    st.error(f"Error al conectar con Firebase. Verifica tus 'secrets.toml'.")
    st.error(e)
    st.stop()


# --- 3. Definición de las Pestañas ---
tab_daily, tab_admin = st.tabs(["🛒 Optimizar Cajas (Diario)", "📚 Gestionar Catálogo (Admin)"])

# ----------------------------------------------------------------------
# PESTAÑA 1: Optimizar Cajas (Diario)
# ----------------------------------------------------------------------
with tab_daily:
    st.header("Paso 1: Define las reglas del día")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        box_sale_price = st.number_input("Precio de Venta de la Caja (€)", min_value=0.0, value=4.00, step=0.50)
    with col2:
        box_retail_min = st.number_input("Valor Retail Mínimo (€)", min_value=0.0, value=12.00, step=1.00)
    with col3:
        max_boxes = st.number_input("Nº Máximo de Cajas a crear", min_value=1, value=5, step=1)

    st.header("Paso 2: Introduce tu inventario de hoy")
    st.info("Rellena solo las cantidades de los productos que tienes hoy. Marca los que caducan.")

    # --- Cargar Catálogo desde la BD ---
    # Ya no usamos session_state, leemos de la BD cada vez.
    try:
        product_catalog_df = db_manager.get_catalog_df(db)
    except Exception as e:
        st.error(f"No se pudo cargar el catálogo desde Firestore: {e}")
        st.stop()


    if product_catalog_df.empty:
        st.warning("Tu catálogo de productos está vacío. Ve a la pestaña 'Gestionar Catálogo' para añadir productos.")
    else:
        # Creamos el formulario para el inventario del día
        with st.form("inventory_form"):
            
            # Usamos una copia para no modificar el DataFrame original
            daily_inventory_df = product_catalog_df.copy()
            
            # Añadimos las columnas 'Cantidad Hoy' y 'Caduca Hoy'
            daily_inventory_df['Cantidad Hoy'] = 0
            daily_inventory_df['Caduca Hoy'] = False
            
            # Mostramos el editor de datos para que el usuario rellene
            edited_df = st.data_editor(
                daily_inventory_df,
                column_config={
                    "id": None, # Ocultamos la columna 'id'
                    "Nombre": st.column_config.TextColumn("Producto", disabled=True),
                    "Coste (€)": None, # Ocultamos
                    "Precio Retail (€)": None, # Ocultamos
                    "Permite Repetir?": None, # Ocultamos
                    "Cantidad Hoy": st.column_config.NumberColumn("Cantidad Hoy", min_value=0, step=1),
                    "Caduca Hoy": st.column_config.CheckboxColumn("Caduca Hoy")
                },
                hide_index=True,
                width="stretch"
            )
            
            submit_button = st.form_submit_button("Optimizar Cajas")

        # --- Lógica de Optimización ---
        if submit_button:
            # Filtramos solo los productos con cantidad > 0
            products_to_optimize = edited_df[edited_df['Cantidad Hoy'] > 0].copy()
            
            if products_to_optimize.empty:
                st.error("No has introducido ningún producto.")
            else:
                st.success("Calculando la solución óptima...")
                
                # Renombramos columnas para que coincidan con el modelo
                products_to_optimize.rename(columns={
                    'Cantidad Hoy': 'Quantity',
                    'Caduca Hoy': 'Expires Today'
                }, inplace=True)

                try:
                    boxes, net_loss, status = solve_box_problem(
                        products_to_optimize,
                        box_retail_min,
                        box_sale_price,
                        max_boxes
                    )
                    
                    st.header("Resultados de la Optimización")
                    
                    if status == "Infeasible":
                        st.error("No se encontró una solución. Es posible que no se puedan cumplir las reglas (ej. no hay suficientes productos para alcanzar el valor retail mínimo).")
                    
                    elif status == "Optimal":
                        st.subheader(f"✅ ¡Solución Óptima Encontrada!")
                        
                        col1, col2 = st.columns(2)
                        col1.metric("Pérdida Neta Total", f"€{net_loss:.2f}")
                        col2.metric("Nº de Cajas Creadas", len(boxes))
                        
                        st.subheader("Composición de las Cajas Recomendadas:")
                        
                        if not boxes:
                            st.warning("No se ha creado ninguna caja. Es probable que no fuera rentable o necesario.")
                        
                        for i, box in enumerate(boxes):
                            box_cost = box['Total Cost']
                            box_value = box['Total Retail Value']
                            box_net = box_cost - box_sale_price
                            
                            with st.expander(f"📦 Caja {i+1} | Valor: €{box_value:.2f} | Coste: €{box_cost:.2f} | Pérdida Neta: €{box_net:.2f}"):
                                st.dataframe(box['Items'], hide_index=True, width="stretch")
                    
                    else:
                        st.warning("El optimizador no pudo encontrar una solución óptima (estado: {status}).")

                except Exception as e:
                    st.error(f"Ha ocurrido un error durante la optimización: {e}")


# ----------------------------------------------------------------------
# PESTAÑA 2: Gestionar Catálogo (Admin)
# ----------------------------------------------------------------------
with tab_admin:
    st.header("Añadir un nuevo producto al catálogo")
    
    # Formulario para añadir nuevos productos
    with st.form("add_product_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre del Producto")
            coste = st.number_input("Coste (€)", min_value=0.0, step=0.01, format="%.2f")
        with col2:
            precio_retail = st.number_input("Precio Retail (€)", min_value=0.0, step=0.01, format="%.2f")
            permite_repetir = st.checkbox("Permite Repetir en la misma caja?", value=True)
        
        submitted_add = st.form_submit_button("Añadir Producto")
        
        if submitted_add:
            if not nombre:
                st.error("El nombre del producto no puede estar vacío.")
            else:
                new_product_data = {
                    "Nombre": nombre,
                    "Coste (€)": coste,
                    "Precio Retail (€)": precio_retail,
                    "Permite Repetir?": permite_repetir
                }
                try:
                    db_manager.add_product(db, new_product_data)
                    st.success(f"¡Producto '{nombre}' añadido con éxito!")
                except Exception as e:
                    st.error(f"Error al añadir producto: {e}")

    st.divider()
    
    st.header("Catálogo de Productos Actual")
    
    # Cargar y mostrar el catálogo actual
    try:
        current_catalog_df = db_manager.get_catalog_df(db)
        
        if current_catalog_df.empty:
            st.info("Aún no hay productos en tu catálogo.")
        else:
            st.dataframe(current_catalog_df, hide_index=True, width="stretch",
                         column_config={"id": None}) # Ocultamos el ID en la vista

            st.subheader("Eliminar un producto")
            # Creamos un selector con los nombres de los productos
            product_names = current_catalog_df['Nombre'].tolist()
            product_ids = current_catalog_df['id'].tolist()
            
            # Mapeo de Nombre a ID
            name_to_id_map = {name: id for name, id in zip(product_names, product_ids)}
            
            product_to_delete = st.selectbox("Selecciona un producto para eliminar", options=[""] + product_names)
            
            if st.button("Eliminar Producto Seleccionado", type="primary"):
                if not product_to_delete:
                    st.warning("Por favor, selecciona un producto.")
                else:
                    try:
                        product_id_to_delete = name_to_id_map[product_to_delete]
                        db_manager.delete_product(db, product_id_to_delete)
                        st.success(f"¡Producto '{product_to_delete}' eliminado!")
                        # Forzamos un refresco de la app para que la lista se actualice
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al eliminar producto: {e}")
    
    except Exception as e:
        st.error(f"Error al cargar el catálogo para la vista de admin: {e}")