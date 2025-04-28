"""
PJECZ Casiopea API Key
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination

from .settings import get_settings

from .routers.autoridades import autoridades
from .routers.bitacoras import bitacoras
from .routers.cit_categorias import cit_categorias
from .routers.cit_citas import cit_citas
from .routers.cit_clientes import cit_clientes
from .routers.cit_clientes_recuperaciones import cit_clientes_recuperaciones
from .routers.cit_clientes_registros import cit_clientes_registros
from .routers.cit_dias_inhabiles import cit_dias_inhabiles
from .routers.cit_horas_bloqueadas import cit_horas_bloqueadas
from .routers.cit_oficinas_servicios import cit_oficinas_servicios
from .routers.cit_servicios import cit_servicios
from .routers.distritos import distritos
from .routers.domicilios import domicilios
from .routers.entradas_salidas import entradas_salidas
from .routers.modulos import modulos
from .routers.oficinas import oficinas
from .routers.permisos import permisos
from .routers.roles import roles
from .routers.usuarios import usuarios
from .routers.usuarios_oficinas import usuarios_oficinas
from .routers.usuarios_roles import usuarios_roles


# FastAPI
app = FastAPI(
    title="PJECZ Casiopea API Key",
    description="API con autentificación para realizar operaciones con la base de datos del sistema de citas.",
    docs_url="/docs",
    redoc_url=None,
)

# CORSMiddleware
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins.split(","),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Rutas
app.include_router(autoridades, tags=["autoridades"])
app.include_router(bitacoras, include_in_schema=False)
app.include_router(cit_categorias, tags=["citas"])
app.include_router(cit_citas, tags=["citas"])
app.include_router(cit_clientes, tags=["citas"])
app.include_router(cit_clientes_recuperaciones, tags=["citas"])
app.include_router(cit_clientes_registros, tags=["citas"])
app.include_router(cit_dias_inhabiles, tags=["citas"])
app.include_router(cit_horas_bloqueadas, tags=["citas"])
app.include_router(cit_oficinas_servicios, tags=["citas"])
app.include_router(cit_servicios, tags=["citas"])
app.include_router(distritos, tags=["autoridades"])
app.include_router(domicilios, tags=["oficinas"])
app.include_router(entradas_salidas, include_in_schema=False)
app.include_router(modulos, include_in_schema=False)
app.include_router(oficinas, tags=["oficinas"])
app.include_router(permisos, include_in_schema=False)
app.include_router(roles, include_in_schema=False)
app.include_router(usuarios, tags=["usuarios"])
app.include_router(usuarios_oficinas, include_in_schema=False)
app.include_router(usuarios_roles, include_in_schema=False)

# Paginación
add_pagination(app)


# Mensaje de Bienvenida
@app.get("/")
async def root():
    """Mensaje de Bienvenida"""
    return {"message": "API con autentificación para realizar operaciones con la base de datos del sistema de citas."}
