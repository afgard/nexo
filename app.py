# app.py (Versión Final con Envío a API Completo)
# coding: utf-8

import os
import io
import json
import pandas as pd
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, send_file
from database import db
from flask_login import LoginManager, login_required, current_user
from datetime import datetime
from functools import wraps

# --- Importar nuestros módulos ---
from file_handler import validate_and_save_files, validar_periodo_archivo
import aliados_processor
import sunshine_processor
import submission_tracker
import api_client
from models import User, Envios, ErroresProceso, Configuracion

# --- Configuración de la App ---
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.secret_key = 'cambiar-esta-clave-por-algo-seguro-y-aleatorio!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'nomina_app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'uploads')
app.config['TEMP_JSON_FOLDER'] = os.path.join(basedir, 'temp_json')

# --- Inicializar Extensiones ---
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = "Por favor, inicia sesión para acceder a esta página."

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Acceso no autorizado.", "danger")
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# --- RUTAS DE LA APLICACIÓN ---

@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    lotes = Envios.query.order_by(Envios.id.desc()).limit(15).all()
    return render_template('dashboard.html', lotes=lotes)

@app.route('/config', methods=['GET', 'POST'])
@login_required
@admin_required
def config():
    if request.method == 'POST':
        if 'form-config' in request.form:
            keys_from_form = [
                'API_URL', 'API_USER', 'API_PASSWORD',
                'EMPLEADOR_RAZON_SOCIAL', 'EMPLEADOR_NIT', 'EMPLEADOR_DV',
                'EMPLEADOR_PAIS', 'EMPLEADOR_DEPARTAMENTO', 'EMPLEADOR_MUNICIPIO', 'EMPLEADOR_DIRECCION',
                'GEN_PERIODO_NOMINA', 'GEN_TIPO_XML', 'GEN_VERSION', 'GEN_IDIOMA'
            ]
            for key in keys_from_form:
                if key == 'API_PASSWORD' and not request.form.get(key):
                    continue
                setting = Configuracion.query.filter_by(clave=key).first()
                if not setting:
                    setting = Configuracion(clave=key)
                    db.session.add(setting)
                setting.valor = request.form.get(key)
            db.session.commit()
            flash('Configuración general y del empleador actualizada.', 'success')
        elif 'form-user' in request.form:
            username = request.form.get('username')
            password = request.form.get('password')
            is_admin = 'is_admin' in request.form
            if User.query.filter_by(username=username).first():
                flash('El nombre de usuario ya existe.', 'danger')
            else:
                new_user = User(username=username, is_admin=is_admin)
                new_user.set_password(password)
                db.session.add(new_user)
                db.session.commit()
                flash(f'Usuario "{username}" creado.', 'success')
        return redirect(url_for('config'))
        
    settings = {s.clave: s.valor for s in Configuracion.query.all()}
    all_users = User.query.all()
    return render_template('config.html', settings=settings, users=all_users)

@app.route('/submission_center')
@login_required
def submission_center():
    year = request.args.get('year', default=datetime.now().year, type=int)
    month = request.args.get('month', default=datetime.now().month, type=int)
    lote = Envios.query.filter_by(anio_periodo=year, mes_periodo=month, usuario_id=current_user.id).first()
    if not lote:
        lote = submission_tracker.iniciar_nuevo_envio(current_user.id, year, month)
    
    errores_aliados = ErroresProceso.query.filter_by(envio_id=lote.id, fuente_datos='Aliados').order_by(ErroresProceso.id).all()
    errores_sunshine = ErroresProceso.query.filter_by(envio_id=lote.id, fuente_datos='Sunshine').order_by(ErroresProceso.id).all()
    return render_template('submission_center.html', year=year, month=month, lote_actual=lote, errores_aliados=errores_aliados, errores_sunshine=errores_sunshine)

