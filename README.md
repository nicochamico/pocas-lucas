# Pocas Lucas — radar automático de ofertas

Proyecto listo para GitHub + Netlify.

La idea es simple:

1. `index.html` muestra la web.
2. `ofertas.json` contiene los productos que se ven en el sitio.
3. `actualizar_ofertas.py` intenta obtener precios reales desde fuentes configuradas.
4. GitHub Actions ejecuta el script todos los días y actualiza `ofertas.json`.
5. Netlify publica automáticamente la nueva versión cuando el repositorio cambia.

## Estado actual

- Jumbo: activo con conector VTEX.
- Santa Isabel: activo con conector VTEX.
- Unimarc y Ekono: preparados, pero inactivos hasta verificar endpoint estable.
- Líder y Tottus: inactivos; no hay API pública equivalente confirmada.
- Si una fuente falla, el script conserva los datos anteriores y no borra productos por error.
- Si los productos siguen siendo demo, la web muestra aviso DEMO automáticamente.
- Si aparecen productos reales, la web cambia sola a estado real o mixto.

## Archivos principales

```text
index.html                         Web estática
ofertas.json                       Datos visibles en la web
actualizar_ofertas.py              Orquestador de actualización
verificar_fuentes.py               Prueba rápida de endpoints
scrapers/store_config.py           Tiendas activas/inactivas
scrapers/vtex_source.py            Conector VTEX
scrapers/utils.py                  Requests, robots.txt, rate limit
requirements.txt                   Dependencias Python
.github/workflows/actualizar-ofertas.yml  Automatización diaria
netlify.toml                       Configuración Netlify
```

## Crear el repositorio en GitHub

1. Crea un repositorio nuevo, por ejemplo `pocas-lucas`.
2. Sube todos los archivos de esta carpeta.
3. En GitHub, entra a **Actions**.
4. Ejecuta manualmente el workflow **Actualizar ofertas** con **Run workflow**.
5. Revisa el log para ver si Jumbo o Santa Isabel devuelven productos reales.

El workflow también queda programado para correr todos los días a las 10:00 UTC.

## Conectar Netlify al repo

1. En Netlify: **Add new project**.
2. Elige **Import an existing project**.
3. Selecciona GitHub y el repositorio `pocas-lucas`.
4. Build command: dejar vacío.
5. Publish directory: `.`
6. Publicar.

Desde ese momento, cada cambio en `ofertas.json` redepliega el sitio.

## Probar localmente

No abras `index.html` con doble clic, porque `fetch()` no carga `ofertas.json` desde `file://`.

Usa:

```bash
python3 -m http.server 8080
```

Luego abre:

```text
http://localhost:8080
```

## Ejecutar actualización manual

```bash
python3 -m pip install -r requirements.txt
python3 verificar_fuentes.py
python3 actualizar_ofertas.py
```

Luego abre `ofertas.json` y revisa si hay productos con:

```json
"es_demo": false
```

## Activar otras tiendas

Editar:

```text
scrapers/store_config.py
```

Cambiar una tienda a:

```python
"activo": True
```

Solo hacerlo después de confirmar que el endpoint devuelve JSON usable.
