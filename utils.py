# utils.py
def set_nested_value(data_dict, path, value):
    """
    Establece un valor en un diccionario anidado, manejando correctamente
    listas basadas en índices numéricos en la ruta.
    """
    keys = iter(path.split('.'))
    current_key = next(keys)
    d = data_dict

    while True:
        try:
            # Miramos la siguiente clave para decidir si la actual es un diccionario o una lista
            next_key = next(keys)

            if next_key.isdigit():
                # La clave actual es una lista. Ej: 'libranza'
                idx = int(next_key)
                # Aseguramos que la lista exista
                list_node = d.setdefault(current_key, [])
                # Aseguramos que el objeto en el índice exista
                while len(list_node) <= idx:
                    list_node.append({})
                # Nos movemos al objeto correcto dentro de la lista
                d = list_node[idx]
                # Consumimos la clave que sigue al índice numérico
                current_key = next(keys)
            else:
                # La clave actual es un diccionario.
                d = d.setdefault(current_key, {})
                current_key = next_key

        except StopIteration:
            # Llegamos al final de la ruta, establecemos el valor en la última clave
            d[current_key] = value
            break
