import streamlit as st
import pandas as pd
from model import solve_box_problem 
import db_manager

# ----------------------------------------------------------------------
# APLICACIÓN STREAMLIT
# ----------------------------------------------------------------------

# --- 1. Configuración de la Página y Título ---
st.set_page_config(page_title="Optimizador TGTG", layout="wide")
st.title("📦 Optimizador de Cajas 'Too Good To Go'")
st.write("Esta app te ayuda a decidir la composición óptima de tus cajas para minimizar pérdidas.")

# --- 2. Conexión a la Base de Datos y Carga de Datos ---
try:
    db = db_manager.get_db()
    
    # Usamos una función para cargar/recargar el catálogo
    def load_catalog():
        st.session_state.product_catalog_df = db_manager.get_catalog_df(db)

    # Si el catálogo no está en el estado de la sesión, cárgalo
    if 'product_catalog_df' not in st.session_state:
        load_catalog()

except Exception as e:
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
        box_sale_price = st.number_input("Precio de Venta de la Caja (€)", min_value=0.0, value=4.0, step=0.5, format="%.2f")
    with col2:
        box_retail_min = st.number_input("Valor Retail Mínimo (€)", min_value=0.0, value=12.0, step=1.0, format="%.2f")
    with col3:
        max_boxes = st.number_input("Nº Máximo de Cajas a crear", min_value=1, value=5, step=1)

    st.header("Paso 2: Introduce tu inventario de hoy")
    
    # Esta pestaña ahora se beneficiará del st.rerun() de la Pestaña 2
    if st.session_state.product_catalog_df.empty:
        st.warning("Tu catálogo de productos está vacío. Ve a la pestaña 'Gestionar Catálogo' para añadir productos.")
    else:
        st.info("Rellena solo las cantidades de los productos que tienes hoy. Los productos con 1 día de vida útil se marcan automáticamente.")
        
        # Copiamos el catálogo para editarlo
        daily_df = st.session_state.product_catalog_df.copy()
        
        # Añadimos las columnas 'Cantidad Hoy' y 'Caduca Hoy?'
        daily_df['Cantidad Hoy'] = 0
        
        # Por defecto, 'Caduca Hoy?' es True si Vida Útil es 1
        # Nos aseguramos de que la columna 'Vida Útil (días)' sea numérica y rellenamos NAs
        daily_df['Vida Útil (días)'] = pd.to_numeric(daily_df['Vida Útil (días)'], errors='coerce').fillna(1)
        daily_df['Caduca Hoy?'] = daily_df['Vida Útil (días)'] == 1
        
        # Creamos la tabla editable
        edited_df = st.data_editor(daily_df,
            column_config={
                "id": None, # Ocultamos la columna ID
                "Nombre": st.column_config.TextColumn("Producto", disabled=True),
                "Coste (€)": st.column_config.NumberColumn("Coste", disabled=True, format="€%.2f"),
                "Precio Retail (€)": st.column_config.NumberColumn("Retail", disabled=True, format="€%.2f"),
                "Permite Repetir?": st.column_config.CheckboxColumn("Repetible?", disabled=True),
                "Vida Útil (días)": st.column_config.NumberColumn("Vida Útil", disabled=True, help="Vida útil configurada en el catálogo."),
                # Estas son las únicas columnas editables
                "Cantidad Hoy": st.column_config.NumberColumn("Cantidad Hoy", min_value=0, step=1),
                "Caduca Hoy?": st.column_config.CheckboxColumn("Caduca Hoy?")
            },
            key="daily_editor",
            width='stretch', 
            hide_index=True
        )

        st.header("Paso 3: Calcular Cajas")
        
        if st.button("🚀 Optimizar mis cajas", type="primary", width='stretch'):
            # Filtramos solo los productos con cantidad
            inventory_df = edited_df[edited_df['Cantidad Hoy'] > 0].copy()
            
            if inventory_df.empty:
                st.warning("No has introducido ningún producto.")
            elif not inventory_df['Caduca Hoy?'].any():
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
                        'Caduca Hoy?': 'Expires Today?'
                    }, inplace=True)

                    boxes, total_net_result, status = solve_box_problem(
                        inventory_df,
                        box_retail_min,
                        box_sale_price,
                        max_boxes
                    )

                    if status == 'Optimal':
                        # Actualizado el mensaje de éxito
                        st.success(f"Solución Óptima Encontrada **Resultado Neto Total: €{total_net_result:.2f}**")
                        
                        if not boxes:
                            st.info("La solución óptima es no crear ninguna caja con los productos que caducan.")
                        
                        # LÓGICA DE ORDENACIÓN
                        # Esta lógica ya era correcta (maximizaba el resultado)
                        sorted_boxes = sorted(
                            boxes, 
                            key=lambda b: (box_sale_price - b['Total Cost']), 
                            reverse=True # De más ganancia (menos pérdida) a peor
                        )
                        
                        for i, box in enumerate(sorted_boxes):
                            total_cost = box['Total Cost']
                            net_result = box_sale_price - total_cost
                            
                            box_color = "green" if net_result >= 0 else "red"
                            
                            with st.container(border=True):
                                st.subheader(f"Caja {i+1} (Valor Retail: €{box['Total Retail']:.2f})")
                                st.markdown(f"**Coste Total:** €{total_cost:.2f} | **Venta:** €{box_sale_price:.2f} | **Resultado: <span style='color:{box_color};'>€{net_result:.2f}</span>**", unsafe_allow_html=True)
                                
                                box_df = pd.DataFrame(box['Items'])
                                st.dataframe(box_df, width='stretch', hide_index=True) 

                    else:
                        st.error("No se pudo encontrar una solución óptima. Posibles razones: \n"
                                 "- Es imposible cumplir el valor retail mínimo de €{box_retail_min} con los productos que caducan. \n"
                                 "- Has puesto un número máximo de cajas muy bajo.")

