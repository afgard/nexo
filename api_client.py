# api_client.py (Versión Corregida Final)
# coding: utf-8

import requests
import json

def get_api_token(base_api_url, user, password):
    """
    Obtiene un token de autenticación de la API construyendo la URL correcta.
    """
    auth_url = f"{base_api_url.rstrip('/')}/Api/NominaElectronica/Autenticacion"
    
    auth_payload = {
        "user": user,
        "password": password,
        "ambiente": 1
    }
    
    print(f"[API Client] Solicitando token de autenticación a: {auth_url}")
    
    try:
        response = requests.post(auth_url, json=auth_payload, timeout=20)
        response.raise_for_status()
        
        response_json = response.json()
        token = response_json.get('token')
        if not token:
            error_msg = f"Respuesta exitosa, pero no se encontró un 'token'. Respuesta recibida: {response_json}"
            raise Exception(error_msg)
        
        print("[API Client] Token recibido con éxito.")
        return token, None
    except json.JSONDecodeError:
        error_msg = "Error de autenticación: La respuesta del servidor no es un JSON válido (probablemente la URL base es incorrecta o la API está caída)."
        print(f"[API Client] {error_msg}")
        return None, error_msg
    except requests.exceptions.HTTPError as e:
        error_msg = f"Error HTTP al autenticar: {e.response.status_code} - {e.response.text}"
        print(f"[API Client] {error_msg}")
        return None, error_msg
    except requests.exceptions.RequestException as e:
        error_msg = f"Error de conexión al autenticar: {e}"
        print(f"[API Client] {error_msg}")
        return None, error_msg
    except Exception as e:
        error_msg = f"Error inesperado en la autenticación: {e}"
        print(f"[API Client] {error_msg}")
        return None, error_msg

def send_payroll_data(base_api_url, token, payroll_data):
    """
    Envía el lote de datos de nómina a la API.
    """
    submission_url = f"{base_api_url.rstrip('/')}/Api/NominaElectronica/Recepcion"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # El payload final es el diccionario completo que ya viene preparado desde app.py.
    final_payload = payroll_data
    
    # Se cuenta el número de trabajadores dentro del payload para el mensaje de log.
    num_trabajadores = len(final_payload.get("trabajador", []))
    print(f"[API Client] Enviando lote de {num_trabajadores} empleados a: {submission_url}")
    try:
        # Se incrementa el timeout por si la carga de datos es muy grande
        response = requests.post(submission_url, headers=headers, json=final_payload, timeout=120) 
        response.raise_for_status()
        
        response_json = response.json()
        track_id = response_json.get('trackId')
        if not track_id:
            raise Exception("La respuesta de la API de envío no contiene un 'trackId'.")
            
        print(f"[API Client] Envío exitoso. Track ID recibido: {track_id}")
        return track_id, None
    except requests.exceptions.HTTPError as e:
        # Capturamos el error HTTP para poder ver el cuerpo de la respuesta del servidor
        error_msg = f"Error HTTP al enviar el lote: {e.response.status_code} - {e.response.text}"
        print(f"[API Client] {error_msg}")
        return None, error_msg
    except requests.exceptions.RequestException as e:
        error_msg = f"Error de conexión al enviar el lote: {e}"
        print(f"[API Client] {error_msg}")
        return None, error_msg
    except Exception as e:
        error_msg = f"Error en la respuesta del envío: {e}"
        print(f"[API Client] {error_msg}")
        return None, error_msg
