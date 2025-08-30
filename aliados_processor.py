# aliados_processor.py (Versión Final Completa y Auditada)
# coding: utf-8

import pandas as pd
import re
from validator import (
    convertir_a_entero,
    convertir_a_fecha_str,
    convertir_a_booleano,
    validar_codigo_dian,
    validar_texto_simple,
    registrar_error,
    validar_formato_hora
)
from utils import set_nested_value

# --- MAPEO COMPLETO (Auditado y Corregido) ---
MAPEO_NIE_API = {
    # --- Bloque de Periodo (dentro de trabajador) ---
    "NIE004": {"path": "trabajador.periodo.fechaLiquidacionInicio", "type": "date", "required": True},
    "NIE005": {"path": "trabajador.periodo.fechaLiquidacionFin", "type": "date", "required": True},
    "NIE008": {"path": "trabajador.periodo.fechaGen", "type": "date", "required": True},
    
    # --- Bloque de Información General del Trabajador (Requeridos) ---
    "NIE002": {"path": "trabajador.fechaIngreso", "type": "date", "required": True},
    "NIE041": {"path": "trabajador.tipoTrabajador", "type": "code", "code_type": "TipoTrabajador", "required": True},
    "NIE042": {"path": "trabajador.subTipoTrabajador", "type": "code", "code_type": "SubTipoTrabajador", "required": True},
    "NIE043": {"path": "trabajador.altoRiesgoPension", "type": "boolean", "required": True},
    "NIE044": {"path": "trabajador.tipoDocumento", "type": "code", "code_type": "TipoDocumento", "required": True},
    "NIE045": {"path": "trabajador.numeroDocumento", "type": "string", "required": True},
    "NIE046": {"path": "trabajador.primerApellido", "type": "string", "required": True},
    "NIE048": {"path": "trabajador.primerNombre", "type": "string", "required": True},
    "NIE050": {"path": "trabajador.lugarTrabajoPais", "type": "code", "code_type": "Pais", "required": True},
    "NIE051": {"path": "trabajador.lugarTrabajoDepartamentoEstado", "type": "code", "code_type": "DepartamentoEstado", "required": True},
    "NIE052": {"path": "trabajador.lugarTrabajoMunicipioCiudad", "type": "code", "code_type": "MunicipioCiudad", "required": True},
    "NIE053": {"path": "trabajador.lugarTrabajoDireccion", "type": "string", "required": True},
    "NIE056": {"path": "trabajador.salarioIntegral", "type": "boolean", "required": True},
    "NIE061": {"path": "trabajador.tipoDeContrato", "type": "code", "code_type": "TipoContrato", "required": True}, # CORREGIDO: tipoDeContrato
    "NIE062": {"path": "trabajador.sueldo", "type": "integer", "required": True},
    # El campo NIE069 (tiempoLaborado) se gestiona manualmente más adelante.
    "NIE203": {"path": "trabajador.fechasPagos.0.fechaPago", "type": "date", "required": True},
    "NIE030": {"path": "trabajador.tipoMoneda", "type": "code", "code_type": "TipoMoneda", "required": True},
    
    # --- AÑADIDO: Bloque de Pago (Requerido) ---
    "NIE064": {"path": "trabajador.pago.forma", "type": "code", "code_type": "FormaPago", "required": True},
    "NIE065": {"path": "trabajador.pago.metodo", "type": "code", "code_type": "MetodoPago", "required": True},
    
    # --- Bloque de Devengados (Requeridos) ---
    # El campo NIE069 (diasTrabajados) también se gestiona manualmente.
    "NIE070": {"path": "trabajador.devengados.basico.sueldoTrabajado", "type": "integer", "required": True},
    
    # --- AÑADIDO: Bloque de Deducciones (Requeridos) ---
    "NIE161": {"path": "trabajador.deducciones.salud.porcentaje", "type": "integer", "required": True},
    "NIE163": {"path": "trabajador.deducciones.salud.deduccion", "type": "integer", "required": True},
    "NIE164": {"path": "trabajador.deducciones.fondoPension.porcentaje", "type": "integer", "required": True},
    "NIE166": {"path": "trabajador.deducciones.fondoPension.deduccion", "type": "integer", "required": True},
    
    # --- Bloque de Totales (Requeridos) ---
    "NIE187": {"path": "trabajador.devengadosTotal", "type": "integer", "required": True},
    "NIE188": {"path": "trabajador.deduccionesTotal", "type": "integer", "required": True},
    "NIE189": {"path": "trabajador.comprobanteTotal", "type": "integer", "required": True},

    # --- Campos Opcionales (No requeridos) ---
    "NIE003": {"path": "trabajador.fechaRetiro", "type": "date", "required": False},
    "NIE009": {"path": "trabajador.codigoTrabajador", "type": "string", "required": False},
    "NIE031": {"path": "trabajador.notas", "type": "string", "required": False},
    "NIE047": {"path": "trabajador.segundoApellido", "type": "string", "required": False},
    "NIE049": {"path": "trabajador.segundoNombre", "type": "string", "required": False},
    # Secciones opcionales que se añaden con lógica en la función procesar
    "NIE125": {"path": "trabajador.devengados.incapacidades.incapacidad.0.cantidad", "type": "integer", "required": False},
    "NIE126": {"path": "trabajador.devengados.incapacidades.incapacidad.0.tipo", "type": "code", "code_type": "TipoIncapacidad", "required": False},
    "NIE127": {"path": "trabajador.devengados.incapacidades.incapacidad.0.pago", "type": "integer", "required": False},
    "NIE146": {"path": "trabajador.devengados.otrosConceptos.otroConcepto.0.descripcionConcepto", "type": "string", "required": False},
    "NIE147": {"path": "trabajador.devengados.otrosConceptos.otroConcepto.0.conceptoS", "type": "integer", "required": False},
    "NIE148": {"path": "trabajador.devengados.otrosConceptos.otroConcepto.0.conceptoNS", "type": "integer", "required": False},
    "NIE175": {"path": "trabajador.deducciones.libranzas.libranza.0.descripcion", "type": "string", "required": False},
    "NIE176": {"path": "trabajador.deducciones.libranzas.libranza.0.deduccion", "type": "integer", "required": False}
}

