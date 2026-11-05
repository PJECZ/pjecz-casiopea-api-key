# Cómo hacer un _deploy_

Instrucciones de como hacer un _deploy_ de un proyecto alojado en **GitHub** con el flujo de trabajo **GitFlow - Simplificado**

## Procedimiento para hacer un _deploy_

### 01. Hacer última entrega

1. Abre tu proyecto de desarrollo en tu rama `dev`. 
2. Crea una rama llamada `release/v1.5.0` para indicar la última entrega a la rama. El número de versión, es el número que vas a entregar.
3. Ve al archivo `CHANGELOG` y coloca la **fecha de publicación** después del número de versión más actual. La fecha debería estar en formato: `YYYY-MM-DD`.
   **Ejemplo**: `## [1.5.0] - 2026-10-28`.
4. Haz un búsqueda dentro del proyecto para ver si la fecha de publicación de la última versión se muestra en otra parte del proyecto, si es así también cámbiala.
5. Haz el **Pull Request** a la rama `dev` institucional. Como **título** escribe: `deploy v1.5.0` y cómo **descripción**, añade todo el apartado del archivo `CHANGELOG` de la versión a entregar.

### 02. Hacer _merge_ del _deploy_

1. Haz el _merge_ del último cambio enviado de la rama `dev -> dev`.
2. Ve a la cuenta institucional y haz un nuevo **Pull Request** de la rama `dev -> main`.
3. Igual que antes haz el **Pull Request** de la rama `dev` institucional. Como **título** escribe: `deploy v1.5.0` y cómo **descripción**, añade todo el apartado del archivo `CHANGELOG` de la versión a entregar. La entrega debe ser desde y para el repositorio institucional `dev -> main`.

### 03. Actualizar rama `dev`

1. Haz un nuevo **Pull Request** dentro del repositorio institucional ahora de `main -> dev`. Esto hará que se actualice `dev` con los últimos cambios de `main` . Cómo título puedes poner: "Actualización de último deploy". 

### 04. Añadir _tag_ de versión

1. En **GitHub** en la cuenta institucional. Presiona sobre la etiqueta **Tags**. Se encuentra a la derecha del selector de ramas.
2. Presiona sobre el botón de **Releases**. Y una vez ahí, presiona el botón **Draft a new release** que se encuentra cargado a la derecha.
3. En la página de **New release**, en el _select tag_ , crea un nuevo tag. Utiliza el nombre: `v1.5.0`. El _Select Target_ elige la rama `main`. Como **título** coloca: `v1.5.0 (2026-10-28)` y en **descripción** pega todo el apartado del archivo `CHANGELOG` de la versión a entregar. 
4. Ahora actualizar tus _Forks_ tanto de las ramas `main` y `dev`.
5. Baja cambios en tu equipo local.

### 05. Actualizar proyecto en servidor de PRODUCCION

2. Baja cambios en el servidor de producción y efectúa las migraciones indicadas si las hay en el archivo `CHANGELOG`.
3. Verifica que todo esté bien.
4. Ahora puedes comunicar al equipo que pueden bajar cambios, que actualicen sus _Forks_ en sus dos ramas `main` y `dev`.



