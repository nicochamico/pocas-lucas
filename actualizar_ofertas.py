#!/usr/bin/env python3
"""
actualizar_ofertas.py
----------------------
Orquestador principal del radar de Pocas Lucas. Pensado para correr una
vez al día (cron) sobre un servidor con salida real a internet (tu
DigitalOcean, por ejemplo — este entorno de desarrollo no tiene acceso a
dominios de supermercados chilenos).

Qué hace, en orden:
  1. Carga el ofertas.json actual (si existe), agrupado por supermercado.
  2. Para cada tienda ACTIVA en scrapers/store_config.py, intenta traer
     productos reales con su conector (hoy: VTEX para Jumbo/Santa
     Isabel/Unimarc/Ekono).
  3. Si una tienda responde con productos válidos, reemplaza los datos
     de ESA tienda. Si falla o no está activa todavía, se CONSERVAN los
     datos que ya existían para esa tienda (reales o demo) — nunca se
     borran datos por una falla de red o de una fuente.
  4. Escribe ofertas.json con meta.es_demo=True solo si el conjunto
     completo sigue siendo 100% demo. Cada producto además trae su propio
     "es_demo", así que el sitio puede mostrar estados mixtos con
     precisión (ver index.html).
  5. Deja un log simple en actualizar_ofertas.log con qué pasó en cada
     corrida, para poder revisar fallas de días anteriores.

Cómo activar una tienda real:
  1. Verifica a mano, desde un ambiente con internet, que
     https://<dominio>/api/catalog_system/pub/products/search/despensa
     responde JSON con productos (o el equivalente que corresponda).
  2. En scrapers/store_config.py, cambia "activo": False a True para esa
     tienda.
  3. Corre este script y revisa ofertas.json y el log.

Ejecutar manualmente:
    python3 actualizar_ofertas.py

Preparar para cron diario (ejemplo, 6:00 AM todos los días):
    crontab -e
    0 6 * * * cd /ruta/al/proyecto && /usr/bin/python3 actualizar_ofertas.py >> cron.log 2>&1
"""

import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

from scrapers.store_config import STORES, CATEGORIAS
from scrapers.vtex_source import fetch_vtex_category, vtex_product_to_ofertas
from scrapers.utils import PoliteSession

OFERTAS_PATH = Path(__file__).parent / "ofertas.json"
LOG_PATH = Path(__file__).parent / "actualizar_ofertas.log"

CATEGORIAS_VALIDAS = set(CATEGORIAS.keys())


