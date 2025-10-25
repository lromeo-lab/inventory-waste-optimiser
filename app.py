import streamlit as st
import pandas as pd
from model import solve_box_problem


# --- 1. Configuración de la Página y Título ---
st.set_page_config(page_title="Optimizador TGTG", layout="wide")
st.title("📦 Optimizador de Cajas 'Too Good To Go'")
st.write("Esta app te ayuda a decidir la composición óptima de tus cajas para minimizar pérdidas.")

# --- 2. Gestión del Estado (Catálogo de Productos) ---
# Usamos st.session_state para guardar el catálogo de productos
# entre ejecuciones de la app.

if 'product_catalog' not in st.session_state:
    # Si es la primera vez que se carga, creamos un catálogo de ejemplo
    st.session_state.product_catalog = [
        {"Product Name": "Croissant", "Retail Price": 2.50, "Purchase Cost": 0.80, "Allow Repeats?": True},
        {"Product Name": "Napolitana Choc.", "Retail Price": 2.80, "Purchase Cost": 1.00, "Allow Repeats?": True},
        {"Product Name": "Palmera", "Retail Price": 3.00, "Purchase Cost": 1.10, "Allow Repeats?": False},
        {"Product Name": "Sandwich Jamón", "Retail Price": 4.50, "Purchase Cost": 2.20, "Allow Repeats?": False},
        {"Product Name": "Cookie", "Retail Price": 2.00, "Purchase Cost": 0.50, "Allow Repeats?": True},
    ]

# --- 3. Definición de las Pestañas (UX) ---
tab_optimizar, tab_catalogo = st.tabs(["🛒 Optimizar Cajas (Diario)", "📚 Gestionar Catálogo (Admin)"])


# --- PESTAÑA 1: OPTIMIZAR (Uso Diario) ---
with tab_optimizar:
    st.header("Paso 1: Define las reglas del día")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        precio_caja = st.number_input("Precio de Venta de la Caja (€)", min_value=0.1, value=4.0, step=0.1)
    with col2:
        valor_minimo = st.number_input("Valor Retail Mínimo (€)", min_value=0.1, value=12.0, step=0.1)
    with col3:
        max_cajas = st.number_input("Nº Máximo de Cajas a crear", min_value=1, value=5, step=1)

    st.header("Paso 2: Introduce tu inventario de hoy")
    st.info("Rellena solo las cantidades de los productos que tienes hoy. Marca los que caducan.")

    # Convertir el catálogo (lista de dicts) a un DataFrame para el editor
    if not st.session_state.product_catalog:
        st.error("Tu catálogo de productos está vacío. Ve a la pestaña 'Gestionar Catálogo' para añadir productos.")
    else:
        df_catalogo = pd.DataFrame(st.session_state.product_catalog)
        
        # Añadir las columnas de 'día a día'
        df_catalogo["Quantity"] = 0
        df_catalogo["Expires Today?"] = False
        
        # Reordenar las columnas para una mejor UX
        column_order = [
            "Quantity", 
            "Expires Today?", 
            "Product Name", 
            "Retail Price", 
            "Purchase Cost", 
            "Allow Repeats?"
        ]
        
        # Usar st.data_editor para una interfaz tipo Excel
        edited_inventory_df = st.data_editor(
            df_catalogo[column_order],
            column_config={
                "Quantity": st.column_config.NumberColumn("Cantidad Hoy", min_value=0),
                "Expires Today?": st.column_config.CheckboxColumn("Caduca Hoy?"),
                "Product Name": st.column_config.TextColumn("Producto", disabled=True),
                "Retail Price": st.column_config.NumberColumn("Precio Retail", format="€%.2f", disabled=True),
                "Purchase Cost": st.column_config.NumberColumn("Coste", format="€%.2f", disabled=True),
                "Allow Repeats?": st.column_config.CheckboxColumn("Permite Repetir?", disabled=True),
            },
            hide_index=True,
            # --- CAMBIO AQUÍ ---
            width='stretch' # Reemplaza a use_container_width=True
        )

        st.header("Paso 3: ¡Optimizar!")
        st.write("Haz clic aquí para calcular el plan de cajas óptimo.")

        # --- CAMBIO AQUÍ ---
        if st.button("GENERAR PLAN DE CAJAS ÓPTIMO", type="primary", width='stretch'): # Reemplaza a use_container_width=True
            with st.spinner("Calculando la mejor combinación..."):
                # 1. Filtrar solo los productos con cantidad > 0
                df_to_solve = edited_inventory_df[edited_inventory_df["Quantity"] > 0].copy()

                if df_to_solve.empty:
                    st.warning("No has introducido cantidad para ningún producto.")
                elif df_to_solve["Expires Today?"].sum() == 0 and df_to_solve["Quantity"].sum() > 0:
                     st.warning("No has marcado ningún producto como 'Caduca Hoy?'. El optimizador no tiene nada que 'salvar' obligatoriamente. Añade productos que caduquen o revisa tu inventario.")
                else:
                    # 2. Llamar al optimizador (¡ahora importado desde model.py!)
                    boxes, net_loss, status = solve_box_problem(
                        df_to_solve,
                        valor_minimo,
                        precio_caja,
                        max_cajas
                    )

                    # 3. Mostrar resultados
                    if status == "Optimal":
                        st.success("¡Plan Óptimo Encontrado!")
                        
                        total_boxes = len(boxes)
                        total_revenue = total_boxes * precio_caja
                        total_cost = total_revenue + net_loss
                        
                        st.subheader("Resumen de la Operación")
                        res_col1, res_col2, res_col3 = st.columns(3)
                        res_col1.metric("Pérdida Neta Total", f"€{net_loss:.2f}")
                        res_col2.metric("Cajas Creadas", f"{total_boxes}")
                        res_col3.metric("Ingresos Totales", f"€{total_revenue:.2f}")
                        
                        st.subheader("Composición de Cajas Recomendada")
                        if not boxes:
                             st.info("La solución óptima es no crear ninguna caja (probablemente la pérdida era menor no vendiendo).")
                        
                        for box_name, data in boxes.items():
                            with st.container(border=True):
                                st.subheader(f"📦 {box_name}")
                                b_col1, b_col2, b_col3 = st.columns(3)
                                b_col1.metric("Valor Retail", f"€{data['Total Retail Value']:.2f}")
                                b_col2.metric("Coste Productos", f"€{data['Total Purchase Cost']:.2f}")
                                b_col3.metric("Resultado Caja", f"€{data['Net for Box']:.2f}", 
                                               help="Ingreso (€4.00) - Coste de Productos")
                                
                                st.markdown("**Contenido:**")
                                for item in data['Items']:
                                    st.markdown(f"- {item}")
                                    
                    elif status == "Infeasible":
                         st.error("No se ha podido encontrar una solución. Es 'Inviable'.")
                         st.write("Esto suele pasar si es imposible cumplir las reglas. Por ejemplo:")
                         st.write("- Tienes demasiados productos que caducan pero no caben en las cajas máximas.")
                         st.write("- Los productos que caducan no pueden combinarse para alcanzar el valor retail mínimo de 12€.")
                         st.write("- Prueba a aumentar el 'Nº Máximo de Cajas' o añade más productos de relleno.")
                    else:
                        st.error(f"No se pudo encontrar una solución óptima. Estado: {status}")


