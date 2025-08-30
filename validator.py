# validator.py
# coding: utf-8
import pandas as pd
from datetime import datetime

# --- Listas de Códigos DIAN Válidos ---
# ¡¡MUY IMPORTANTE!! REVISAR Y COMPLETAR ESTAS LISTAS SEGÚN ANEXOS TÉCNICOS OFICIALES DE LA DIAN.
# Fuentes principales: Resolución 000013 de 11-02-2021 y su Anexo Técnico v1.0.

CODIGOS_TIPO_DOCUMENTO = [ # Tabla 5.2.1 Anexo Técnico v1.0 (p.120 Anexo / PDF p.150)
    '11', # Registro civil
    '12', # Tarjeta de identidad
    '13', # Cédula de ciudadanía
    '21', # Tarjeta de extranjería
    '22', # Cédula de extranjería
    '31', # NIT
    '41', # Pasaporte
    '42', # Documento de identificación extranjero
    '47', # PEP
    '50', # NIT de otro país
	    '91'  # NUIP * (Solo para empleado)
    # La API de Aportes en Línea también menciona '48' (PPT) en su doc. Añadir si es necesario.
]
CODIGOS_TIPO_TRABAJADOR = [ # Tabla 5.5.3 Anexo Técnico v1.0 (p.179 Anexo / PDF p.209)
    '01', # Dependiente
    '02', # Servicio domestico
    '04', # Madre comunitaria
    '12', # Aprendices del Sena en etapa lectiva
    '18', # Funcionarios públicos sin tope máximo de ibc
    '19', # Aprendices del SENA en etapa productiva
    '21', # Estudiantes de postgrado en salud
    '22', # Profesor de establecimiento particular
    '23', # Estudiantes aportes solo riesgos laborales
    '30', # Dependiente entidades o universidades públicas con régimen especial en salud
    '31', # Cooperados o pre cooperativas de trabajo asociado
    '47', # Trabajador dependiente de entidad beneficiaria del sistema general de participaciones - aportes patronales
    '51', # Trabajador de tiempo parcial
    '54', # Pre pensionado de entidad en liquidación.
    '56', # Pre pensionado con aporte voluntario a salud
    '58'  # Estudiantes de prácticas laborales en el sector público
    # El Anexo Técnico v1.0 de la DIAN es más corto aquí que algunas listas generales de PILA.
    # Validar contra los que Aportes en Línea realmente acepte si hay diferencias.
]
CODIGOS_SUBTIPO_TRABAJADOR = [ # Tabla 5.5.4 Anexo Técnico v1.0 (p.179 Anexo / PDF p.209)
    '00', # No Aplica
    '01'  # Dependiente pensionado por vejez activo
]
CODIGOS_TIPO_CONTRATO = [ # Tabla 5.5.2 Anexo Técnico v1.0 (p.179 Anexo / PDF p.209)
    '1', # Termino Fijo
    '2', # Término Indefinido
    '3', # Obra o Labor
    '4', # Aprendizaje
    '5'  # Prácticas o Pasantías
]
CODIGOS_PAIS = [ # Tabla 5.4.1 Anexo Técnico v1.0 (ISO 3166-1 alpha-2)
    'CO' # Para Colombia. Completar si se manejan otros países.
]
CODIGOS_DEPARTAMENTO_ESTADO = [ # Tabla 5.4.2 Anexo Técnico v1.0 (Códigos DANE numéricos, p.143-144 Anexo / PDF p.173-174)
    '05', '08', '11', '13', '15', '17', '18', '19', '20', '23', '25',
    '27', '41', '44', '47', '50', '52', '54', '63', '66', '68', '70',
    '73', '76', '81', '85', '86', '88', '91', '94', '95', '97', '99'
]
# CODIGOS_MUNICIPIO_CIUDAD: Como acordamos, para esta lista tan extensa,
# haremos una validación de formato/longitud y confiaremos en la API.
# No se incluirá una lista completa aquí.