def log(msg):
    ts = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def cargar_ofertas_actuales():
    if not OFERTAS_PATH.exists():
        return {}, {}
    try:
        data = json.loads(OFERTAS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        log(f"AVISO: no se pudo leer ofertas.json existente ({e}), se parte de cero")
        return {}, {}

    por_tienda = {}
    for p in data.get("productos", []):
        por_tienda.setdefault(p["supermercado"], []).append(p)
    return por_tienda, data.get("meta", {})


def validar_producto(p):
    campos = ["id", "supermercado", "nombre", "categoria", "precio_actual",
              "precio_anterior", "descuento_pct", "actualizado", "fuente", "es_demo"]
    for c in campos:
        if c not in p:
            raise ValueError(f"Producto sin campo '{c}': {p.get('id', '?')}")
    if p["categoria"] not in CATEGORIAS_VALIDAS:
        raise ValueError(f"Categoría inválida '{p['categoria']}' en {p['id']}")
    if p["precio_actual"] <= 0 or p["precio_anterior"] <= 0:
        raise ValueError(f"Precio inválido en {p['id']}")
    datetime.fromisoformat(p["actualizado"])  # lanza excepción si está mal formada


def fetch_tienda_vtex(store_key, store_cfg):
    """Intenta traer productos reales de una tienda VTEX. Devuelve lista (puede ser [])."""
    session = PoliteSession(min_delay=0.7, max_retries=1)
    productos = []
    vistos = set()

    # Preflight rápido: si ni siquiera responde una búsqueda básica, no
    # recorremos todas las categorías. Así una fuente caída no demora minutos.
    try:
        prueba = fetch_vtex_category(session, store_cfg["dominio"], "arroz", max_items=3)
    except Exception as e:
        log(f"  [{store_cfg['nombre']}] preflight VTEX falló: {e}")
        return []
    if not prueba:
        log(f"  [{store_cfg['nombre']}] preflight VTEX sin productos")
        return []

    for cat_id, cat_info in CATEGORIAS.items():
        for termino in cat_info["terminos_busqueda"]:
            try:
                crudos = fetch_vtex_category(session, store_cfg["dominio"], termino, max_items=24)
            except Exception as e:
                log(f"  [{store_cfg['nombre']}] búsqueda '{termino}' falló: {e}")
                continue

            for raw in crudos:
                item = vtex_product_to_ofertas(
                    raw,
                    store_cfg["nombre"],
                    cat_id,
                    cat_info["label"],
                    cat_info["icono"],
                    domain=store_cfg["dominio"],
                )
                if not item:
                    continue
                if item["id"] in vistos:
                    continue
                vistos.add(item["id"])
                productos.append(item)

    return productos


FETCHERS = {
    "vtex": fetch_tienda_vtex,
}


def actualizar():
    datos_previos_por_tienda, meta_previa = cargar_ofertas_actuales()
    resultado_por_tienda = {}
    tiendas_con_error = []
    tiendas_actualizadas = []

    for store_key, store_cfg in STORES.items():
        nombre = store_cfg["nombre"]

        if not store_cfg["activo"]:
            resultado_por_tienda[nombre] = datos_previos_por_tienda.get(nombre, [])
            log(f"{nombre}: inactiva (conector '{store_cfg['conector']}'), se mantienen "
                f"{len(resultado_por_tienda[nombre])} productos previos")
            continue

        fetcher = FETCHERS.get(store_cfg["conector"])
        if fetcher is None:
            resultado_por_tienda[nombre] = datos_previos_por_tienda.get(nombre, [])
            log(f"{nombre}: conector '{store_cfg['conector']}' sin implementación, "
                f"se mantienen datos previos")
            continue

        try:
            productos_nuevos = fetcher(store_key, store_cfg)
        except Exception:
            tiendas_con_error.append(nombre)
            resultado_por_tienda[nombre] = datos_previos_por_tienda.get(nombre, [])
            log(f"{nombre}: FALLÓ la actualización, se conservan "
                f"{len(resultado_por_tienda[nombre])} productos previos.\n"
                f"{traceback.format_exc()}")
            continue

        if not productos_nuevos:
            resultado_por_tienda[nombre] = datos_previos_por_tienda.get(nombre, [])
            log(f"{nombre}: la fuente respondió sin productos válidos, se conservan "
                f"{len(resultado_por_tienda[nombre])} productos previos")
            continue

        resultado_por_tienda[nombre] = productos_nuevos
        tiendas_actualizadas.append(nombre)
        log(f"{nombre}: OK, {len(productos_nuevos)} productos reales actualizados")

    todos = [p for lista in resultado_por_tienda.values() for p in lista]

    for p in todos:
        validar_producto(p)

    ahora = datetime.now(timezone.utc).astimezone()
    todos_demo = all(p.get("es_demo") for p in todos) if todos else True

    payload = {
        "meta": {
            "generado_el": ahora.isoformat(),
            "total_productos": len(todos),
            "es_demo": todos_demo,
            "aviso": (
                "Estos son datos de DEMOSTRACION. No representan precios reales."
                if todos_demo else None
            ),
            "supermercados": sorted({p["supermercado"] for p in todos}),
            "categorias": [
                {"id": k, "label": v["label"], "icono": v["icono"]}
                for k, v in CATEGORIAS.items()
            ],
            "tiendas_actualizadas_ultima_corrida": tiendas_actualizadas,
            "tiendas_con_error_ultima_corrida": tiendas_con_error,
        },
        "productos": todos,
    }

    OFERTAS_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log(f"ofertas.json escrito con {len(todos)} productos "
        f"({len(tiendas_actualizadas)} tiendas actualizadas, "
        f"{len(tiendas_con_error)} con error)")


if __name__ == "__main__":
    try:
        actualizar()
    except Exception:
        log(f"ERROR FATAL, no se modificó ofertas.json:\n{traceback.format_exc()}")
        sys.exit(1)