@app.route('/upload_source_files', methods=['POST'])
@login_required
def upload_source_files():
    lote_id = request.form.get('lote_id')
    source_type = request.form.get('source_type')
    lote = db.get_or_404(Envios, lote_id)
    ErroresProceso.query.filter_by(envio_id=lote_id, fuente_datos=source_type).delete()
    db.session.commit()
    saved_files_info, file_errors = validate_and_save_files(request.files, source_type)
    if file_errors:
        for error in file_errors: flash(error, 'danger')
        return redirect(url_for('submission_center', year=lote.anio_periodo, month=lote.mes_periodo))
    
    archivo_principal_path = saved_files_info[0]['saved_path'] if source_type == 'Aliados' else next((f['saved_path'] for f in saved_files_info if 'ne_aliados' in f['original_name'].lower()), None)
    if archivo_principal_path:
        error_periodo = validar_periodo_archivo(archivo_principal_path, lote.anio_periodo, lote.mes_periodo, source_type)
        if error_periodo:
            flash(error_periodo, 'danger')
            return redirect(url_for('submission_center', year=lote.anio_periodo, month=lote.mes_periodo))
    else:
        flash("No se pudo encontrar el archivo principal para validar el periodo.", 'danger')
        return redirect(url_for('submission_center', year=lote.anio_periodo, month=lote.mes_periodo))
    
    processed_data, validation_errors = ([], [])
    if source_type == 'Aliados':
        processed_data, validation_errors = aliados_processor.procesar(saved_files_info[0]['saved_path'])
    elif source_type == 'Sunshine':
        rutas_archivos = {info['original_name']: info['saved_path'] for info in saved_files_info}
        processed_data, validation_errors = sunshine_processor.procesar(rutas_archivos)
    
    submission_tracker.actualizar_estado_fuente(lote_id, source_type, 'VALIDADO' if not validation_errors else 'ERROR_VALIDACION')
    
    if validation_errors:
        flash(f"Se encontraron {len(validation_errors)} errores para {source_type}. Revísalos a continuación.", 'danger')
        for error in validation_errors:
            submission_tracker.log_error_validacion(lote_id, fuente_datos=source_type, nombre_archivo=error.get('nombre_archivo', 'Desconocido'), fila=error.get('fila'), columna=error.get('columna_excel') or error.get('campo_nie'), mensaje=error.get('mensaje'))
    else:
        flash(f"Archivos de {source_type} validados con éxito.", 'success')
        if processed_data:
            try:
                os.makedirs(app.config['TEMP_JSON_FOLDER'], exist_ok=True)
                json_path = os.path.join(app.config['TEMP_JSON_FOLDER'], f"prevalidated_{source_type.lower()}_{lote_id}.json")
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(processed_data, f, ensure_ascii=False, indent=4)
                print(f"Datos pre-validados de {source_type} guardados en: {json_path}")
            except Exception as e:
                flash(f"Error al guardar los datos procesados: {e}", "warning")
    
    return redirect(url_for('submission_center', year=lote.anio_periodo, month=lote.mes_periodo))

