# submission_tracker.py (Versión Final y Completa)
# coding: utf-8

from database import db
from models import Envios, ErroresProceso
from datetime import datetime

def iniciar_nuevo_envio(usuario_id, anio, mes):
    """Crea un nuevo Lote Mensual en la base de datos y devuelve el objeto completo."""
    lote = Envios(
        anio_periodo=int(anio),
        mes_periodo=int(mes),
        usuario_id=usuario_id,
        estado_lote='PENDIENTE'
    )
    db.session.add(lote)
    db.session.commit()
    print(f"Nuevo lote creado para {anio}-{mes} con ID: {lote.id}")
    return lote

def actualizar_estado_fuente(lote_id, fuente, nuevo_estado):
    """Actualiza el estado de una fuente de datos específica (Aliados o Sunshine) dentro del lote."""
    # Sintaxis moderna de SQLAlchemy 2.0
    lote = db.session.get(Envios, lote_id)
    if lote:
        if fuente == 'Aliados': lote.estado_aliados = nuevo_estado
        elif fuente == 'Sunshine': lote.estado_sunshine = nuevo_estado
        lote.fecha_actualizacion = datetime.utcnow()
        db.session.commit()

def log_error_validacion(lote_id, fuente_datos, nombre_archivo, fila=None, columna=None, mensaje=None):
    """Registra un error de validación en la base de datos."""
    nuevo_error = ErroresProceso(
        envio_id=lote_id,
        fuente_datos=fuente_datos,
        nombre_archivo=nombre_archivo,
        fila_excel=fila,
        columna_excel=columna,
        mensaje_error=mensaje
    )
    db.session.add(nuevo_error)
    db.session.commit()
