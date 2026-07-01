"""
Servicio para crear un código de barras
"""
import barcode
from google.cloud import storage
from google.api_core import exceptions
import io
import secrets
from datetime import datetime
from typing import Tuple

from ..config.settings import Settings, get_settings
from ..dependencies.database import Session

from barcode.writer import ImageWriter

from ..models.cit_citas import CitCita

class CodigoBarras():
    """Código de Barras"""

    _settings: Settings
    _database: Session

    def __init__(self, database: Session):
        """
        Inicializa la clase encargada de los códigos de barras.
        :param ruta_salida: Carpeta donde se guardarán las imágenes generadas.
        """
        self._settings = get_settings()
        self._database = database

    def crear_y_subir(self) -> Tuple[str, str]:
        """
        Crea un nuevo código de barras y regresa al URL donde fue guardado
        en el registro de la cita indicada
        """

        # 1. Generar un código numérico único que no exista en la base de datos
        codigo_barras_numerico_unico = None
        codigo_barras_repetido = True
        while codigo_barras_repetido:
            codigo_barras_numerico_unico = self._generar_codigo_barras_ean13()
            cita_existente = self._database.query(CitCita).filter_by(codigo_barras=codigo_barras_numerico_unico).first()
            codigo_barras_repetido = cita_existente is not None

        # 2. Generar la imagen del código de barras en memoria
        codigo_barras_img = self._crear_imagen_ean13(codigo_barras_numerico_unico)

        # 3. Subirla a Google Cloud Storage
        try:
            codigo_barras_url = self._subir_a_google_storage(
                imagen=codigo_barras_img,
                numero_codigo=codigo_barras_numerico_unico
            )
        except (exceptions.GoogleAPICallError, ValueError) as e:
            # Manejar posibles errores durante la subida
            # Aquí podrías loggear el error o lanzar una excepción más específica
            raise ConnectionError(f"Error al subir imagen a Google Storage: {e}") from e

        return codigo_barras_numerico_unico, codigo_barras_url
    
    def _subir_a_google_storage(self, imagen: bytes, numero_codigo: str) -> str:
        """Sube la imagen generada a Google Storage y regresa la URL pública."""

        storage_client = storage.Client()
        bucket = storage_client.bucket(self._settings.GCS_BUCKET_NAME)
        
        # Generar ruta con formato AÑO/MES/archivo.png
        ahora = datetime.now()
        nombre_archivo = f"pjecz-citas/{ahora.strftime('%Y')}/{ahora.strftime('%m')}/{numero_codigo}.png"
        blob = bucket.blob(nombre_archivo)

        blob.upload_from_string(imagen, content_type="image/png")

        return blob.public_url
    
    def _calcular_digito_verificador_ean13(self, base_12_digitos: str) -> str:
        """Calcula el 13º dígito de control para un código EAN-13."""
        suma = 0
        for i, digito in enumerate(base_12_digitos):
            num = int(digito)
            # Las posiciones impares se multiplican por 1, las pares por 3
            # (Nota: i empieza en 0, que es la primera posición)
            if i % 2 == 0:
                suma += num * 1
            else:
                suma += num * 3
                
        digito_control = (10 - (suma % 10)) % 10
        return str(digito_control)

    def _generar_codigo_barras_ean13(self) -> str:
        """Genera un código EAN-13 aleatorio de 13 dígitos válido para lectores."""
        # 1. Generamos un número aleatorio de 11 dígitos
        # Usamos secrets.randbelow para garantizar un rango limpio de 11 posiciones
        numero_aleatorio = secrets.randbelow(90000000000) + 10000000000
        # Añadimos un número identificador de la app quien crea el código al principio del mismo.
        APP_CITAS_ID = 1
        base_12 = str(APP_CITAS_ID) + str(numero_aleatorio)
        
        # 2. Calculamos el dígito 13
        digito_13 = self._calcular_digito_verificador_ean13(base_12)
        
        # 3. Retornamos el código EAN-13 completo
        return base_12 + digito_13
    
    def _crear_imagen_ean13(self, numero_codigo: str) -> bytes:
        """
        Genera una imagen PNG de un código de barras EAN-13 y la devuelve como bytes.
        
        :param numero_codigo: String de 13 dígitos numéricos válidos.
        :return: Los datos de la imagen en formato bytes.
        """

        # 1. Validar que la longitud sea la correcta para EAN-13
        if len(numero_codigo) != 13 or not numero_codigo.isdigit():
            raise ValueError("El código EAN-13 debe tener exactamente 13 dígitos numéricos.")

        # 2. Crear un buffer en memoria para la imagen
        buffer = io.BytesIO()

        # 2. Obtener la clase del formato EAN-13
        EAN13 = barcode.get_barcode_class('ean13')

        # 3. Configurar el diseño visual del código de barras
        # Ajustamos opciones para que sea altamente legible por escáneres
        opciones_diseno = {
            'format': 'PNG',
            'dpi': 300,              # Alta resolución para impresión o pantallas
            'module_height': 10.0,   # Altura de las barras
            'module_width': 0.2,     # Ancho de cada barra individual
            'font_size': 10,         # Tamaño del texto que sale abajo
            'text_distance': 4.0,    # Distancia entre las barras y el texto
            'quiet_zone': 5.0        # Margen blanco a los lados para que el lector enfoque bien
        }

        # 4. Instanciar el código con el ImageWriter (necesario para generar archivos de imagen)
        codigo_objeto = EAN13(numero_codigo, writer=ImageWriter())

        # 5. Escribir la imagen en el buffer en memoria en lugar de un archivo
        codigo_objeto.write(buffer, options=opciones_diseno)

        # 6. Regresar al inicio del buffer y devolver su contenido
        buffer.seek(0)
        return buffer.read()