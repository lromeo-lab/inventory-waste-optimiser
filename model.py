import pandas as pd
import pulp


def solve_box_problem(products_df, box_retail_min, box_sale_price, max_boxes):
    """
    Resuelve el problema de optimización de cajas TGTG (v2) usando PuLP.
    
    Esta versión usa correctamente CANTIDADES de producto, no ítems únicos.

    products_df: Un DataFrame de pandas con las columnas:
        'Product Name', 'Retail Price', 'Purchase Cost', 'Expires Today?', 'Quantity'
        'Allow Repeats?' (Booleano)
    box_retail_min: El valor retail mínimo (ej. 12.0)
    box_sale_price: El ingreso por vender una caja (ej. 4.0)
    max_boxes: El número máximo de cajas que estás dispuesto a hacer.
    """
    
    # --- 1. Crear el Problema ---
    prob = pulp.LpProblem("TGTG_Box_Optimization_v2", pulp.LpMinimize)

    # --- 2. Pre-procesar Datos (Parámetros) ---
    products = products_df.to_dict('index')
    product_ids = list(products.keys())
    box_ids = list(range(max_boxes))
    BIG_M = 1000 # Un valor "suficientemente grande"

    # --- 3. Variables de Decisión ---
    
    # x[(i, j)] = La CANTIDAD (Entero) de producto i a poner en la caja j
    x = pulp.LpVariable.dicts("qty_in_box",
                             ((i, j) for i in product_ids for j in box_ids),
                             cat='Integer',
                             lowBound=0)
    
    # y[j] = 1 si la caja j se crea/usa, 0 si no
    y = pulp.LpVariable.dicts("box_used", box_ids, cat='Binary')

    # --- 4. Función Objetivo (Minimizar Pérdida Neta) ---
    # Minimizar: (Coste Total) - (Ingreso Total)
    
    total_cost = pulp.lpSum(products[i]['Purchase Cost'] * x[(i, j)] 
                           for i in product_ids for j in box_ids)
    
    total_revenue = pulp.lpSum(y[j] * box_sale_price for j in box_ids)
    
    prob += total_cost - total_revenue, "Pérdida Neta Total"

    # --- 5. Restricciones ---
    
    for j in box_ids:
        # Restricción 3: Valor Mínimo de la Caja
        # El valor retail total en la caja debe cumplir el mínimo si se usa.
        prob += pulp.lpSum(products[i]['Retail Price'] * x[(i, j)] for i in product_ids) >= box_retail_min * y[j], f"Box_Value_Min_{j}"

        # Restricción 4: Ligar x e y (Big M)
        # El número total de ítems en una caja debe ser 0 si la caja no se usa.
        prob += pulp.lpSum(x[(i, j)] for i in product_ids) <= BIG_M * y[j], f"Link_x_y_{j}"

    for i in product_ids:
        # Restricción 1 y 2: Disponibilidad de Producto
        if products[i]['Expires Today?']:
            # Restricción 1: Ítems que caducan (Obligatorio Vender)
            # La cantidad total usada en TODAS las cajas debe ser IGUAL a la disponible.
            prob += pulp.lpSum(x[(i, j)] for j in box_ids) == products[i]['Quantity'], f"Must_Use_Product_{i}"
        else:
            # Restricción 2: Ítems de "Relleno" (Opcional)
            # La cantidad total usada en TODAS las cajas no puede EXCEDER la disponible.
            prob += pulp.lpSum(x[(i, j)] for j in box_ids) <= products[i]['Quantity'], f"At_Most_Once_Product_{i}"

    # Restricción 6: Regla de "No Repetir"
    for i in product_ids:
        if not products[i]['Allow Repeats?']:
            # Si no se permiten repeticiones, para cada caja...
            for j in box_ids:
                # La cantidad de este ítem i en esta caja j puede ser como máximo 1.
                prob += x[(i, j)] <= 1, f"No_Repeats_{i}_in_{j}"
            
    # --- 6. Resolver el Problema ---
    # Ocultar los logs de la consola en Streamlit
    prob.solve(pulp.PULP_CBC_CMD(msg=False))
    
    # --- 7. Procesar Resultados ---
    status = pulp.LpStatus[prob.status]
    
    if status == 'Optimal':
        boxes = {}
        for j in box_ids:
            if y[j].varValue == 1:
                box_items = []
                total_retail = 0
                total_cost = 0
                for i in product_ids:
                    item_qty = x[(i, j)].varValue
                    if item_qty > 0:
                        item = products[i]
                        box_items.append(f"{item['Product Name']} (Cant: {item_qty:.0f})")
                        total_retail += item['Retail Price'] * item_qty
                        total_cost += item['Purchase Cost'] * item_qty
                
                boxes[f"Caja {j+1}"] = {
                    'Items': box_items,
                    'Total Retail Value': total_retail,
                    'Total Purchase Cost': total_cost,
                    'Net for Box': box_sale_price - total_cost
                }
        
        total_net_loss = pulp.value(prob.objective)
        return boxes, total_net_loss, status
    else:
        # Si no es óptimo, devuelve el estado para mostrar un error
        return None, 0, status