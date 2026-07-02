#!/usr/bin/env python3
"""
verificar_fuentes.py
--------------------
Prueba rápidamente, desde TU servidor, si las fuentes configuradas responden.
No modifica ofertas.json. Sirve antes de activar nuevas tiendas o revisar fallas.

Uso:
    python3 verificar_fuentes.py
"""

from scrapers.store_config import STORES, CATEGORIAS
from scrapers.utils import PoliteSession
from scrapers.vtex_source import fetch_vtex_search


def main():
    session = PoliteSession(min_delay=0.5, max_retries=1)
    terminos = ["arroz", "detergente", "leche"]

    for key, cfg in STORES.items():
        print(f"\n== {cfg['nombre']} ({cfg['dominio']}) ==")
        if cfg["conector"] != "vtex":
            print(f"Conector: {cfg['conector']} — no se prueba automáticamente.")
            continue

        total = 0
        for termino in terminos:
            try:
                data = fetch_vtex_search(session, cfg["dominio"], termino, max_items=5)
                print(f"  {termino}: OK, {len(data)} productos crudos")
                total += len(data)
            except Exception as e:
                print(f"  {termino}: FALLÓ — {e}")
        if total:
            print("  Resultado: fuente candidata OK. Puede quedar activo=True.")
        else:
            print("  Resultado: no se obtuvo JSON VTEX usable desde este servidor.")


if __name__ == "__main__":
    main()
