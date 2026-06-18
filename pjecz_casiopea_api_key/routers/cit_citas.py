"""
Cit Citas, routers
"""

import json
from datetime import date, datetime, timedelta
from typing import Annotated, Tuple

import requests
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlalchemy import func

from ..config.settings import Settings, get_settings
from ..dependencies.authentications import UsuarioInDB, get_current_active_user
from ..dependencies.control_acceso import generar_referencia
from ..dependencies.database import Session, get_db
from ..dependencies.fastapi_pagination_custom_page import CustomPage
from ..dependencies.pwgen import generar_codigo_asistencia
from ..dependencies.safe_string import safe_clave, safe_curp, safe_email, safe_string, safe_uuid
from ..models.cit_citas import CitCita
from ..models.cit_clientes import CitCliente
from ..models.cit_dias_inhabiles import CitDiaInhabil
from ..models.cit_oficinas_servicios import CitOficinaServicio
from ..models.cit_servicios import CitServicio
from ..models.oficinas import Oficina
from ..models.permisos import Permiso
from ..schemas.cit_citas import CitCitaIn, CitCitaOut, OneCitCitaOut, CitCitaConfirmadaOut, OneCitCitaConfirmadaOut
from .cit_dias_disponibles import listar_dias_disponibles
from .cit_horas_disponibles import listar_horas_disponibles
from ..services.sendmail import MyRequestError, Email, PlantillaCitaCancelada, PlantillaCitaCreada
from ..services.codigo_barras import CodigoBarras
from ..services.turnos import Turnos

LIMITE_CITAS_PENDIENTES = 3

cit_citas = APIRouter(prefix="/api/v5/cit_citas")


@cit_citas.patch("/cancelar", response_model=OneCitCitaOut)
async def cancelar(
    current_user: Annotated[UsuarioInDB, Depends(get_current_active_user)],
    database: Annotated[Session, Depends(get_db)],
    cit_cita_id: str,
):
    """Cancelar una cita"""
    if current_user.permissions.get("CIT CITAS", 0) < Permiso.CREAR:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    # Consultar, validar que no esté eliminada o que no sea PENDIENTE
    try:
        cit_cita_id = safe_uuid(cit_cita_id)
    except ValueError:
        return OneCitCitaOut(success=False, message="No es válida la UUID")
    cit_cita = database.query(CitCita).get(cit_cita_id)
    if not cit_cita:
        return OneCitCitaOut(success=False, message="No existe esa cita")
    if cit_cita.estatus != "A":
        return OneCitCitaOut(success=False, message="No está habilitada esa cita")
    if cit_cita.estado != "PENDIENTE":
        return OneCitCitaOut(success=False, message="No se puede cancelar esta cita porque no esta pendiente")
    if cit_cita.puede_cancelarse is False:
        raise ValueError("No se puede cancelar esta cita")

    # Actualizar
    cit_cita.estado = "CANCELO"
    database.add(cit_cita)
    database.commit()

    # Creación de la plantilla para el email
    plantilla_email_cita_cancelada = PlantillaCitaCancelada(
        id=str(cit_cita_id),
        nombre_cliente=cit_cita.cit_cliente.nombre,
        oficina=cit_cita.oficina_descripcion,
        servicio=cit_cita.cit_servicio_descripcion,
        fecha_hora_cita=cit_cita.inicio,
        notas=cit_cita.notas,
        fecha_hora_cancelacion=datetime.now(),
    )

    # Envío de email
    send_email = Email(cit_cita.cit_cliente_email, plantilla_email_cita_cancelada)
    try:
        send_email.enviar_email()
    except MyRequestError as error:
        return OneCitCitaOut(success=False, message=str(error))

    # Entregar
    return OneCitCitaOut(
        success=True,
        message="Se ha cancelado la cita",
        data=CitCitaOut.model_validate(cit_cita),
    )


