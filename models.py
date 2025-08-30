# models.py (Versión Final y Completa)
# coding: utf-8

from database import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Envios(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    anio_periodo = db.Column(db.Integer, nullable=False)
    mes_periodo = db.Column(db.Integer, nullable=False)
    estado_lote = db.Column(db.String(50), default='PENDIENTE')
    estado_aliados = db.Column(db.String(50))
    estado_sunshine = db.Column(db.String(50))
    track_id_api = db.Column(db.String(255))
    mensaje_resultado = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, server_default=func.now())
    fecha_actualizacion = db.Column(db.DateTime, onupdate=func.now())
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
class ErroresProceso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    envio_id = db.Column(db.Integer, db.ForeignKey('envios.id'), nullable=False)
    fuente_datos = db.Column(db.String(50))
    nombre_archivo = db.Column(db.String(255)) 
    fila_excel = db.Column(db.Integer)
    columna_excel = db.Column(db.String(255))
    mensaje_error = db.Column(db.Text)

class Configuracion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    clave = db.Column(db.String(100), unique=True, nullable=False)
    valor = db.Column(db.Text, nullable=True)
