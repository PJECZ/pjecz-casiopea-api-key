"""
Domicilios, routers
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_pagination.ext.sqlalchemy import paginate

from ..dependencies.authentications import UsuarioInDB, get_current_active_user
from ..dependencies.database import Session, get_db
from ..dependencies.fastapi_pagination_custom_page import CustomPage
from ..dependencies.safe_string import safe_uuid
from ..models.domicilios import Domicilio
from ..models.permisos import Permiso
from ..schemas.domicilios import DomicilioOut, OneDomicilioOut

domicilios = APIRouter(prefix="/api/v5/domicilios")


@domicilios.get("/{domicilio_id}", response_model=OneDomicilioOut)
async def detalle_domicilios(
    current_user: Annotated[UsuarioInDB, Depends(get_current_active_user)],
    database: Annotated[Session, Depends(get_db)],
    domicilio_id: str,
):
    """Detalle de un domicilio a partir de su ID"""
    if current_user.permissions.get("DOMICILIOS", 0) < Permiso.VER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    try:
        domicilio_id = safe_uuid(domicilio_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No es válida la UUID")
    domicilio = database.query(Domicilio).get(domicilio_id)
    if not domicilio:
        return OneDomicilioOut(success=False, message="No existe ese domicilio")
    if domicilio.estatus != "A":
        return OneDomicilioOut(success=False, message="No está habilitado ese domicilio")
    return OneDomicilioOut(success=True, message=f"Detalle de {domicilio_id}", data=DomicilioOut.model_validate(domicilio))


@domicilios.get("", response_model=CustomPage[DomicilioOut])
async def paginado_domicilios(
    current_user: Annotated[UsuarioInDB, Depends(get_current_active_user)],
    database: Annotated[Session, Depends(get_db)],
):
    """Paginado de domicilios"""
    if current_user.permissions.get("DOMICILIOS", 0) < Permiso.VER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return paginate(database.query(Domicilio).filter_by(estatus="A").order_by(Domicilio.edificio))