@cit_citas.post("/crear", response_model=OneCitCitaOut)
async def crear(
    current_user: Annotated[UsuarioInDB, Depends(get_current_active_user)],
    database: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    cit_cita_in: CitCitaIn,
):
    """Crear una cita"""
    if current_user.permissions.get("CIT CITAS", 0) < Permiso.CREAR:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    # Consultar el cliente
    cit_cliente = database.query(CitCliente).get(cit_cita_in.cit_cliente_id)
    if cit_cliente is None:
        return OneCitCitaOut(success=False, message="No existe ese cliente")
    if cit_cliente.estatus != "A":
        return OneCitCitaOut(success=False, message="No está habilitado ese cliente")

    # Consultar la oficina
    oficina_clave = safe_clave(cit_cita_in.oficina_clave)
    if oficina_clave == "":
        return OneCitCitaOut(success=False, message="No es válida la clave de la oficina")
    try:
        oficina = database.query(Oficina).filter_by(clave=oficina_clave).one()
    except (MultipleResultsFound, NoResultFound):
        return OneCitCitaOut(success=False, message="No existe esa oficina")
    if oficina.estatus != "A":
        return OneCitCitaOut(success=False, message="No está habilitada esa oficina")

    # Consultar el servicio
    cit_servicio_clave = safe_clave(cit_cita_in.cit_servicio_clave)
    if cit_servicio_clave == "":
        return OneCitCitaOut(success=False, message="No es válida la clave del servicio")
    try:
        cit_servicio = database.query(CitServicio).filter_by(clave=cit_servicio_clave).one()
    except (MultipleResultsFound, NoResultFound):
        return OneCitCitaOut(success=False, message="No existe ese servicio")
    if cit_servicio.estatus != "A":
        return OneCitCitaOut(success=False, message="No está habilitado ese servicio")

    # Validar que la oficina tenga el servicio dado
    try:
        _ = (
            database.query(CitOficinaServicio)
            .filter_by(oficina_id=oficina.id)
            .filter_by(cit_servicio_id=cit_servicio.id)
            .filter_by(estatus="A")
            .one()
        )
    except NoResultFound:
        return OneCitCitaOut(success=False, message="No se puede agendar el servicio en la oficina")

    # Validar que la fecha sea un día disponible
    if cit_cita_in.fecha not in listar_dias_disponibles(database, settings):
        return OneCitCitaOut(success=False, message="No es válida la fecha")

    # Validar la hora_minuto, respecto a las horas disponibles
    if cit_cita_in.hora_minuto not in listar_horas_disponibles(database, cit_servicio, oficina, cit_cita_in.fecha):
        return OneCitCitaOut(success=False, message="No es valida la hora-minuto porque no esta disponible")

    # Definir el inicio de la cita
    inicio_dt = datetime(
        year=cit_cita_in.fecha.year,
        month=cit_cita_in.fecha.month,
        day=cit_cita_in.fecha.day,
        hour=cit_cita_in.hora_minuto.hour,
        minute=cit_cita_in.hora_minuto.minute,
    )

    # Definir el término de la cita
    termino_dt = inicio_dt + timedelta(hours=cit_servicio.duracion.hour, minutes=cit_servicio.duracion.minute)

    # Validar que la cantidad de citas de la oficina en ese tiempo NO hayan llegado al límite
    cit_citas_oficina_cantidad = (
        database.query(CitCita)
        .filter(CitCita.oficina_id == oficina.id)
        .filter(CitCita.inicio >= inicio_dt)
        .filter(CitCita.termino <= termino_dt)
        .filter(CitCita.estado != "CANCELADO")
        .filter(CitCita.estatus == "A")
        .count()
    )
    if cit_citas_oficina_cantidad >= oficina.limite_personas:
        return OneCitCitaOut(
            success=False,
            message="No se puede crear la cita porque ya se alcanzo el limite de personas en la oficina",
        )

    # Validar que la cantidad de citas PENDIENTE del cliente y NO sean pasados, NO haya llegado a su límite
    cit_citas_cit_cliente_cantidad = (
        database.query(CitCita)
        .filter(CitCita.cit_cliente_id == cit_cliente.id)
        .filter(func.date(CitCita.inicio) >= datetime.now().date())
        .filter(CitCita.estado == "PENDIENTE")
        .filter(CitCita.estatus == "A")
        .count()
    )
    if cit_citas_cit_cliente_cantidad >= cit_cliente.limite_citas_pendientes:
        return OneCitCitaOut(
            success=False,
            message="No se puede crear la cita porque ya se alcanzo el limite de citas pendientes",
        )

    # Validar que el cliente no tenga una cita pendiente en la misma fecha y hora
    cit_citas_cit_cliente = (
        database.query(CitCita)
        .filter(CitCita.cit_cliente_id == cit_cliente.id)
        .filter(CitCita.estado == "PENDIENTE")
        .filter(CitCita.inicio >= inicio_dt)
        .filter(CitCita.termino <= termino_dt)
        .filter(CitCita.estatus == "A")
        .first()
    )
    if cit_citas_cit_cliente:
        return OneCitCitaOut(
            success=False,
            message="No se puede crear la cita porque ya tiene una cita pendiente en esta fecha y hora",
        )

    # Definir cancelar_antes con 24 horas antes de la cita
    cancelar_antes = inicio_dt - timedelta(hours=24)

    # Si cancelar_antes es un dia inhábil, domingo o sábado, se busca el dia habil anterior
    cit_dias_inhabiles = database.query(CitDiaInhabil).filter_by(estatus="A").order_by(CitDiaInhabil.fecha).all()
    cit_dias_inhabiles_listado = [di.fecha for di in cit_dias_inhabiles]
    while cancelar_antes.date() in cit_dias_inhabiles_listado or cancelar_antes.weekday() == 6 or cancelar_antes.weekday() == 5:
        if cancelar_antes.date() in cit_dias_inhabiles_listado:
            cancelar_antes = cancelar_antes - timedelta(days=1)
        if cancelar_antes.weekday() == 6:  # Si es domingo, se cambia a viernes
            cancelar_antes = cancelar_antes - timedelta(days=2)
        if cancelar_antes.weekday() == 5:  # Si es sábado, se cambia a viernes
            cancelar_antes = cancelar_antes - timedelta(days=1)

    # Variables para códigos de acceso
    codigo_acceso_id = None
    codigo_acceso_url = None
    codigo_barras_num = None
    codigo_barras_url = None
    if oficina.puede_enviar_qr:
        # Obtener código de acceso, entrega idAcceso (int), imagen (str), success (bool) y message (str)
        payload = {
            "aplicacion": settings.CONTROL_ACCESO_APLICACION,
            "referencia": generar_referencia(cit_cliente.email, cit_servicio.clave, oficina.clave, inicio_dt),
            "nombres": cit_cliente.nombres,
            "apellidos": f"{cit_cliente.apellido_primero} {cit_cliente.apellido_segundo}",
            "correoElectronico": cit_cliente.email,
            "telefono": f"+52{cit_cliente.telefono}",
            "fecha": inicio_dt.isoformat(timespec="minutes"),
            "cita": True,
        }
        try:
            respuesta = requests.post(
                url=settings.CONTROL_ACCESO_URL,
                headers={"X-Api-Key": settings.CONTROL_ACCESO_API_KEY},
                timeout=settings.CONTROL_ACCESO_TIMEOUT,
                json=payload,
            )
        except requests.exceptions.ConnectionError as error:
            return OneCitCitaOut(success=False, message=f"ERROR: No responde Control Acceso: {str(error)}")
        if respuesta.status_code != 200:
            return OneCitCitaOut(
                success=False, message=f"ERROR: No fue código 200 la respuesta de Control Acceso: {respuesta.text}"
            )
        contenido = respuesta.json()
        if contenido.get("success") is False:
            return OneCitCitaOut(
                success=False, message=f"ERROR: Falló la obtención del Código de Acceso: {contenido.get('message')}"
            )
        codigo_acceso_id = contenido.get("idAcceso")
        if not codigo_acceso_id:
            return OneCitCitaOut(success=False, message="ERROR: Faltó el IdAcceso en la respuesta de Control Acceso")
        codigo_acceso_url = contenido.get("imagen")
        if not codigo_acceso_url:
            return OneCitCitaOut(success=False, message="ERROR: Faltó la imagen en la respuesta de Control Acceso")

        # Crear el código de barras de asistencia
        codigo_barras = CodigoBarras(database)
        try:
            codigo_barras_num, codigo_barras_url = codigo_barras.crear_y_subir()
        except ConnectionError as e:
            # Captura errores de conexión o de la API de Google Storage
            return OneCitCitaOut(success=False, message=f"ERROR: Falló la comunicación para generar el código de barras de asistencia. {e}")
        except Exception as e:
            # Captura cualquier otro error inesperado durante la generación
            return OneCitCitaOut(success=False, message=f"ERROR: No se pudo generar el código de barras de asistencia. {e}")


    # Guardar
    cit_cita = CitCita(
        cit_cliente_id=cit_cliente.id,
        cit_servicio_id=cit_servicio.id,
        oficina_id=oficina.id,
        inicio=inicio_dt,
        termino=termino_dt,
        notas=safe_string(cit_cita_in.notas, max_len=1000, save_enie=True),
        estado="PENDIENTE",
        asistencia=False,
        codigo_asistencia=generar_codigo_asistencia(),
        codigo_acceso_id=codigo_acceso_id,
        codigo_acceso_url=codigo_acceso_url,
        cancelar_antes=cancelar_antes,
        codigo_barras=codigo_barras_num,
        codigo_barras_url=codigo_barras_url,
    )
    database.add(cit_cita)
    database.commit()
    database.refresh(cit_cita)

    # Creación de la plantilla para el email
    plantilla_email_cita_creada = PlantillaCitaCreada(
        id=str(cit_cita.id),
        nombre_cliente=cit_cita.cit_cliente.nombre,
        oficina=cit_cita.oficina_descripcion,
        servicio=cit_cita.cit_servicio_descripcion,
        fecha_hora_cita=cit_cita.inicio,
        notas=cit_cita.notas,
        codigo_qr_url=cit_cita.codigo_acceso_url,
        codigo_barras_url=cit_cita.codigo_barras_url,
    )

    # Envío de email
    send_email = Email(cit_cita.cit_cliente_email, plantilla_email_cita_creada)
    try:
        send_email.enviar_email()
    except MyRequestError as error:
        return OneCitCitaOut(success=False, message=str(error))

    # Entregar
    return OneCitCitaOut(
        success=True,
        message="Se ha creado la cita",
        data=CitCitaOut.model_validate(cit_cita),
    )


