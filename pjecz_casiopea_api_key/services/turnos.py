"""
Servicio para conectar con la API del sistema de turnos
"""

import json
import requests
from requests.exceptions import RequestException
from json.decoder import JSONDecodeError
from typing import Tuple

from pjecz_casiopea_flask.config.settings import Settings


class MyAnyError(Exception):
    """Base exception class"""

class MyRequestError(MyAnyError):
    """Excepción porque falló el request"""

class Turnos():
    """Turnos"""

    _settings: Settings
    _turno_id: int
    _turno_codigo: str

    def __init__(self, setting: Settings):
        """Inicializa el servicio de turnos"""

        self._settings = setting
        self._turno_id = 0
        self._turno_codigo = ""
    
    def crear_turno(self, payload_json: json) -> Tuple[bool, str]:
        """
        Crea un nuevo turno en el sistema de turnos con el tipo cita.
        :return ID del turno y el código del turno generado.
        """

        url = f"{self._settings.TURNOS_API_KEY_URL}/crear_turno"
        headers = {
            "X-API-KEY": self._settings.TURNOS_API_KEY,
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(url, headers=headers, data=payload_json, timeout=5)
            response.raise_for_status()

            try:
                data = response.json()
                if "success" in data and "message" in data:
                    self._turno_id = data["data"]["turno_id"];
                    self._turno_codigo = f'{data["data"]["unidad"]["clave"]}-{data["data"]["turno_numero"]}'
                    return data["success"], data["message"]
                return False, "Respuesta JSON inválida desde el servidor de turnos."

            except JSONDecodeError:
                return False, "No se pudo decodificar la respuesta JSON del servidor de turnos."

        except RequestException as e:
            return False, f"Error de conexión con el sistema de turnos: {e}"
        except Exception as e:
            return False, f"Ocurrió un error inesperado: {e}"

    def get_turno_id(self) -> int:
        """Entrega el ID del turno generado"""
        return self._turno_id
    
    def get_turno_codigo(self) -> int:
        """Entrega el Código del turno generado"""
        return self._turno_codigo
    
    def test_conexion(self) -> Tuple[bool, str]:
        """
        Prueba de conexión con el sistema de turnos
        :return Éxito o fallo y mensaje de respuesta.
        """

        url = f"{self._settings.TURNOS_API_KEY_URL}/test_conexion"
        headers = {"X-API-KEY": self._settings.TURNOS_API_KEY}

        try:
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()  # Lanza una excepción para códigos de error HTTP (4xx o 5xx)

            try:
                data = response.json()
                if "success" in data and "message" in data:
                    return data["success"], data["message"]
                return False, "Respuesta JSON inválida desde el servidor de turnos."

            except JSONDecodeError:
                return False, "No se pudo decodificar la respuesta JSON del servidor de turnos."

        except RequestException as e:
            return False, f"Error de conexión con el sistema de turnos: {e}"

        except Exception as e:
            return False, f"Ocurrió un error inesperado: {e}"
    
    def test_crear_turno(self, payload_json_file: json) -> Tuple[bool, str]:
        """
        Prueba para crear un turno en el sistema de turnos
        :return Éxito o fallo y mensaje de respuesta.
        """

        url = f"{self._settings.TURNOS_API_KEY_URL}/test_crear_turno"
        headers = {"X-API-KEY": self._settings.TURNOS_API_KEY}

        try:
            response = requests.post(url, headers=headers, json=payload_json_file, timeout=5)
            response.raise_for_status()

            try:
                data = response.json()
                if "success" in data and "message" in data:
                    return data["success"], data["message"]
                return False, "Respuesta JSON inválida desde el servidor de turnos."

            except JSONDecodeError:
                return False, "No se pudo decodificar la respuesta JSON del servidor de turnos."

        except RequestException as e:
            return False, f"Error de conexión con el sistema de turnos: {e}"
        except Exception as e:
            return False, f"Ocurrió un error inesperado: {e}"