CODIGOS_TIPO_CUENTA = [ # No hay tabla DIAN explícita en Anexo 013. Usamos comunes para API Aportes en Línea.
    'A', # Ahorros
    'C'  # Corriente
    # La API Aportes en Línea podría aceptar el texto "AHORROS", "CORRIENTE". Verificar.
]
CODIGOS_METODO_PAGO = [ # Tabla 5.3.3.2 Anexo Técnico v1.0 (Medios de Pago, p.130-131 Anexo / PDF p.160-161)
    '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19',
    '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35', '36', '37', '38', '39',
    '40', '41', '42', '43', '44', '45', '46', '47', '48', '49', '50', '51', '52', '53', # API Aportes en Línea usa estos
    '60', '61', '62', '63', '64', '65', '66', '67', '70', '71', '72',
    '74', '75', '76', '77', '78', '91', '92', '93', '94', '95', '96', '97', 'ZZZ' # '98' CATS está en Aportes en Línea doc
]
CODIGOS_FORMA_PAGO = [ # Tabla 5.3.3.1 Anexo Técnico v1.0 (Formas de Pago, p.130 Anexo / PDF p.160)
    '1' # Anexo DIAN solo muestra '1' (Contado). API Aportes en Línea podría permitir '2' (Crédito).
        # Mantener '1' por ahora según Anexo estricto, o añadir '2' si Aportes en Línea lo valida.
]
CODIGOS_TIPO_INCAPACIDAD = [ # Tabla 5.5.6 Anexo Técnico v1.0 (Tipo de Incapacidad, p.180 Anexo / PDF p.210)
    '1', # Común
    '2', # Profesional
    '3'  # Laboral
]
CODIGOS_PERIODO_NOMINA = [ # Tabla 5.5.1 Anexo Técnico v1.0 (p.178-179 Anexo / PDF p.208-209)
    '1', # Semanal
    '2', # Decenal
    '3', # Catorcenal
    '4', # Quincenal
    '5', # Mensual
    '6'  # Otro
]
CODIGOS_TIPO_XML = [ # Tabla 5.5.7 Anexo Técnico v1.0 (p.180 Anexo / PDF p.210)
    '102', # NominaIndividual
    '103'  # NominaIndividualDeAjuste
]
CODIGOS_IDIOMA = [ # Tabla 5.3.1 Anexo Técnico v1.0 (ISO 639-1)
    'es' # Español
]
CODIGOS_TIPO_MONEDA = [ # Tabla 5.3.2 Anexo Técnico v1.0 (ISO 4217)
    'COP' # Peso Colombiano
]

# Diccionario para acceder a las listas correctas de códigos
LISTAS_CODIGOS_VALIDOS = {
    "TipoDocumento": CODIGOS_TIPO_DOCUMENTO,
    "TipoTrabajador": CODIGOS_TIPO_TRABAJADOR,
    "SubTipoTrabajador": CODIGOS_SUBTIPO_TRABAJADOR,
    "TipoContrato": CODIGOS_TIPO_CONTRATO,
    "Pais": CODIGOS_PAIS,
    "DepartamentoEstado": CODIGOS_DEPARTAMENTO_ESTADO,
    # "MunicipioCiudad" se valida por formato, no por lista.
    "TipoCuenta": CODIGOS_TIPO_CUENTA,
    "MetodoPago": CODIGOS_METODO_PAGO,
    "FormaPago": CODIGOS_FORMA_PAGO,
    "TipoIncapacidad": CODIGOS_TIPO_INCAPACIDAD,
    "PeriodoNomina": CODIGOS_PERIODO_NOMINA,
    "TipoXML": CODIGOS_TIPO_XML,
    "Idioma": CODIGOS_IDIOMA,
    "TipoMoneda": CODIGOS_TIPO_MONEDA,
}

# --- Funciones de Validación y Conversión ---

def registrar_error(errores_lista, fila_idx, campo_nie, valor, mensaje):
    fila_excel = fila_idx + 2
    errores_lista.append({
        'fila': fila_excel, 'campo_nie': campo_nie,
        'valor_original': str(valor), 'mensaje': mensaje
    })

def convertir_a_entero(valor, errores_lista, fila_idx, campo_nie, es_obligatorio=False):
    """Función robusta para convertir valores de Excel a entero."""
    if pd.isna(valor) or str(valor).strip() == '':
        if es_obligatorio:
            registrar_error(errores_lista, fila_idx, campo_nie, valor, 'Campo numérico obligatorio está vacío.')
        return None
    try:
        valor_str = str(valor).strip()
        return int(float(valor_str))
    except (ValueError, TypeError):
        if es_obligatorio:
            registrar_error(errores_lista, fila_idx, campo_nie, valor, f'Valor "{valor}" no es un número entero válido.')
        return None

