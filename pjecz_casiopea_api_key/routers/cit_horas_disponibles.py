"""
Cit Horas Disponibles, routers
"""

from datetime import date, datetime, time, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from ..config.settings import Settings, get_settings
from ..dependencies.authentications import UsuarioInDB, get_current_active_user
from ..dependencies.database import Session, get_db
from ..dependencies.safe_string import safe_clave
from ..models.cit_citas import CitCita
from ..models.cit_horas_bloqueadas import CitHoraBloqueada
from ..models.cit_servicios import CitServicio
from ..models.oficinas import Oficina
from ..models.permisos import Permiso
from ..schemas.cit_horas_disponibles import ListCitHoraDisponibleOut
from .cit_dias_disponibles import listar_dias_disponibles

cit_horas_disponibles = APIRouter(prefix="/api/v5/cit_horas_disponibles")


def listar_horas_disponibles(
    database: Session,
    cit_servicio: CitServicio,
    oficina: Oficina,
    fecha: date,
) -> list[time]:
    """Listar las horas disponibles"""

    # Tomar los tiempos de inicio y término de la oficina
    apertura = oficina.apertura
    cierre = oficina.cierre

    # Si el servicio tiene un tiempo desde
    if cit_servicio.desde and apertura < cit_servicio.desde:
        apertura = cit_servicio.desde

    # Si el servicio tiene un tiempo hasta
    if cit_servicio.hasta and cierre > cit_servicio.hasta:
        cierre = cit_servicio.hasta

    # Definir los tiempos de inicio, de final y el timedelta de la duración
    tiempo_inicial = datetime(
        year=fecha.year,
        month=fecha.month,
        day=fecha.day,
        hour=apertura.hour,
        minute=apertura.minute,
        second=0,
    )
    tiempo_final = datetime(
        year=fecha.year,
        month=fecha.month,
        day=fecha.day,
        hour=cierre.hour,
        minute=cierre.minute,
        second=0,
    )
    duracion = timedelta(
        hours=cit_servicio.duracion.hour,
        minutes=cit_servicio.duracion.minute,
    )

    # Consultar las horas bloqueadas de la oficina en la fecha dada
    cit_horas_bloqueadas = (
        database.query(CitHoraBloqueada)
        .filter_by(oficina_id=oficina.id)
        .filter_by(fecha=fecha)
        .filter_by(estatus="A")
        .order_by(CitHoraBloqueada.id)
        .all()
    )

    # Determinar los tiempos bloqueados
    tiempos_bloqueados = []
    for cit_hora_bloqueada in cit_horas_bloqueadas:
        tiempo_bloquedo_inicia = datetime(
            year=fecha.year,
            month=fecha.month,
            day=fecha.day,
            hour=cit_hora_bloqueada.inicio.hour,
            minute=cit_hora_bloqueada.inicio.minute,
            second=0,
        )
        tiempo_bloquedo_termina = datetime(
            year=fecha.year,
            month=fecha.month,
            day=fecha.day,
            hour=cit_hora_bloqueada.termino.hour,
            minute=cit_hora_bloqueada.termino.minute,
            second=0,
        ) - timedelta(minutes=1)
        tiempos_bloqueados.append((tiempo_bloquedo_inicia, tiempo_bloquedo_termina))

    # Determinar los tiempos para filtrar las citas agendadas
    inicio_dt = datetime(year=fecha.year, month=fecha.month, day=fecha.day, hour=0, minute=0, second=0)
    termino_dt = datetime(year=fecha.year, month=fecha.month, day=fecha.day, hour=23, minute=59, second=59)

    # Consultar las citas agendadas para ese servicio en esa oficina
    cit_citas = (
        database.query(CitCita)
        .filter(CitCita.oficina_id == oficina.id)
        .filter(CitCita.cit_servicio_id == cit_servicio.id)
        .filter(CitCita.inicio >= inicio_dt)
        .filter(CitCita.inicio <= termino_dt)
        .filter(CitCita.estado != "CANCELO")
        .all()
    )

    # Acumular las cantidades de citas agendadas en un diccionario de tiempos y cantidad de citas
    # Por ejemplo { 08:30: 2, 08:45: 1, 10:00: 2,... }
    citas_ya_agendadas = {}
    for cit_cita in cit_citas:
        if cit_cita.inicio not in citas_ya_agendadas:
            citas_ya_agendadas[cit_cita.inicio] = 1
        else:
            citas_ya_agendadas[cit_cita.inicio] += 1

    # Bucle por los intervalos
    horas_minutos_segundos_disponibles = []
    tiempo = tiempo_inicial
    while tiempo < tiempo_final:
        # Bandera
        es_hora_disponible = True
        # Quitar las horas bloqueadas
        for tiempo_bloqueado in tiempos_bloqueados:
            if tiempo_bloqueado[0] <= tiempo <= tiempo_bloqueado[1]:
                es_hora_disponible = False
                break
        # Quitar las horas ocupadas
        if tiempo in citas_ya_agendadas:
            if citas_ya_agendadas[tiempo] >= oficina.limite_personas:
                es_hora_disponible = False
        # Acumular si es hora disponible
        if es_hora_disponible:
            horas_minutos_segundos_disponibles.append(tiempo.time())
        # Siguiente intervalo
        tiempo = tiempo + duracion

    # Entregar
    return horas_minutos_segundos_disponibles


