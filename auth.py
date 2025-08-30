# auth.py (Versión Corregida)
# coding: utf-8

from flask import Blueprint, render_template, redirect, url_for, request, flash
from database import db
from models import User
from flask_login import login_user, logout_user, login_required, current_user

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # --- CORREGIDO ---
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            flash('Usuario o contraseña incorrectos.', 'danger')
            return render_template('login.html')

        login_user(user, remember=True)
        flash('¡Inicio de sesión exitoso!', 'success')
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
             # --- CORREGIDO ---
             next_page = url_for('dashboard')
        return redirect(next_page)

    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('auth.login'))
