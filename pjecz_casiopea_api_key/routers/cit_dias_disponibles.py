"""
Cit Días Disponibles, routers
"""

from datetime import date, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
import pytz
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from ..config.settings import Settings, get_settings
from ..dependencies.authentications import UsuarioInDB, get_current_active_user
from ..dependencies.database import Session, get_db
from ..dependencies.safe_string import safe_clave
from ..models.cit_dias_inhabiles import CitDiaInhabil
from ..models.cit_servicios import CitServicio
from ..models.oficinas import Oficina
from ..models.permisos import Permiso
from ..schemas.cit_dias_disponibles import ListCitDiaDisponibleOut

LIMITE_DIAS = 90
QUITAR_PRIMER_DIA_DESPUES_HORAS = 14

cit_dias_disponibles = APIRouter(prefix="/api/v5/cit_dias_disponibles")


def listar_dias_disponibles(
    database: Session,
    settings: Settings,
) -> list[date]:
    """Listar los días disponibles"""

    # Consultar los días inhábiles
    cit_dias_inhabiles = (
        database.query(CitDiaInhabil)
        .filter(CitDiaInhabil.fecha >= date.today())
        .filter(CitDiaInhabil.estatus == "A")
        .order_by(CitDiaInhabil.fecha)
        .all()
    )
    dias_inhabiles = [item.fecha for item in cit_dias_inhabiles]

    # Acumular los días
    dias_disponibles = []
    for fecha in (date.today() + timedelta(n) for n in range(1, LIMITE_DIAS)):
        if fecha.weekday() in (5, 6):  # Quitar los sábados y domingos
            continue
        if fecha in dias_inhabiles:  # Quitar los dias inhábiles
            continue
        dias_disponibles.append(fecha)  # Acumular

    # Determinar el dia de hoy
    servidor_tz = pytz.UTC
    local_tz = pytz.timezone(settings.TZ)
    servidor_ts = datetime.now(tz=servidor_tz)
    local_ts = servidor_ts.astimezone(local_tz)
    hoy = local_ts.date()

    # Si hoy es sábado, domingo o dia inhábil, quitar el primer día disponible
    hoy_es_sabado_o_domingo = hoy.weekday() in (5, 6)
    hoy_es_dia_inhabil = hoy in dias_inhabiles
    pasa_de_la_hora = local_ts.hour > QUITAR_PRIMER_DIA_DESPUES_HORAS
    if hoy_es_sabado_o_domingo or hoy_es_dia_inhabil or pasa_de_la_hora:
        dias_disponibles.pop(0)

    # Entregar
    return dias_disponibles


@cit_dias_disponibles.get("", response_model=ListCitDiaDisponibleOut)
async def listado(
    current_user: Annotated[UsuarioInDB, Depends(get_current_active_user)],
    database: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    oficina_clave: str = None,
    cit_servicio_clave: str = None,
):
    """Días disponibles"""
    if current_user.permissions.get("CIT CITAS", 0) < Permiso.CREAR:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    # Obtener los días disponibles base
    dias = listar_dias_disponibles(database, settings)

    # Si se dan oficina y servicio, filtrar días sin horas disponibles
    if oficina_clave and cit_servicio_clave:
        try:
            oficina = database.query(Oficina).filter_by(clave=safe_clave(oficina_clave)).one()
        except (ValueError, MultipleResultsFound, NoResultFound):
            return ListCitDiaDisponibleOut(success=False, message="No existe esa oficina")
        if oficina.estatus != "A":
            return ListCitDiaDisponibleOut(success=False, message="No está habilitada esa oficina")
        try:
            cit_servicio = database.query(CitServicio).filter_by(clave=safe_clave(cit_servicio_clave)).one()
        except (ValueError, MultipleResultsFound, NoResultFound):
            return ListCitDiaDisponibleOut(success=False, message="No existe ese servicio")
        if cit_servicio.estatus != "A":
            return ListCitDiaDisponibleOut(success=False, message="No está habilitado ese servicio")

        # Import local para evitar importación circular (cit_horas_disponibles importa de este módulo)
        from .cit_horas_disponibles import listar_horas_disponibles

        dias = [dia for dia in dias if listar_horas_disponibles(database, cit_servicio, oficina, dia)]

    # Entregar
    return ListCitDiaDisponibleOut(
        success=True,
        message="Listado de días disponibles",
        data=dias,
    )
