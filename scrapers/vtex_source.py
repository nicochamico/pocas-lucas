"""
scrapers/vtex_source.py
-----------------------
Conector genérico para tiendas VTEX.

Usa la Search API pública de VTEX:
    /api/catalog_system/pub/products/search
con búsqueda full-text y paginación _from/_to.

No inventa productos. Si la tienda no responde con JSON VTEX válido,
devuelve lista vacía y el orquestador conserva datos previos.
"""

from datetime import datetime, timezone
from urllib.parse import quote, urlparse

from .utils import PoliteSession, clamp_discount, slugify, is_restricted_product

PAGE_SIZE = 24
MAX_PAGES_PER_TERM = 2


def _product_url(domain, raw_product):
    """Construye URL pública desde link/linkText VTEX, sin inventar dominios."""
    link = raw_product.get("link")
    if link:
        return link
    link_text = raw_product.get("linkText", "")
    if link_text:
        return f"https://{domain}/{link_text}/p"
    return f"https://{domain}"


def _iter_sku_offers(raw_product):
    """Genera ofertas VTEX de todos los SKUs/sellers disponibles."""
    for sku in raw_product.get("items", []) or []:
        for seller in sku.get("sellers", []) or []:
            offer = seller.get("commertialOffer") or {}
            yield sku, seller, offer


def fetch_vtex_search(session: PoliteSession, domain, search_term, max_items=48):
    """
    Busca productos por término usando query params (_from/_to), que suele
    ser más estable que depender de slugs de categoría específicos.
    """
    items = []
    term = quote(search_term)
    for page in range(MAX_PAGES_PER_TERM):
        start = page * PAGE_SIZE
        end = start + PAGE_SIZE - 1
        urls = [
            f"https://{domain}/api/catalog_system/pub/products/search?ft={term}&_from={start}&_to={end}",
            f"https://{domain}/api/catalog_system/pub/products/search/{term}?_from={start}&_to={end}",
        ]
        page_data = None
        last_error = None
        for url in urls:
            try:
                resp = session.get(url)
                data = resp.json()
                if isinstance(data, list):
                    page_data = data
                    break
            except Exception as e:
                last_error = e
                continue
        if page_data is None:
            print(f"[vtex:{domain}] sin JSON válido para '{search_term}' pág {page}: {last_error}")
            break
        if not page_data:
            break
        items.extend(page_data)
        if len(items) >= max_items:
            break
    return items[:max_items]


# Compatibilidad con el nombre anterior usado por actualizar_ofertas.py.
def fetch_vtex_category(session: PoliteSession, domain, category_term, max_items=48):
    return fetch_vtex_search(session, domain, category_term, max_items=max_items)


def vtex_product_to_ofertas(raw_product, store_nombre, categoria_id, categoria_label,
                             categoria_icono, domain=None, unidad_default="unidad"):
    """
    Convierte un producto VTEX al esquema de Pocas Lucas.
    Devuelve None si no hay precio válido, stock, oferta real o si el producto
    cae en una categoría que no queremos mostrar.
    """
    nombre = raw_product.get("productName", "Producto sin nombre")
    if is_restricted_product(nombre):
        return None

    product_id = raw_product.get("productId") or raw_product.get("linkText") or slugify(nombre)
    best = None

    for sku, seller, offer in _iter_sku_offers(raw_product):
        try:
            precio_actual = float(offer.get("Price") or 0)
            precio_anterior = float(offer.get("ListPrice") or precio_actual)
            disponible = offer.get("IsAvailable", True)
            stock = offer.get("AvailableQuantity", 1)
        except (TypeError, ValueError):
            continue

        if not disponible or stock == 0:
            continue
        if precio_actual <= 0 or precio_anterior <= 0:
            continue
        if precio_actual >= precio_anterior:
            continue

        if best is None or precio_actual < best[0]:
            best = (precio_actual, precio_anterior)

    if best is None:
        return None

    precio_actual, precio_anterior = best
    now = datetime.now(timezone.utc).astimezone().isoformat()
    safe_store = slugify(store_nombre)
    url = _product_url(domain or urlparse(raw_product.get("link", "")).netloc or "", raw_product)

    return {
        "id": f"{safe_store}-{product_id}",
        "supermercado": store_nombre,
        "nombre": nombre,
        "categoria": categoria_id,
        "categoria_label": categoria_label,
        "categoria_icono": categoria_icono,
        "precio_actual": round(precio_actual),
        "precio_anterior": round(precio_anterior),
        "descuento_pct": clamp_discount(precio_actual, precio_anterior),
        "unidad_precio": unidad_default,
        "actualizado": now,
        "url_oferta": url,
        "fuente": f"{domain or store_nombre} (VTEX)",
        "es_demo": False,
    }