# --- PESTAÑA 2: GESTIONAR CATÁLOGO (Admin) ---
with tab_catalogo:
    st.header("Gestionar Catálogo de Productos")
    st.write("Aquí puedes añadir o eliminar productos de tu lista 'maestra'.")
    st.write("Estos productos aparecerán en la pestaña 'Optimizar Cajas' cada día.")

    # --- Formulario para Añadir Productos ---
    st.subheader("Añadir Nuevo Producto")
    with st.form("nuevo_producto_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            prod_name = st.text_input("Nombre del Producto")
            prod_retail = st.number_input("Precio Retail (€)", min_value=0.0, step=0.1)
        with col2:
            prod_cost = st.number_input("Coste de Compra (€)", min_value=0.0, step=0.1)
            prod_repeats = st.checkbox("Permitir repetir en una caja?", value=True)
        
        submitted = st.form_submit_button("Añadir Producto al Catálogo")
        if submitted:
            if prod_name:
                new_product = {
                    "Product Name": prod_name,
                    "Retail Price": prod_retail,
                    "Purchase Cost": prod_cost,
                    "Allow Repeats?": prod_repeats
                }
                st.session_state.product_catalog.append(new_product)
                st.success(f"¡Producto '{prod_name}' añadido!")
            else:
                st.error("El nombre del producto no puede estar vacío.")

    st.divider()

    # --- Ver y Eliminar Productos ---
    st.subheader("Catálogo Actual")
    
    if not st.session_state.product_catalog:
        st.info("Aún no hay productos en tu catálogo.")
    else:
        # Convertir a DataFrame para mostrarlo
        catalog_df = pd.DataFrame(st.session_state.product_catalog)
        st.dataframe(catalog_df, width='stretch', hide_index=True)

        # Lógica para Eliminar
        st.subheader("Eliminar un Producto")
        products_names = [p["Product Name"] for p in st.session_state.product_catalog]
        product_to_delete = st.selectbox("Selecciona un producto para eliminar", options=products_names, index=None, placeholder="Elige un producto...")

        if st.button("Eliminar Producto Seleccionado", type="secondary"):
            if product_to_delete:
                # Encontrar y eliminar el producto
                st.session_state.product_catalog = [p for p in st.session_state.product_catalog if p["Product Name"] != product_to_delete]
                st.success(f"Producto '{product_to_delete}' eliminado.")
                st.rerun() # Recargar la app para actualizar la lista
            else:
                st.warning("Por favor, selecciona un producto de la lista para eliminar.")