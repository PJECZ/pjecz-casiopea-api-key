"""
Cit Citas, esquemas de pydantic
"""

import uuid
from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict


class CitCitaCancelIn(BaseModel):
    """Esquema para cancelar una cita"""

    id: uuid.UUID
    cit_cliente_email: str


class CitCitaIn(BaseModel):
    """Esquema para crear una cita"""

    cit_cliente_id: uuid.UUID
    cit_servicio_clave: str
    fecha: date
    hora_minuto: time
    oficina_clave: str
    notas: str


class CitCitaOut(BaseModel):
    """Esquema para entregar citas"""

    id: uuid.UUID
    cit_cliente_id: uuid.UUID
    cit_cliente_nombre: str
    cit_cliente_curp: str
    cit_cliente_email: str
    cit_servicio_clave: str
    cit_servicio_descripcion: str
    oficina_clave: str
    oficina_descripcion: str
    oficina_descripcion_corta: str
    inicio: datetime
    termino: datetime
    notas: str
    estado: str
    asistencia: bool
    codigo_asistencia: str
    codigo_acceso_url: str | None = None
    creado: datetime
    puede_cancelarse: bool
    codigo_barras: str | None = None
    codigo_barras_url: str | None = None
    model_config = ConfigDict(from_attributes=True)


class OneCitCitaOut(BaseModel):
    """Esquema para entregar un cita"""

    success: bool
    message: str
    data: CitCitaOut | None = None


class CitCitaConfirmadaOut(BaseModel):
    """Esquema para entregar una cita confirmada"""

    id: uuid.UUID
    cit_cliente_nombre: str
    cit_cliente_email: str | None = None
    cit_cliente_telefono: str | None = None
    oficina_clave: str
    oficina_descripcion_corta: str
    cit_servicio_clave: str
    cit_servicio_descripcion: str
    unidad_id: int
    fecha: date
    hora_inicio: str
    notas: str
    codigo_acceso_id: int
    codigo_acceso_url: str | None = None
    codigo_acceso_url_whatsapp: str | None = None
    turno_codigo: str
    turno_id: int
    model_config = ConfigDict(from_attributes=True)


class OneCitCitaConfirmadaOut(BaseModel):
    """Esquema para entregar una cita confirmada"""

    success: bool
    message: str
    data: CitCitaConfirmadaOut | None = None