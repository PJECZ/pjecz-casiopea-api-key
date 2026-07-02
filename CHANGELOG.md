# 📝 Historial de Cambios (Changelog)

Todos los cambios notables en este proyecto serán documentados en este archivo.
El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

## [1.5.0] - 2026-07-02 (Trabajando)

### ✨ Mejoras

- Añadido parámetro opcional en _endpoint_ `confirmar_cita` para evitar validar la fecha y hora de la cita.
- Incluir los campos `unidad_id`, `codigo_acceso_id` y `turno_id` en la respuesta del _endpoint_ `confirmar_cita`.
- Se mejoró el código de barras, ahora se utiliza el primer dígito como personalizado para definir la aplicación _backend_ que lo crea y a la cual debe comunicarse el _frontend_ cuando lo lea.
- Se entrega el campo `codigo_acceso_url_whatsapp` en el _endpoint_ `confirmar_cita`.
- Nuevo campo `codigo_acceso_url_whatsapp` en la tabla `cit_citas`. Para almacenar la dirección del QR que se envía vía WhatsApp, y es entregada por el sistema de Control de Accesos.
- Nuevo _endpoint_ `confirmar_cita`. Al recibir el número de código de asistencia, se marca la asistencia y se genera un turno en el sistema de turnos, y se regresa toda esa información como resultado de la petición. Si ya existe la asistencia y el turno, solo regresar la información.

### 🐞 Arreglado

- En el _endpoint_ `cit-días-disponibles`, si se proporcionan `oficina_clave` y `cit_servicio_clave`, se filtran los días que ya no tienen horas disponibles para ese servicio en esa oficina.
- Al consultar las horas disponibles, el límite de citas se aplica por servicio-oficina y no por oficina en general.

### ⚙️ Requerimientos

- Añadir campo `codigo_acceso_url_whatsapp` a la tabla `cit_citas`:
    - `v1.5.0-01-Add-Campo-cit_citas.sql`.


## [1.4.2] - 2026-06-11

### 🛠️ Cambios

- En la entrega de límite de citas, no contar las citas pasadas.


## [1.4.1] - 2026-06-04

### 🛠️ Cambios

- Cambio de texto en las plantillas de email "Código de Barras" por "Código de Asistencia".
- Cambio de texto en las plantillas de email "Código QR" por "Código de Acceso".


## [1.4.0] - 2026-05-29

### ✨ Mejoras

- Al entregar las citas agendadas de un cliente, mostrar las que se encuentran en estado de "Pendiente" o en "Asistió". Para que en caso de que este siendo atendido en su cita actual, la mantenga activa por ese día.
- Al enviar el email de cita_creada si la oficina no tiene activo del campo de `pude_enviar_qr`. No genera ni envía los códigos de acceso (QR y Barras).
- Validar el campo booleano `oficinas.puede_enviar_qr` para incluir el código QR y código de barras de asistencia en los emails al crear una cita.
- Añadido campos nuevos al modelo de `cit_citas` para almacenar el código de barras de asistencia.
- Nuevo servicio para creación de un código de barras para identificar la cita.

### ❌ Eliminado

- Código de asistencia en la plantilla de email al crear una cita nueva.

### ⚙️ Requerimientos

- Añadir paquetes de librerías con `uv add [lib]`:
    - `python-barcode pillow`
    - `google-cloud-storage`

- Añadir nuevas variables de entorno. Para almacenamiento del código de barras generado como imagen.
    - `GOOGLE_APPLICATION_CREDENTIALS`
    - `GCS_BUCKET_NAME`


## [1.3.0] - 2026-05-22

### ✨ Mejoras

- Añadido _endpoint_ `exp_juzgados`. Para entrega de los juzgados de los que se pueden pedir expedientes, en el servicio de "revisión de expedientes" preferentemente para la unidad de "Archivo".
- Mejora en el formato del archivo `README.md`.
- Mensaje de requisitos en plantilla para cita creada. "_Debes presentar tu credencial de identificación (INE) vigente_".
- Añadido campo `instrucciones` al modelo `cit_servicios` y añadirlo en la entrega de su _endpoint_.
- Descripción de la versión en la documentación _swagger_ hecha por defecto.

### 🛠️ Cambios

- El límite por defecto para el paginado subió de `10` a `25`.

## [1.2.0] - 2026-05-20

### ✨ Mejoras

- Creación de plantillas para diferentes envíos de email, al crear y canelar citas.
- Uso de plantillas para envío de emails.
- Creación de servicio de envío de emails con plantillas.
- Documentación en 'README.md', 'CONTRIBUTING.md' y este 'CHANGELOG.md'.

### 🛠️ Cambios

- Cambiar asunto de email de PJECZ a SAJI.


## [0.1.2] - 2026-05-07

### ✨ Mejoras

- Utilización de `uv` como manejador de paquetes de **Python**.