@cit_citas.get("/disponibles", response_model=int)
async def disponibles(
    current_user: Annotated[UsuarioInDB, Depends(get_current_active_user)],
    database: Annotated[Session, Depends(get_db)],
):
    """Cantidad de citas disponibles"""
    if current_user.permissions.get("CIT CITAS", 0) < Permiso.VER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    # Definir la cantidad máxima de citas
    limite = LIMITE_CITAS_PENDIENTES
    if current_user.limite_citas_pendientes > LIMITE_CITAS_PENDIENTES:
        limite = current_user.limite_citas_pendientes

    # Consultar la cantidad de citas PENDIENTES del cliente
    cantidad = (
        database.query(CitCita)
        .filter(CitCita.cit_cliente_id == current_user.id)
        .filter(CitCita.estado == "PENDIENTE")
        .filter(CitCita.estatus == "A")
        .count()
    )

    # Entregar la cantidad de citas disponibles que puede agendar
    if cantidad >= limite:
        return 0
    return limite - cantidad


@cit_citas.get("/mis_citas", response_model=CustomPage[CitCitaOut])
async def mis_citas(
    current_user: Annotated[UsuarioInDB, Depends(get_current_active_user)],
    database: Annotated[Session, Depends(get_db)],
    cit_cliente_id: str = None,
    curp: str = None,
):
    """Paginado de las citas con estado PENDIENTE, del futuro y de un cliente"""
    if current_user.permissions.get("CIT CITAS", 0) < Permiso.VER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    # Por defecto no hay cliente
    cit_cliente = None

    # Validar y consultar por cit_cliente_id
    if cit_cliente_id is not None and curp is None:
        try:
            cit_cliente_id = safe_uuid(cit_cliente_id)
        except ValueError:
            return CustomPage(success=False, message="No es válido el cit_cliente_id")
        cit_cliente = database.query(CitCliente).get(cit_cliente_id)
        if cit_cliente is None:
            return CustomPage(success=False, message="No existe ese cliente")

    # Validar y consultar por CURP
    if curp is not None and cit_cliente_id is None:
        try:
            curp = safe_curp(curp, is_optional=False, search_fragment=False)
        except ValueError:
            return CustomPage(success=False, message="No es válido el CURP")
        try:
            cit_cliente = database.query(CitCliente).filter_by(curp=curp).one()
        except (MultipleResultsFound, NoResultFound):
            return CustomPage(success=False, message="No existe un cliente con ese CURP")

    # Si no se proporcionó ninguno de los dos parámetros
    if cit_cliente is None:
        return CustomPage(success=False, message="No se proporcionó cit_cliente_id ni CURP, debe dar uno de los dos")

    # Validar que cliente NO esté deshabilitado
    if cit_cliente.estatus != "A":
        return CustomPage(success=False, message="No está habilitado ese cliente")

    # Consultar
    consulta = database.query(CitCita)

    # Filtar por el cliente
    consulta = consulta.filter(CitCita.cit_cliente_id == cit_cliente.id)

    # Filtrar por las citas del futuro. Solo mostrar las de hoy hacía futuro.
    hoy = date.today()
    consulta = consulta.filter(CitCita.inicio >= hoy)

    # Filtrar por el estado PENDIENTE
    consulta = consulta.filter(CitCita.estado.in_(["PENDIENTE", "ASISTIO"]))

    # Filtar por el estatus "A"
    consulta = consulta.filter(CitCita.estatus == "A")

    # Entregar
    return paginate(database,consulta.order_by(CitCita.inicio.desc()))