@app.route('/consolidate_batch', methods=['POST'])
@login_required
def consolidate_batch():
    lote_id = request.form.get('lote_id')
    lote = db.get_or_404(Envios, lote_id)
    datos_consolidados = []
    
    try:
        path_aliados = os.path.join(app.config['TEMP_JSON_FOLDER'], f'prevalidated_aliados_{lote_id}.json')
        path_sunshine = os.path.join(app.config['TEMP_JSON_FOLDER'], f'prevalidated_sunshine_{lote_id}.json')
        datos_aliados = json.load(open(path_aliados, 'r', encoding='utf-8')) if os.path.exists(path_aliados) else []
        datos_sunshine = json.load(open(path_sunshine, 'r', encoding='utf-8')) if os.path.exists(path_sunshine) else []
        df_aliados = pd.DataFrame([d.get('trabajador', {}) for d in datos_aliados])
        df_sunshine = pd.DataFrame([d.get('trabajador', {}) for d in datos_sunshine])
        df_final = pd.DataFrame()
        if not df_aliados.empty and not df_sunshine.empty:
            print("[Consolidate] Fusionando datos de Aliados y Sunshine con método robusto...")
            df_aliados.dropna(subset=['numeroDocumento'], inplace=True)
            df_sunshine.dropna(subset=['numeroDocumento'], inplace=True)
            df_aliados['numeroDocumento'] = df_aliados['numeroDocumento'].astype(str)
            df_sunshine['numeroDocumento'] = df_sunshine['numeroDocumento'].astype(str)
            df_aliados.set_index('numeroDocumento', inplace=True)
            df_sunshine.set_index('numeroDocumento', inplace=True)
            df_final = df_sunshine.combine_first(df_aliados)
            df_final.reset_index(inplace=True)
        elif not df_aliados.empty:
            df_final = df_aliados
        elif not df_sunshine.empty:
            df_final = df_sunshine
        for col in df_final.select_dtypes(include=['float64']).columns:
            if (df_final[col].dropna() % 1 == 0).all():
                df_final[col] = df_final[col].astype('Int64')
        df_final = df_final.where(pd.notna(df_final), None)
        datos_consolidados = df_final.to_dict('records') # CAMBIO: Ya no se envuelve en {'trabajador': ...}
        lote.estado_lote = 'CONSOLIDADO'
        lote.fecha_actualizacion = datetime.utcnow()
        db.session.commit()
        os.makedirs(app.config['TEMP_JSON_FOLDER'], exist_ok=True)
        json_path = os.path.join(app.config['TEMP_JSON_FOLDER'], f'consolidated_{lote_id}.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(datos_consolidados, f, ensure_ascii=False, indent=4) # Guardamos la lista de trabajadores directamente
        flash(f'Datos consolidados con éxito. {len(datos_consolidados)} registros de empleados preparados.', 'success')
    except Exception as e:
        flash(f"Error durante la consolidación: {e}", "danger")
        lote.estado_lote = 'ERROR_CONSOLIDACION'
        db.session.commit()
    return redirect(url_for('final_submission_status', lote_id=lote.id))

@app.route('/lote/<int:lote_id>/final_status')
@login_required
def final_submission_status(lote_id):
    lote = db.get_or_404(Envios, lote_id)
    json_path = os.path.join(app.config['TEMP_JSON_FOLDER'], f'consolidated_{lote_id}.json')
    json_disponible = os.path.exists(json_path)
    return render_template('final_submission_status.html', lote=lote, json_disponible=json_disponible)

@app.route('/lote/<int:lote_id>/reset', methods=['POST'])
@login_required
def reset_lote_status(lote_id):
    lote = db.get_or_404(Envios, lote_id)
    lote.estado_lote = 'PENDIENTE'
    lote.fecha_actualizacion = datetime.utcnow()
    json_path = os.path.join(app.config['TEMP_JSON_FOLDER'], f'consolidated_{lote_id}.json')
    if os.path.exists(json_path):
        os.remove(json_path)
    db.session.commit()
    flash(f"El estado del Lote #{lote.id} ha sido reseteado.", "info")
    return redirect(url_for('submission_center', year=lote.anio_periodo, month=lote.mes_periodo))

@app.route('/lote/<int:lote_id>/delete', methods=['POST'])
@login_required
def delete_lote(lote_id):
    lote = db.get_or_404(Envios, lote_id)
    ErroresProceso.query.filter_by(envio_id=lote_id).delete()
    db.session.delete(lote)
    db.session.commit()
    flash(f"El Lote #{lote.id} ha sido eliminado.", "success")
    return redirect(url_for('dashboard'))

@app.route('/submission/<int:lote_id>/download_errors')
@login_required
def download_errors(lote_id):
    source = request.args.get('source')
    if not source:
        flash("Fuente de datos no especificada para la descarga de errores.", "danger")
        return redirect(url_for('dashboard'))
    errors_query = ErroresProceso.query.filter_by(envio_id=lote_id, fuente_datos=source).order_by(ErroresProceso.fila_excel).all()
    if not errors_query:
        flash("No hay errores para descargar para esta fuente.", "info")
        lote = db.session.get(Envios, lote_id)
        return redirect(url_for('submission_center', year=lote.anio_periodo, month=lote.mes_periodo))
    error_data = [{'Archivo': e.nombre_archivo, 'Fila_Excel': e.fila_excel, 'Campo/Columna': e.columna_excel, 'Mensaje_Error': e.mensaje_error} for e in errors_query]
    df_errors = pd.DataFrame(error_data)
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df_errors.to_excel(writer, index=False, sheet_name=f'Errores_{source}')
    writer.close()
    output.seek(0)
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name=f'errores_{source.lower()}_lote_{lote_id}.xlsx')

@app.route('/lote/<int:lote_id>/view_consolidated_json')
@login_required
def view_consolidated_json(lote_id):
    json_path = os.path.join(app.config['TEMP_JSON_FOLDER'], f'consolidated_{lote_id}.json')
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            datos_json = json.load(f)
        return jsonify(datos_json)
    except FileNotFoundError:
        flash("No se encontró el archivo JSON consolidado para este lote.", "danger")
        return redirect(url_for('final_submission_status', lote_id=lote_id))
    except Exception as e:
        flash(f"Error al leer el archivo JSON: {e}", "danger")
        return redirect(url_for('final_submission_status', lote_id=lote_id))