# Reemplaza la función procesar completa en aliados_processor.py
def procesar(ruta_archivo_aliados):
    print("[aliados_processor] Iniciando procesamiento de: " + ruta_archivo_aliados)
    lista_empleados_procesados = []
    lista_errores_validacion = []
    try:
        df = pd.read_excel(ruta_archivo_aliados, dtype=str)
        column_mapping = { re.match(r"^(NIE\d+)", str(c).strip()).group(1): str(c).strip() for c in df.columns if re.match(r"^(NIE\d+)", str(c).strip()) }

        for idx, row in df.iterrows():
            datos_empleado_api = {}
            errores_empleado_actual = []

            # --- LÓGICA CONDICIONAL INTELIGENTE ---
            inc_cantidad = convertir_a_entero(row.get(column_mapping.get("NIE125")), [], 0, "") or 0
            inc_pago = convertir_a_entero(row.get(column_mapping.get("NIE127")), [], 0, "") or 0
            procesar_incapacidad = inc_cantidad > 0 or inc_pago > 0

            lib_deduccion = convertir_a_entero(row.get(column_mapping.get("NIE176")), [], 0, "") or 0
            procesar_libranza = lib_deduccion > 0

            oc_sal = convertir_a_entero(row.get(column_mapping.get("NIE147")), [], 0, "") or 0
            oc_nosal = convertir_a_entero(row.get(column_mapping.get("NIE148")), [], 0, "") or 0
            procesar_otros_conceptos = oc_sal > 0 or oc_nosal > 0
            
            # --- MANEJO MANUAL DE NIE069 ---
            # Se lee el valor de la columna NIE069 una sola vez
            dias_trabajados_str = row.get(column_mapping.get("NIE069"))
            dias_trabajados_val = convertir_a_entero(dias_trabajados_str, errores_empleado_actual, idx, "NIE069", es_obligatorio=True)
            if dias_trabajados_val is not None:
                # Se asigna a los dos campos requeridos en el JSON final
                set_nested_value(datos_empleado_api, 'trabajador.tiempoLaborado', str(dias_trabajados_val))
                set_nested_value(datos_empleado_api, 'trabajador.devengados.basico.diasTrabajados', dias_trabajados_val)

            # --- Procesamiento del resto del Mapeo ---
            for nie_code, api_info in MAPEO_NIE_API.items():
                is_required = api_info.get("required", False)
                col_name = column_mapping.get(nie_code)
                if not col_name:
                    if is_required: registrar_error(errores_empleado_actual, idx, nie_code, None, f"Campo obligatorio no encontrado.")
                    continue
                valor_original = row.get(col_name)
                if not is_required and (pd.isna(valor_original) or str(valor_original).strip() == ''): continue
                valor_procesado = None
                data_type = api_info["type"]
                if data_type == "integer": valor_procesado = convertir_a_entero(valor_original, errores_empleado_actual, idx, nie_code, es_obligatorio=is_required)
                elif data_type == "date": valor_procesado = convertir_a_fecha_str(valor_original, errores_empleado_actual, idx, nie_code, es_obligatorio=is_required)
                elif data_type == "boolean": valor_procesado = convertir_a_booleano(valor_original, errores_empleado_actual, idx, nie_code, es_obligatorio=is_required)
                elif data_type == "code": valor_procesado = validar_codigo_dian(valor_original, api_info.get("code_type"), errores_empleado_actual, idx, nie_code, es_obligatorio=is_required)
                elif data_type == "string": valor_procesado = validar_texto_simple(valor_original, errores_empleado_actual, idx, nie_code, es_obligatorio=is_required)
                if valor_procesado is not None: set_nested_value(datos_empleado_api, api_info['path'], valor_procesado)

            # --- PROCESAMIENTO CONDICIONAL ---
            if procesar_incapacidad:
                set_nested_value(datos_empleado_api, 'trabajador.devengados.incapacidades.incapacidad.0.cantidad', inc_cantidad)
                set_nested_value(datos_empleado_api, 'trabajador.devengados.incapacidades.incapacidad.0.pago', inc_pago)
                tipo_inc = validar_codigo_dian(row.get(column_mapping.get("NIE126")), "TipoIncapacidad", errores_empleado_actual, idx, "NIE126", es_obligatorio=True)
                if tipo_inc: set_nested_value(datos_empleado_api, 'trabajador.devengados.incapacidades.incapacidad.0.tipo', tipo_inc)

            if procesar_libranza:
                set_nested_value(datos_empleado_api, 'trabajador.deducciones.libranzas.libranza.0.deduccion', lib_deduccion)
                desc_lib = validar_texto_simple(row.get(column_mapping.get("NIE175")), errores_empleado_actual, idx, "NIE175", es_obligatorio=True)
                if desc_lib: set_nested_value(datos_empleado_api, 'trabajador.deducciones.libranzas.libranza.0.descripcion', desc_lib)

            if procesar_otros_conceptos:
                set_nested_value(datos_empleado_api, 'trabajador.devengados.otrosConceptos.otroConcepto.0.conceptoS', oc_sal)
                set_nested_value(datos_empleado_api, 'trabajador.devengados.otrosConceptos.otroConcepto.0.conceptoNS', oc_nosal)
                desc_oc = validar_texto_simple(row.get(column_mapping.get("NIE146")), errores_empleado_actual, idx, "NIE146", es_obligatorio=True)
                if desc_oc: set_nested_value(datos_empleado_api, 'trabajador.devengados.otrosConceptos.otroConcepto.0.descripcionConcepto', desc_oc)

            if not errores_empleado_actual:
                if 'trabajador' in datos_empleado_api:
                    lista_empleados_procesados.append(datos_empleado_api) # MODIFICADO: Se añade el dict completo
            else:
                lista_errores_validacion.extend(errores_empleado_actual)
        
        print(f"[aliados_processor] Procesamiento completado.")
        return lista_empleados_procesados, lista_errores_validacion
    except Exception as e:
        return [], [{'mensaje': f'Error crítico: {e}', 'campo_nie': 'General'}]
