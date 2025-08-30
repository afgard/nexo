# file_handler.py (Versión Final con Validación de Periodo de Pago Corregida)
# coding: utf-8

import os
import pandas as pd
from werkzeug.utils import secure_filename
from uuid import uuid4

def validate_and_save_files(files_dict, source_type):
    """
    Guarda los archivos subidos en una carpeta temporal y devuelve sus rutas.
    """
    saved_files_info = []
    errors = []

    if source_type == 'Aliados':
        file_list = [files_dict.get('file_aliados')]
    elif source_type == 'Sunshine':
        file_list = files_dict.getlist('files_sunshine[]')
    else:
        errors.append("Tipo de fuente no válida.")
        return [], errors

    if not any(f and f.filename for f in file_list):
        errors.append(f"No se seleccionó ningún archivo para la fuente {source_type}.")
        return [], errors

    os.makedirs('uploads', exist_ok=True)

    for file in file_list:
        if file and file.filename:
            original_name = secure_filename(file.filename)
            unique_id = uuid4().hex[:8]
            saved_filename = f"{os.path.splitext(original_name)[0]}_{unique_id}{os.path.splitext(original_name)[1]}"
            saved_path = os.path.join('uploads', saved_filename)

            try:
                file.save(saved_path)
                saved_files_info.append({
                    'original_name': original_name,
                    'saved_path': saved_path
                })
            except Exception as e:
                errors.append(f"Error al guardar el archivo '{original_name}': {e}")
                return [], errors

    return saved_files_info, errors


def validar_periodo_archivo(file_path, expected_year, expected_month, source_type):
    """
    Lee un archivo Excel y comprueba que el PERIODO DE PAGO coincide con el esperado.
    """
    print(f"[file_handler] Validando periodo para archivo: {file_path}")
    try:
        df = pd.read_excel(file_path, dtype=str, nrows=5)

        # --- LÓGICA CORREGIDA: Usar columnas de periodo de pago ---
        date_column = None
        if source_type == 'Aliados':
            # Usamos 'Fecha Liquidacion Fin' (NIE005) que es la que define el mes de pago
            date_column = next((col for col in df.columns if 'NIE005' in col), None)
        elif source_type == 'Sunshine':
            # Usamos 'Fecha Fin de Pago'
            date_column = 'Fecha Fin de Pago'

        if not date_column or date_column not in df.columns:
            return f"Error: No se pudo encontrar la columna de fecha de periodo de pago en el archivo {os.path.basename(file_path)}."

        fecha_str = df[date_column].iloc[0]
        fecha_archivo = pd.to_datetime(fecha_str)

        if fecha_archivo.year != expected_year or fecha_archivo.month != expected_month:
            return (f"¡Conflicto de Periodo! El periodo del archivo es ({fecha_archivo.year}-{fecha_archivo.month:02d}), "
                    f"pero el periodo seleccionado en la aplicación es ({expected_year}-{expected_month:02d}).")

        print("[file_handler] El periodo del archivo coincide con el seleccionado.")
        return None

    except Exception as e:
        return f"Error crítico al leer la fecha del archivo {os.path.basename(file_path)}: {e}"
