# sunshine_processor.py (Versión Corregida Final)
# coding: utf-8
import pandas as pd
from validator import (
    convertir_a_entero, convertir_a_fecha_str, convertir_a_booleano,
    validar_codigo_dian, validar_texto_simple, registrar_error
)

MAPEO_SUNSHINE_API = {
    "Sueldo básico": {"path": "trabajador.sueldo", "type": "integer", "required": True},
    "Tipo de documento": {"path": "trabajador.tipoDocumento", "type": "code", "code_type": "TipoDocumento", "required": True},
    "Nro. de documento": {"path": "trabajador.numeroDocumento", "type": "string", "required": True},
    "Primer apellido trabajador": {"path": "trabajador.primerApellido", "type": "string", "required": True},
    "Tipo trabajador": {"path": "trabajador.tipoTrabajador", "type": "code", "code_type": "TipoTrabajador", "required": True},
    "Subtipo trabajador": {"path": "trabajador.subTipoTrabajador", "type": "code", "code_type": "SubTipoTrabajador", "required": True},
    "Total devengos": {"path": "trabajador.devengadosTotal", "type": "integer", "required": True},
    "Total deducciones": {"path": "trabajador.deduccionesTotal", "type": "integer", "required": True},
    "Comprobante total": {"path": "trabajador.comprobanteTotal", "type": "integer", "required": True},
}

# Reemplaza la vieja función set_nested_value con esta
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

def procesar(rutas_archivos):
    print("[sunshine_processor] Iniciando procesamiento...")
    def get_file_path(rutas, keyword): return next((k for k in rutas if keyword in k.lower()), None)
    
    nombre_archivo_principal = get_file_path(rutas_archivos, 'ne_aliados')
    if not nombre_archivo_principal: return [], [{'mensaje': 'Falta el archivo principal NE_ALIADOS.xlsx'}]
        
    try:
        df_principal = pd.read_excel(rutas_archivos[nombre_archivo_principal], dtype=str)
        columna_llave = 'Nro. de documento'
        if columna_llave not in df_principal.columns: return [], [{'mensaje': f"La columna '{columna_llave}' no se encontró."}]
        print(f"[sunshine_processor] Leído archivo principal: {len(df_principal)} empleados.")
        
        lista_errores_validacion = []
        lista_empleados_procesados = []
        
        for idx, empleado_row in df_principal.iterrows():
            errores_empleado_actual = []
            datos_empleado_api = {}
            for col_excel, api_info in MAPEO_SUNSHINE_API.items():
                valor_original = empleado_row.get(col_excel)
                is_required = api_info.get('required', False)
                data_type = api_info['type']
                
                if data_type == 'integer': convertir_a_entero(valor_original, errores_empleado_actual, idx, col_excel, es_obligatorio=is_required)
                elif data_type == 'code': validar_codigo_dian(valor_original, api_info.get('code_type'), errores_empleado_actual, idx, col_excel, es_obligatorio=is_required)
                else: validar_texto_simple(valor_original, errores_empleado_actual, idx, col_excel, es_obligatorio=is_required)
            
            if errores_empleado_actual:
                for error in errores_empleado_actual:
                    error['nombre_archivo'] = nombre_archivo_principal
                lista_errores_validacion.extend(errores_empleado_actual)
            else:
                for col_excel, api_info in MAPEO_SUNSHINE_API.items():
                    valor_original = empleado_row.get(col_excel)
                    is_required = api_info.get('required', False)
                    data_type = api_info['type']
                    valor_procesado = None
                    if data_type == 'integer': valor_procesado = convertir_a_entero(valor_original, [], idx, col_excel, es_obligatorio=is_required)
                    elif data_type == 'code': valor_procesado = validar_codigo_dian(valor_original, api_info.get('code_type'), [], idx, col_excel, es_obligatorio=is_required)
                    else: valor_procesado = validar_texto_simple(valor_original, [], idx, col_excel, es_obligatorio=is_required)
                    if valor_procesado is not None:
                        set_nested_value(datos_empleado_api, api_info['path'], valor_procesado)
                lista_empleados_procesados.append({'trabajador': datos_empleado_api.get('trabajador', {})})

        print("[sunshine_processor] ¡Validación completada!")
        return lista_empleados_procesados, lista_errores_validacion
        
    except Exception as e:
        return [], [{'mensaje': f'Error crítico: {e}'}]
