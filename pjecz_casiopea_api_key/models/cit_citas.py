"""
Cit Citas, modelos
"""

import base64
from datetime import datetime
from typing import Optional
import uuid

import pytz
from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import BYTEA, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..dependencies.database import Base
from ..dependencies.universal_mixin import UniversalMixin


class CitCita(Base, UniversalMixin):
    """CitCita"""

    ESTADOS = {
        "ASISTIO": "Asistió",
        "CANCELO": "Canceló",
        "INASISTENCIA": "Inasistencia",
        "PENDIENTE": "Pendiente",
    }

    # Nombre de la tabla
    __tablename__ = "cit_citas"

    # Clave primaria
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Claves foráneas
    cit_cliente_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cit_clientes.id"))
    cit_cliente: Mapped["CitCliente"] = relationship(back_populates="cit_citas")
    cit_servicio_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cit_servicios.id"))
    cit_servicio: Mapped["CitServicio"] = relationship(back_populates="cit_citas")
    oficina_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("oficinas.id"))
    oficina: Mapped["Oficina"] = relationship(back_populates="cit_citas")

    # Columnas
    inicio: Mapped[datetime]
    termino: Mapped[datetime]
    notas: Mapped[Optional[str]] = mapped_column(Text)
    estado: Mapped[str] = mapped_column(Enum(*ESTADOS, name="estados", native_enum=False), index=True)
    cancelar_antes: Mapped[datetime]
    asistencia: Mapped[bool] = mapped_column(default=False)
    codigo_asistencia: Mapped[str] = mapped_column(String(6), default="000000")
    codigo_acceso_id: Mapped[Optional[int]]
    codigo_acceso_url: Mapped[Optional[str]] = mapped_column(String(512))
    codigo_barras: Mapped[Optional[str]] = mapped_column(String(13))
    codigo_barras_url: Mapped[Optional[str]] = mapped_column(String(512))
    turno_id: Mapped[Optional[int]]
    turno: Mapped[Optional[str]] = mapped_column(String(16))

    @property
    def codigo_acceso_imagen_base64(self):
        """Codificar en base64 la imagen del codigo de acceso"""
        if self.codigo_acceso_imagen is None:
            return None
        return base64.b64encode(self.codigo_acceso_imagen)

    @property
    def cit_cliente_nombre(self):
        """Nombre del cliente"""
        return self.cit_cliente.nombre

    @property
    def cit_cliente_curp(self):
        """Curp del cliente"""
        return self.cit_cliente.curp

    @property
    def cit_cliente_email(self):
        """Email del cliente"""
        return self.cit_cliente.email

    @property
    def cit_servicio_clave(self):
        """Clave del servicio"""
        return self.cit_servicio.clave

    @property
    def cit_servicio_descripcion(self):
        """Descripción del servicio"""
        return self.cit_servicio.descripcion

    @property
    def oficina_clave(self):
        """Clave de la oficina"""
        return self.oficina.clave

    @property
    def oficina_descripcion(self):
        """Descripcion de la oficina"""
        return self.oficina.descripcion

    @property
    def oficina_descripcion_corta(self):
        """Descripcion corta de la oficina"""
        return self.oficina.descripcion_corta

    @property
    def puede_cancelarse(self):
        """¿Puede cancelarse esta cita?"""
        if self.estado != "PENDIENTE":
            return False
        ahora = datetime.now(tz=pytz.timezone("America/Mexico_City"))
        ahora_sin_tz = ahora.replace(tzinfo=None)
        if self.cancelar_antes is None:
            return ahora_sin_tz < self.inicio
        return ahora_sin_tz < self.cancelar_antes

    def __repr__(self):
        """Representación"""
        return f"<CitCita {self.id}>"
