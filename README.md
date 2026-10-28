# 🏛️ pjecz-casiopea-api-key

> Aplicación tipo API para la comunicación con el sistema de gestión SAJI y Kiosko.

Proyectos relacionados:
- [pjecz-casiopea-api-oauth2](https://github.com/PJECZ/pjecz-casiopea-api-oauth2)
- [pjecz-casiopea-api-key](https://github.com/PJECZ/pjecz-casiopea-api-key)
- [pjecz-casiopea-reactjs](https://github.com/PJECZ/pjecz-casiopea-reactjs)

---

## 📖 Descripción General

Es parte de un conjunto de proyectos para hacer funcionar el sistema de Citas al cual acceder el público. En esta API hacemos que el sistema de gestión SAJI se comunique con este sistema, creado citas, cancelandolas o listando las citas para cada persona.

## 🛠️ Tecnologías Utilizadas

* **Lenguaje:** Python v3.14
* **Framework:** FastAPI
* **Base de Datos:** PostgreSQL v15.19
* **Servidor:** Nginx
* **Otros:** Sendgrid

## ⚙️ Requisitos Previos

Lista de herramientas necesarias para correr el proyecto localmente:
- Git
- Python
- uv - manejador de paquetes para Python

## 🚀 Instalación y Configuración

### 1. Clonar el repositorio:

```bash
git clone https://github.com/PJECZ/pjecz-casiopea-api-key.git
cd pjecz-casiopea-api-key
```

### 2. Configurar variables de entorno:

Copia el archivo de ejemplo y edita las credenciales necesarias (Base de datos, API Keys):
```
cp .env.example .env
```

### 3. Instalar dependencias:

```bash
uv sync
```

### 4. Iniciar el servidor de desarrollo:

```bash
uv run uvicorn --host=0.0.0.0 --port=8001 --reload pjecz_casiopea_api_key.main:app
```

## 🌿 Estructura de Ramas

Este proyecto sigue el flujo de trabajo institucional:
- `main`: Rama de producción (Solo código estable).
- `dev`: Rama de integración y pruebas (_Staging_).
- `feature/*`: Ramas temporales para nuevas funcionalidades.

Ver más sobre como contribuir: [CONTRIBUTING](CONTRIBUTING.md)

## 🚢 Despliegue

Ejecutar comando en servidor de producción después de haber integrado el PR en la rama `dev`:

```bash
actualizar-proyecto-casiopea
```

---

## ✉️ Contacto

- **Departamento:** Dirección de Informática - PJECZ
- **Responsable:** Dir. Guillermo Valdés, Lucía Aranda y Ricardo Valdés
- **Email:** [correo@pjecz.gob.mx]

---

© 2026 Poder Judicial del Estado de Coahuila de Zaragoza.
