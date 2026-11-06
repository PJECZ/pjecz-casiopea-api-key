"""
Exp Juzgados, routers
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.exc import MultipleResultsFound, NoResultFound

from ..dependencies.authentications import UsuarioInDB, get_current_active_user
from ..dependencies.database import Session, get_db
from ..dependencies.fastapi_pagination_custom_page import CustomPage
from ..dependencies.safe_string import safe_clave
from ..models.exp_juzgados import ExpJuzgado
from ..models.permisos import Permiso
from ..schemas.exp_juzgados import ExpJuzgadoOut, OneExpJuzgadoOut

exp_juzgados = APIRouter(prefix="/api/v5/exp_juzgados")


@exp_juzgados.get("/{clave}", response_model=OneExpJuzgadoOut)
async def detalle(
    current_user: Annotated[UsuarioInDB, Depends(get_current_active_user)],
    database: Annotated[Session, Depends(get_db)],
    clave: str,
):
    """Detalle de un juzgado para expedientes a partir de su clave"""
    if current_user.permissions.get("EXP JUZGADOS", 0) < Permiso.VER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    try:
        clave = safe_clave(clave)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No es válida la clave")
    try:
        exp_juzgado = database.query(ExpJuzgado).filter_by(clave=clave).one()
    except (MultipleResultsFound, NoResultFound):
        return OneExpJuzgadoOut(success=False, message="No existe ese juzgado")
    if exp_juzgado.estatus != "A":
        return OneExpJuzgadoOut(success=False, message="Ese juzgado está eliminado")
    return OneExpJuzgadoOut(success=True, message=f"Detalle de {clave}", data=ExpJuzgadoOut.model_validate(exp_juzgado))


@exp_juzgados.get("", response_model=CustomPage[ExpJuzgadoOut])
async def paginado(
    current_user: Annotated[UsuarioInDB, Depends(get_current_active_user)],
    database: Annotated[Session, Depends(get_db)],
):
    """Paginado de exp-juzgados"""
    if current_user.permissions.get("EXP JUZGADOS", 0) < Permiso.VER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return paginate(database.query(ExpJuzgado).filter(ExpJuzgado.estatus == "A").order_by(ExpJuzgado.descripcion))