# --- Pestaña 2: Gestión del Catálogo ---
with tab2:
    
    # Comprobamos si la bandera de éxito se activó en el refresco anterior.
    if st.session_state.get("show_catalog_success", False):
        st.success("¡Catálogo actualizado con éxito!", icon="✅")
        # Limpiamos la bandera para que no se muestre de nuevo
        st.session_state.show_catalog_success = False
        
    st.header("Gestionar Catálogo de Productos")
    st.info("Añade, edita o elimina productos directamente en la tabla. Los cambios no se guardan hasta que presiones 'Guardar Cambios'.")

    # --- Iniciamos un formulario ---
    with st.form(key="catalog_form"):
        # --- El editor está DENTRO del formulario ---
        edited_catalog = st.data_editor(
            st.session_state.product_catalog_df,
            column_config={
                "id": None, # Ocultamos la columna ID
                "Nombre": st.column_config.TextColumn("Producto", required=True),
                "Coste (€)": st.column_config.NumberColumn("Coste (€)", min_value=0.0, format="€%.2f", required=True),
                "Precio Retail (€)": st.column_config.NumberColumn("Precio Retail (€)", min_value=0.0, format="€%.2f", required=True),
                "Permite Repetir?": st.column_config.CheckboxColumn("Repetible?"),
                "Vida Útil (días)": st.column_config.NumberColumn(
                    "Vida Útil (días)", 
                    min_value=1, 
                    step=1, 
                    format="%d", 
                    required=True, 
                    help="Vida útil del producto en días. 1 = Caduca hoy."
                )
            },
            num_rows="dynamic", # Permite añadir y eliminar filas
            width='stretch',
            hide_index=True,
            key="catalog_editor"
        )
        
        # --- Usamos st.form_submit_button ---
        submitted = st.form_submit_button(
            "Guardar Cambios en Catálogo", 
            type="primary", 
            width='stretch'
        )

        # --- La lógica se ejecuta solo si el formulario se envía ---
        if submitted:
            try:
                with st.spinner("Guardando cambios en la base de datos..."):
                    original_df = st.session_state.product_catalog_df
                    edited_df = pd.DataFrame(edited_catalog) 
                    
                    # --- Lógica para encontrar cambios ---
                    original_ids = set(original_df['id'].dropna())
                    edited_ids = set(edited_df['id'].dropna())

                    # 1. Filas Añadidas (no tienen 'id' o el 'id' es NaN)
                    added_rows = edited_df[pd.isna(edited_df['id'])]
                    for _, row in added_rows.iterrows():
                        product_data = row.to_dict()
                        if pd.isna(product_data.get('Nombre')) or product_data.get('Nombre') == "":
                            continue 
                        db_manager.add_product(db, product_data)

                    # 2. Filas Eliminadas (IDs en original pero no en editado)
                    deleted_ids = original_ids - edited_ids
                    for product_id in deleted_ids:
                        db_manager.delete_product(db, product_id)

                    # 3. Filas Editadas (IDs en ambos)
                    original_indexed = original_df.set_index('id')
                    edited_indexed = edited_df.dropna(subset=['id']).set_index('id')
                    
                    for product_id in (original_ids & edited_ids):
                        if product_id not in original_indexed.index or product_id not in edited_indexed.index:
                            continue 
                        
                        original_row = original_indexed.loc[product_id]
                        edited_row = edited_indexed.loc[product_id]
                        
                        if not original_row.equals(edited_row):
                            product_data = edited_row.to_dict()
                            db_manager.update_product(db, product_id, product_data)

                # --- CHECK DE GUARDADO EXITOSO ---
                load_catalog()
                st.session_state.show_catalog_success = True
                st.rerun()

            except Exception as e:
                # Si algo falla en el 'try', se muestra este error
                st.error(f"Error al guardar los cambios: {e}")

