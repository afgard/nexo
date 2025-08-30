# database.py
# coding: utf-8
from flask_sqlalchemy import SQLAlchemy

# Solo creamos la instancia de la extensión aquí, sin la app todavía
# Otros módulos importarán 'db' desde este archivo.
db = SQLAlchemy()