@cit_horas_disponibles.get("", response_model=ListCitHoraDisponibleOut)
async def listado(
    current_user: Annotated[UsuarioInDB, Depends(get_current_active_user)],
    database: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    cit_servicio_clave: str,
    fecha: date,
    oficina_clave: str,
):
    """Horas disponibles"""
    if current_user.permissions.get("CIT CITAS", 0) < Permiso.CREAR:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    # Consultar la oficina
    oficina_clave = safe_clave(oficina_clave)
    if oficina_clave == "":
        return ListCitHoraDisponibleOut(success=False, message="No es válida la clave de la oficina")
    try:
        oficina = database.query(Oficina).filter_by(clave=oficina_clave).one()
    except (MultipleResultsFound, NoResultFound):
        return ListCitHoraDisponibleOut(success=False, message="No existe esa oficina")
    if oficina.estatus != "A":
        return ListCitHoraDisponibleOut(success=False, message="No está habilitada esa oficina")

    # Consultar el servicio
    cit_servicio_clave = safe_clave(cit_servicio_clave)
    if cit_servicio_clave == "":
        return ListCitHoraDisponibleOut(success=False, message="No es válida la clave del servicio")
    try:
        cit_servicio = database.query(CitServicio).filter_by(clave=cit_servicio_clave).one()
    except (MultipleResultsFound, NoResultFound):
        return ListCitHoraDisponibleOut(success=False, message="No existe ese servicio")
    if cit_servicio.estatus != "A":
        return ListCitHoraDisponibleOut(success=False, message="No está habilitado ese servicio")

    # Validar la fecha
    if fecha not in listar_dias_disponibles(database, settings):
        return ListCitHoraDisponibleOut(success=False, message="La fecha proporcionada no es válida")

    # Listar las horas disponibles
    horas_minutos_segundos_disponibles = listar_horas_disponibles(
        database=database,
        cit_servicio=cit_servicio,
        oficina=oficina,
        fecha=fecha,
    )

    # Si no hay disponibilidad, entregar success falso y con mensaje de que no hay
    if len(horas_minutos_segundos_disponibles) == 0:
        return ListCitHoraDisponibleOut(
            success=False,
            message="No hay horas disponibles para esa fecha",
            data=None,
        )

    # Entregar listado
    return ListCitHoraDisponibleOut(
        success=True,
        message="Listado de horas disponibles",
        data=horas_minutos_segundos_disponibles,
    )