def validar_codigo_dian(valor, tipo_codigo, errores_lista, fila_idx, campo_nie, es_obligatorio=False):
    """Valida si el código está en la lista DIAN o si tiene el formato correcto (para Municipio)."""
    if pd.isna(valor) or str(valor).strip() == '':
        if es_obligatorio:
            registrar_error(errores_lista, fila_idx, campo_nie, valor, f'Código obligatorio ({tipo_codigo}) vacío.')
        return None
    
    valor_str = str(valor).strip()
    if '.' in valor_str:
        try:
            num_float = float(valor_str)
            if num_float == int(num_float):
                valor_str = str(int(num_float))
        except (ValueError, TypeError):
            pass

    # Validación especial para MunicipioCiudad: se valida el formato en lugar de una lista.
    if tipo_codigo == "MunicipioCiudad":
        if not valor_str.isdigit():
            registrar_error(errores_lista, fila_idx, campo_nie, valor, f'Código de Municipio "{valor_str}" debe ser numérico.')
            return None
        if len(valor_str) > 5:
            registrar_error(errores_lista, fila_idx, campo_nie, valor, f'Código de Municipio "{valor_str}" no puede tener más de 5 dígitos.')
            return None
        # Normaliza a 5 dígitos (ej: '5001' -> '05001'). Se confía en la API para la validación final.
        return valor_str.zfill(5)

    lista_valida = LISTAS_CODIGOS_VALIDOS.get(tipo_codigo)
    if not lista_valida:
        registrar_error(errores_lista, fila_idx, campo_nie, valor, f'Error interno: No se encontró lista de códigos para {tipo_codigo}.')
        return None
    
    if valor_str not in lista_valida:
        ejemplos_validos = lista_valida[:15]
        registrar_error(errores_lista, fila_idx, campo_nie, valor, f'Código "{valor_str}" inválido para {tipo_codigo}. Valores permitidos: {ejemplos_validos}...')
        return None
    
    return valor_str

def convertir_a_fecha_str(valor, errores_lista, fila_idx, campo_nie, es_obligatorio=False):
    if pd.isna(valor):
        if es_obligatorio: registrar_error(errores_lista, fila_idx, campo_nie, valor, 'Campo de fecha obligatorio está vacío.'); return None
    try:
        return pd.to_datetime(valor).strftime('%Y-%m-%d')
    except (ValueError, TypeError):
        registrar_error(errores_lista, fila_idx, campo_nie, valor, 'Formato de fecha inválido.'); return None

def convertir_a_booleano(valor, errores_lista, fila_idx, campo_nie, es_obligatorio=False):
    if pd.isna(valor):
        if es_obligatorio: registrar_error(errores_lista, fila_idx, campo_nie, valor, 'Campo booleano obligatorio está vacío.'); return None
    valor_str = str(valor).strip().upper()
    if valor_str in ['TRUE', 'VERDADERO', 'SI', 'S', '1', '1.0']: return True
    elif valor_str in ['FALSE', 'FALSO', 'NO', 'N', '0', '0.0']: return False
    else:
        if es_obligatorio: registrar_error(errores_lista, fila_idx, campo_nie, valor, 'Valor no es Verdadero/Falso.'); return None

def validar_texto_simple(valor, errores_lista, fila_idx, campo_nie, es_obligatorio=False, max_longitud=None):
    if pd.isna(valor) or str(valor).strip() == '':
        if es_obligatorio: registrar_error(errores_lista, fila_idx, campo_nie, valor, 'Campo de texto obligatorio está vacío.'); return None
        else: return ""
    valor_str = str(valor).strip()
    if max_longitud is not None and len(valor_str) > max_longitud:
         registrar_error(errores_lista, fila_idx, campo_nie, valor, f'Texto excede longitud máxima de {max_longitud} caracteres.'); return None
    return valor_str

def validar_formato_hora(valor, errores_lista, fila_idx, campo_nie, es_obligatorio=False):
    if pd.isna(valor) or str(valor).strip() == '':
        if es_obligatorio: registrar_error(errores_lista, fila_idx, campo_nie, valor, 'Campo de hora obligatorio vacío.'); return None
    valor_str = str(valor).strip()
    try:
        datetime.strptime(valor_str, '%H:%M:%S'); return valor_str
    except ValueError:
        try:
            datetime.strptime(valor_str, '%H:%M'); return valor_str
        except ValueError:
            registrar_error(errores_lista, fila_idx, campo_nie, valor, 'Formato de hora inválido. Se esperaba HH:MM:SS o HH:MM.'); return None
