import pulp
import pandas as pd

# ----------------------------------------------------------------------
# LÓGICA DEL OPTIMIZADOR (v2)
# Esta es la versión que devuelve un diccionario de cajas,
# que es lo que app.py espera.
# ----------------------------------------------------------------------

def solve_box_problem(products_df, box_retail_min, box_sale_price, max_boxes):
    """
    Resuelve el problema de asignación de cajas v2, enfocado en cantidades.
    """
    try:
        # --- 1. Inicialización de Datos ---
        # Convertir el DataFrame a un formato de diccionario más fácil
        products = products_df.to_dict('index')
        # Crear los IDs de los productos (usando el índice del DataFrame)
        product_ids = list(products.keys())
        # Crear los IDs de las cajas (de 0 a max_boxes-1)
        box_ids = list(range(max_boxes))

        # --- 2. Creación del Problema ---
        # Ahora Maximizamos el Resultado Neto.
        prob = pulp.LpProblem("Maximizar_Resultado_Neto", pulp.LpMaximize)

        # --- 3. Definición de Variables --- 
        # x[i][j] = Cantidad (entero) del producto 'i' asignada a la caja 'j'
        x = pulp.LpVariable.dicts("cantidad_producto_caja",
                                 ((i, j) for i in product_ids for j in box_ids),
                                 lowBound=0,
                                 cat='Integer')
        
        # y[j] = 1 si la caja 'j' se usa (y por tanto se vende), 0 si no.
        y = pulp.LpVariable.dicts("caja_usada", box_ids, cat='Binary')

        # --- 4. Función Objetivo ---
        # Queremos maximizar el resultado neto.
        # Resultado Neto = (Ingreso Total de Cajas Vendidas) - (Coste Total de Productos Usados)

        # Coste Total = Suma( Coste[i] * Cantidad[i][j] ) para todos los productos i y cajas j
        total_cost = pulp.lpSum(products[i]['Purchase Cost'] * x[(i, j)]
                               for i in product_ids for j in box_ids)
        
        # Ingreso Total = Suma( PrecioVentaCaja * y[j] ) para todas las cajas j
        total_revenue = pulp.lpSum(y[j] * box_sale_price for j in box_ids)

        # Objetivo: Maximizar (Ingreso - Coste)
        prob += total_revenue - total_cost, "Resultado_Neto_Total"

        # --- 5. Definición de Restricciones ---

        # C1: Restricción de Cantidad (No podemos usar más de lo que tenemos)
        for i in product_ids:
            prob += pulp.lpSum(x[(i, j)] for j in box_ids) <= products[i]['Quantity'], f"Max_Cantidad_Producto_{i}"

        # C2: Productos que Caducan (DEBEMOS usar todos los que caducan)
        for i in product_ids:
            if products[i]['Expires Today?']:
                prob += pulp.lpSum(x[(i, j)] for j in box_ids) == products[i]['Quantity'], f"Usar_Todo_Producto_{i}"

        # C3: Valor Retail Mínimo por Caja (Solo si la caja se usa)
        #  Suma( PrecioRetail[i] * Cantidad[i][j] ) >= ValorMinimo * y[j]
        # (Si y[j]=0, el lado derecho es 0. Si y[j]=1, es ValorMinimo)
        for j in box_ids:
            prob += pulp.lpSum(products[i]['Retail Price'] * x[(i, j)] for i in product_ids) >= box_retail_min * y[j], f"Valor_Minimo_Caja_{j}"

        # C4: No Repetir Productos (Si Allow Repeats? es Falso)
        # La cantidad de ese producto en esa caja no puede ser > 1
        for i in product_ids:
            if not products[i]['Allow Repeats?']:
                for j in box_ids:
                    prob += x[(i, j)] <= 1, f"No_Repetir_Producto_{i}_Caja_{j}"

        # C5: Ligar 'x' con 'y' (No se pueden poner items en una caja no usada)
        # Usamos M (un número grande). Si y[j]=0, la suma de items debe ser 0.
        M = 1000 # Asumimos que nunca pondremos 1000 items en una caja
        for j in box_ids:
            prob += pulp.lpSum(x[(i, j)] for i in product_ids) <= M * y[j], f"Ligar_X_Y_Caja_{j}"

        # --- 6. Resolución del Problema ---
        prob.solve(pulp.PULP_CBC_CMD(msg=False)) # msg=False para silenciar el log

        # --- 7. Extracción de Resultados ---
        status_str = pulp.LpStatus[prob.status]

        if status_str == 'Optimal':
            box_details = []
            
            for j in box_ids:
                # Si la caja j se usó
                if y[j].value() > 0.5:
                    items_in_box = []
                    total_box_cost = 0
                    total_box_retail = 0
                    
                    for i in product_ids:
                        quantity = x[(i, j)].value()
                        # Si se añadió al menos 1 unidad de este producto
                        if quantity > 0:
                            cost = products[i]['Purchase Cost']
                            retail = products[i]['Retail Price']
                            
                            items_in_box.append({
                                'Producto': products[i]['Product Name'],
                                'Cantidad': int(quantity),
                                'Coste Unit.': cost,
                                'Coste Total Prod.': cost * quantity
                            })
                            
                            total_box_cost += cost * quantity
                            total_box_retail += retail * quantity
                    
                    # Añadimos el diccionario de la caja
                    box_details.append({
                        'Box ID': j + 1,
                        'Items': items_in_box,
                        'Total Cost': total_box_cost,
                        'Total Retail': total_box_retail
                    })
            
            # El valor objetivo ahora es el resultado neto (ingreso - coste)
            total_net_result = prob.objective.value()
            return box_details, total_net_result, status_str
        
        else:
            # Si no es óptimo, devolvemos listas vacías y 0
            return [], 0, status_str

    except Exception as e:
        print(f"Error en el optimizador: {e}")
        return [], 0, f"Error: {e}"