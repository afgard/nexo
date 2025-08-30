# test_api_connection.py
# coding: utf-8

import os
import api_client
import json

def run_test():
    """
    Ejecuta una prueba de conexión completa contra la API de Aportes en Línea.
    """
    print("--- INICIANDO PRUEBA DE CONEXIÓN CON LA API DE APORTES EN LÍNEA ---")

    # 1. Cargar credenciales desde variables de entorno
    print("\n[Paso 1: Cargando credenciales]")
    api_url = os.environ.get('NEXO_API_URL')
    api_user = os.environ.get('NEXO_API_USER')
    api_password = os.environ.get('NEXO_API_PASSWORD')

    if not all([api_url, api_user, api_password]):
        print("\n[ERROR] Faltan una o más variables de entorno.")
        print("Asegúrate de haber configurado las siguientes variables antes de ejecutar:")
        print("  - NEXO_API_URL: La URL base de la API (ej: https://api.aportesenlinea.com)")
        print("  - NEXO_API_USER: Tu usuario de la API.")
        print("  - NEXO_API_PASSWORD: Tu contraseña de la API.")
        print("\n--- PRUEBA FALLIDA ---")
        return

    print("Credenciales cargadas correctamente.")

    # 2. Probar la autenticación y obtener el token
    print("\n[Paso 2: Solicitando token de autenticación]")
    token, error = api_client.get_api_token(api_url, api_user, api_password)

    if error:
        print(f"\n[ERROR] No se pudo obtener el token: {error}")
        print("\n--- PRUEBA FALLIDA ---")
        return

    print(f"¡Token obtenido con éxito! Token: {token[:15]}...") # Mostramos solo una parte por seguridad

    # 3. Probar el envío de datos con un payload de ejemplo
    print("\n[Paso 3: Enviando un paquete de datos de prueba]")

    # Creamos un payload mínimo y falso que imita la estructura real.
    # La API debería rechazarlo por contenido inválido, pero responder con un HTTP 200 y un JSON.
    # Si obtenemos un error 401 (No autorizado) o 400 por estructura, hay un problema.
    mock_payload = {
        "periodo": {
            "fechaLiquidacionInicio": "2023-01-01",
            "fechaLiquidacionFin": "2023-01-31",
            "fechaGen": "2023-02-01"
        },
        "informacionGeneral": {
            "periodoNomina": "5",
            "tipoXML": "102",
            "version": "1.0"
        },
        "empleador": {
            "razonSocial": "Mi Empresa de Prueba",
            "nit": 123456789,
            "dv": 1,
            "pais": "CO",
            "departamentoEstado": "11",
            "municipioCiudad": "11001",
            "direccion": "Calle Falsa 123"
        },
        "trabajador": [
            {
                "numeroDocumento": "987654321",
                "primerApellido": "ApellidoPrueba",
                "primerNombre": "NombrePrueba",
                # ... y muchos otros campos que la app real llenaría ...
                "devengadosTotal": 50000,
                "deduccionesTotal": 5000,
                "comprobanteTotal": 45000
            }
        ]
    }
    print("Payload de prueba construido.")
    print("Enviando al endpoint de recepción...")

    track_id, error = api_client.send_payroll_data(api_url, token, mock_payload)

    if error:
        print(f"\n[RESPUESTA] La API respondió con un error al enviar datos: {error}")
        print("NOTA: Esto puede ser normal si la API valida el contenido y rechaza nuestros datos de prueba.")
        print("Lo importante es que no sea un error 401 (No Autorizado) o de conexión.")
    else:
        print(f"\n[RESPUESTA] ¡La API aceptó el envío!")
        print(f"Track ID recibido: {track_id}")

    print("\n--- PRUEBA FINALIZADA ---")


if __name__ == '__main__':
    print("=====================================================================")
    print("Este script prueba la conexión con la API de Aportes en Línea.")
    print("Utiliza las funciones de `api_client.py` para autenticar y enviar datos.")
    print("=====================================================================")
    print("Instrucciones de uso:")
    print("1. Abre una terminal o línea de comandos.")
    print("2. Configura las variables de entorno con tus credenciales.")
    print("   - En Linux/macOS: export NEXO_API_URL='https://...'")
    print("   - En Windows (cmd): set NEXO_API_URL='https://...'")
    print("   - En Windows (PowerShell): $env:NEXO_API_URL='https://...'")
    print("3. Ejecuta el script con: python test_api_connection.py")
    print("=====================================================================")

    run_test()