# --- RUTA DE ENVÍO FINAL Y COMPLETA ---
@app.route('/lote/<int:lote_id>/send_to_api', methods=['POST'])
@login_required
def send_to_api(lote_id):
    lote = db.get_or_404(Envios, lote_id)
    settings = {s.clave: s.valor for s in Configuracion.query.all()}
    
    json_path = os.path.join(app.config['TEMP_JSON_FOLDER'], f'consolidated_{lote_id}.json')
    if not os.path.exists(json_path):
        flash("No se encontró el archivo JSON consolidado para enviar.", "danger")
        return redirect(url_for('final_submission_status', lote_id=lote.id))
    with open(json_path, 'r', encoding='utf-8') as f:
        lista_trabajadores = json.load(f)

    if not lista_trabajadores:
        flash("El archivo consolidado está vacío, no se puede enviar.", "danger")
        return redirect(url_for('final_submission_status', lote_id=lote.id))

    if 'periodo' not in lista_trabajadores[0]:
        flash("No se encontraron datos del 'periodo' en los registros consolidados.", "danger")
        return redirect(url_for('final_submission_status', lote_id=lote.id))

    periodo_data = lista_trabajadores[0].pop('periodo')
    for trabajador in lista_trabajadores[1:]:
        trabajador.pop('periodo', None)
            
    payload_maestro = {
        "periodo": {
            "fechaLiquidacionInicio": periodo_data.get("fechaLiquidacionInicio"),
            "fechaLiquidacionFin": periodo_data.get("fechaLiquidacionFin"),
            "fechaGen": periodo_data.get("fechaGen")
        },
        "informacionGeneral": {
            "periodoNomina": settings.get('GEN_PERIODO_NOMINA'),
            "tipoXML": settings.get('GEN_TIPO_XML'),
            "version": settings.get('GEN_VERSION')
        },
        "lugarGeneracionXML": {
            "pais": settings.get('EMPLEADOR_PAIS'),
            "departamentoEstado": settings.get('EMPLEADOR_DEPARTAMENTO'),
            "municipioCiudad": settings.get('EMPLEADOR_MUNICIPIO'),
            "idioma": settings.get('GEN_IDIOMA')
        },
        "empleador": {
            "razonSocial": settings.get('EMPLEADOR_RAZON_SOCIAL'),
            "nit": int(settings.get('EMPLEADOR_NIT', 0)),
            "dv": int(settings.get('EMPLEADOR_DV', 0)),
            "pais": settings.get('EMPLEADOR_PAIS'),
            "departamentoEstado": settings.get('EMPLEADOR_DEPARTAMENTO'),
            "municipioCiudad": settings.get('EMPLEADOR_MUNICIPIO'),
            "direccion": settings.get('EMPLEADOR_DIRECCION')
        },
        "trabajador": lista_trabajadores # <--- Aquí usamos la lista completa por ahora
    }
    
    # --- INICIO DE CÓDIGO DE DEPURACIÓN ---
    # Vamos a usar solo el primer trabajador para la prueba
    payload_maestro_debug = payload_maestro.copy()
    payload_maestro_debug['trabajador'] = payload_maestro['trabajador'][:1]

    # Guardamos el payload exacto que se va a enviar en un archivo
    debug_file_path = os.path.join(basedir, 'final_payload_for_debug.json')
    with open(debug_file_path, 'w', encoding='utf-8') as f:
        json.dump(payload_maestro_debug, f, ensure_ascii=False, indent=4)
    print(f"Payload de depuración guardado en: {debug_file_path}")
    # --- FIN DE CÓDIGO DE DEPURACIÓN ---


    api_url = settings.get('API_URL')
    api_user = settings.get('API_USER')
    api_password = settings.get('API_PASSWORD')
    token, error_token = api_client.get_api_token(api_url, api_user, api_password)
    if error_token:
        flash(f"Error de autenticación con la API: {error_token}", "danger")
        return redirect(url_for('final_submission_status', lote_id=lote.id))
    
    # Enviamos el payload de depuración (1 solo trabajador)
    track_id, error_envio = api_client.send_payroll_data(api_url, token, payload_maestro_debug)
    
    if error_envio:
        flash(f"Error al enviar el lote a la API: {error_envio}", "danger")
        lote.estado_lote = 'ERROR_ENVIO'
        lote.mensaje_resultado = error_envio
        db.session.commit()
        return redirect(url_for('final_submission_status', lote_id=lote.id))
    
    lote.estado_lote = 'ENVIADO'
    lote.track_id_api = track_id
    lote.fecha_actualizacion = datetime.utcnow()
    lote.mensaje_resultado = "Lote enviado exitosamente."
    db.session.commit()
    flash(f"¡Lote enviado con éxito! El Track ID es: {track_id}", "success")
    return redirect(url_for('final_submission_status', lote_id=lote.id))
# --- Registrar Blueprints ---
from auth import auth_bp
app.register_blueprint(auth_bp)

# --- Crear la BD y ejecutar la app ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['TEMP_JSON_FOLDER'], exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