@cit_citas.get("/{cit_cita_id}", response_model=OneCitCitaOut)
async def detalle(
    current_user: Annotated[UsuarioInDB, Depends(get_current_active_user)],
    database: Annotated[Session, Depends(get_db)],
    cit_cita_id: str,
):
    """Detalle de una cita a partir de su ID"""
    if current_user.permissions.get("CIT CITAS", 0) < Permiso.VER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    try:
        cit_cita_id = safe_uuid(cit_cita_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No es válida la UUID")
    cit_cita = database.query(CitCita).get(cit_cita_id)
    if not cit_cita:
        return OneCitCitaOut(success=False, message="No existe esa cita")
    if cit_cita.estatus != "A":
        return OneCitCitaOut(success=False, message="No está habilitada esa cita")
    return OneCitCitaOut(success=True, message=f"Detalle de {cit_cita_id}", data=CitCitaOut.model_validate(cit_cita))


@cit_citas.get("", response_model=CustomPage[CitCitaOut])
async def paginado(
    current_user: Annotated[UsuarioInDB, Depends(get_current_active_user)],
    database: Annotated[Session, Depends(get_db)],
    cit_cliente_id: str = None,
    creado: date = None,
    creado_desde: date = None,
    creado_hasta: date = None,
    curp: str = None,
    email: str = None,
    estado: str = None,
    inicio: date = None,
    inicio_desde: date = None,
    inicio_hasta: date = None,
    oficina_clave: str = None,
):
    """Paginado de citas"""
    if current_user.permissions.get("CIT CITAS", 0) < Permiso.VER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    # Validar cit_cliente_id
    if cit_cliente_id is not None:
        try:
            cit_cliente_id = safe_uuid(cit_cliente_id)
        except ValueError:
            return CustomPage(success=False, message="No es válida la UUID")

    # Consultar
    consulta = database.query(CitCita)
    if cit_cliente_id is not None:
        consulta = consulta.filter(CitCita.cit_cliente_id == cit_cliente_id)

    # Filtrar por creado
    if creado is not None:
        desde_dt = datetime(year=creado.year, month=creado.month, day=creado.day, hour=0, minute=0, second=0)
        hasta_dt = datetime(year=creado.year, month=creado.month, day=creado.day, hour=23, minute=59, second=59)
        consulta = consulta.filter(CitCita.creado >= desde_dt).filter(CitCita.creado <= hasta_dt)
    if creado is None and creado_desde is not None:
        desde_dt = datetime(year=creado_desde.year, month=creado_desde.month, day=creado_desde.day, hour=0, minute=0, second=0)
        consulta = consulta.filter(CitCita.creado >= desde_dt)
    if creado is None and creado_hasta is not None:
        hasta_dt = datetime(
            year=creado_hasta.year, month=creado_hasta.month, day=creado_hasta.day, hour=23, minute=59, second=59
        )
        consulta = consulta.filter(CitCita.creado <= hasta_dt)

    # Filtrar por CURP y e-mail
    if curp is not None or email is not None:
        consulta = consulta.join(CitCliente)
        if curp is not None:
            try:
                curp = safe_curp(curp, is_optional=False, search_fragment=False)
                consulta = consulta.filter(CitCliente.curp == curp)
            except ValueError:
                return CustomPage(success=False, message="No es válido el CURP")
        if email is not None:
            try:
                email = safe_email(email, search_fragment=False)
                consulta = consulta.filter(CitCliente.email == email)
            except ValueError:
                return CustomPage(success=False, message="No es válido el e-mail")

    # Filtrar por estado
    if estado is not None:
        estado = safe_string(estado)
        if estado in CitCita.ESTADOS:
            consulta = consulta.filter(CitCita.estado == estado)

    # Filtrar por inicio
    if inicio is not None:
        desde_dt = datetime(year=inicio.year, month=inicio.month, day=inicio.day, hour=0, minute=0, second=0)
        hasta_dt = datetime(year=inicio.year, month=inicio.month, day=inicio.day, hour=23, minute=59, second=59)
        consulta = consulta.filter(CitCita.inicio >= desde_dt).filter(CitCita.inicio <= hasta_dt)
    if inicio is None and inicio_desde is not None:
        desde_dt = datetime(year=inicio_desde.year, month=inicio_desde.month, day=inicio_desde.day, hour=0, minute=0, second=0)
        consulta = consulta.filter(CitCita.inicio >= desde_dt)
    if inicio is None and inicio_hasta is not None:
        hasta_dt = datetime(
            year=inicio_hasta.year, month=inicio_hasta.month, day=inicio_hasta.day, hour=23, minute=59, second=59
        )
        consulta = consulta.filter(CitCita.inicio <= hasta_dt)

    # Filtrar por oficina_clave
    if oficina_clave is not None:
        oficina_clave = safe_clave(oficina_clave)
        if oficina_clave == "":
            return CustomPage(success=False, message="No es válida la clave de la oficina")
        consulta = consulta.join(Oficina).filter(Oficina.clave == oficina_clave)

    # Entregar
    return paginate(consulta.filter(CitCita.estatus == "A").order_by(CitCita.id.desc()))


@cit_citas.patch("/confirmar_cita", response_model=OneCitCitaConfirmadaOut)
async def confirmar_cita(
    current_user: Annotated[UsuarioInDB, Depends(get_current_active_user)],
    database: Annotated[Session, Depends(get_db)],
    cit_cita_codigo_barras: str,
):
    """Detalle de una cita a partir de su código de barras"""
    if current_user.permissions.get("CIT CITAS", 0) < Permiso.VER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    cit_cita = database.query(CitCita).filter_by(codigo_barras=cit_cita_codigo_barras).first()
    if not cit_cita:
        return OneCitCitaConfirmadaOut(success=False, message="ERROR: No existe esta cita")
    if cit_cita.estatus != "A":
        return OneCitCitaConfirmadaOut(success=False, message="ADVERTENCIA: No está habilitada esa cita")
    if cit_cita.inicio.date() != datetime.today().date():
        return OneCitCitaConfirmadaOut(success=False, message="ADVERTENCIA: Esta cita no es para el día de hoy.")
    if cit_cita.oficina.turnos_unidad_id is None:
        return OneCitCitaConfirmadaOut(success=False, message="ERROR: La oficina no tiene una unidad de turnos asignada.")
    if cit_cita.estado != "PENDIENTE" and cit_cita.estado != "ASISTIO":
        return OneCitCitaConfirmadaOut(success=False, message="ADVERTENCIA: Esta cita no está en un estado PENDIENTE")
    
    # Crear Turno
    resultado, mensaje = _crear_turno(cit_cita)
    if resultado == False:
        return OneCitCitaConfirmadaOut(success=False, message=f"Error en el sistema de turnos: {mensaje}")

    # Añadir asistencia
    cit_cita.asistencia = True
    cit_cita.estado = "ASISTIO"
    cit_cita.save()

    # Formar CitCitaConfirmadaOut
    cit_cita_confirmada = CitCitaConfirmadaOut(
        id=cit_cita.id,
        cit_cliente_nombre=cit_cita.cit_cliente.nombre,
        cit_cliente_telefono=cit_cita.cit_cliente.telefono,
        cit_cliente_email=cit_cita.cit_cliente.email,
        oficina_clave=cit_cita.oficina.clave,
        oficina_descripcion_corta=cit_cita.oficina.descripcion_corta,
        cit_servicio_clave=cit_cita.cit_servicio.clave,
        cit_servicio_descripcion=cit_cita.cit_servicio.descripcion,
        fecha=cit_cita.inicio.date(),
        hora_inicio=cit_cita.inicio.strftime("%I:%M %p").lower(),
        notas=cit_cita.notas,
        turno_codigo=cit_cita.turno,
    )
    return OneCitCitaConfirmadaOut(success=True, message=f"Cita confirmada de {cit_cita.id}", data=CitCitaConfirmadaOut.model_validate(cit_cita_confirmada))


def _crear_turno(cit_cita: CitCita) -> Tuple[bool, str]:
    """
    Crea un nuevo turno en el sistema de turnos
    :return El id del turno generado y el número de turno compuesto.
    """

    settings = get_settings()

    payload = {
        "usuario_id": settings.TURNOS_USUARIO_ID,
        "turno_tipo_id": settings.TURNOS_TIPO_ID,
        "turno_telefono": cit_cita.cit_cliente.telefono,
        "unidad_id": cit_cita.oficina.turnos_unidad_id,
        "comentarios": cit_cita.notas,
    }
    payload_json = json.dumps(payload)

    turnos = Turnos(settings)
    resultado, mensaje = turnos.crear_turno(payload_json)

    if resultado:
        cit_cita.turno_id = turnos.get_turno_id()
        cit_cita.turno = turnos.get_turno_codigo()
        cit_cita.save()

    return resultado, mensaje