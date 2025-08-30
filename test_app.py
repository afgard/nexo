# test_app.py
from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    # Esta página solo tiene un enlace a la página de prueba
    return 'Página de inicio. <a href="/test/123">Haz clic aquí para probar</a>'

@app.route('/test/<int:some_id>')
def test_page(some_id):
    # Esta es la ruta que queremos verificar que funcione
    return f'<h1>¡Éxito!</h1><p>Has llegado a la página de prueba con el ID: {some_id}</p>'

if __name__ == '__main__':
    # Ejecutamos esta app de prueba simple
    app.run(host='0.0.0.0', port=5000)
