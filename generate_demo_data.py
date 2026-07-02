#!/usr/bin/env python3
"""
generate_demo_data.py
----------------------
Genera ofertas.json con datos DE DEMOSTRACIÓN (no son precios reales).
Sirve para poblar el radar de Pocas Lucas con 100-150 productos mientras
no hay una fuente de datos real conectada.

Uso:
    python3 generate_demo_data.py

Produce: ofertas.json en el mismo directorio.

IMPORTANTE: todos los productos generados llevan "fuente": "demo" y
"es_demo": true. Cuando exista una fuente real, ese campo debe pasar a
"fuente": "<nombre de la fuente>" y "es_demo": false. Ver actualizar_ofertas.py
para el script que reemplazará a este generador.
"""

import json
import random
from datetime import datetime, timedelta, timezone

random.seed(42)  # reproducible

STORES = [
    {"nombre": "Jumbo", "url": "https://www.jumbo.cl"},
    {"nombre": "Líder", "url": "https://www.lider.cl"},
    {"nombre": "Santa Isabel", "url": "https://www.santaisabel.cl"},
    {"nombre": "Unimarc", "url": "https://www.unimarc.cl"},
    {"nombre": "Tottus", "url": "https://www.tottus.cl"},
    {"nombre": "Ekono", "url": "https://www.ekono.cl"},
]

# categoria_id: (etiqueta, icono, rango_precio_clp, [(nombre, unidad), ...])
CATEGORIES = {
    "despensa": ("Despensa", "🍚", (700, 6000), [
        ("Aceite Chef Vegetales 1L", "$/L"),
        ("Arroz Tucapel Grado 1 1kg", "$/kg"),
        ("Fideos Carozzi Spaghetti 400g", "$/kg"),
        ("Azúcar Iansa 1kg", "$/kg"),
        ("Harina Selecta 1kg", "$/kg"),
        ("Café Nescafé Tradición 170g", "$/kg"),
        ("Atún Robinson Crusoe en Agua 170g", "unidad"),
        ("Lentejas Tattersall 400g", "$/kg"),
        ("Salsa de Tomate Maggi 500g", "unidad"),
        ("Té Supremo 25 bolsitas", "unidad"),
        ("Miel de Palma Bonasa 500g", "unidad"),
        ("Mermelada Watts Frutilla 300g", "unidad"),
    ]),
    "aseo": ("Aseo", "🧽", (800, 9500), [
        ("Papel Higiénico Elite 30un", "$/rollo"),
        ("Detergente Omo Líquido 3kg", "$/kg"),
        ("Cloro Clorinda 1L", "$/L"),
        ("Lavaloza Quix 750ml", "$/L"),
        ("Jabón en Barra Popeye 5un", "unidad"),
        ("Suavizante Comfort 1.8L", "$/L"),
        ("Toalla de Papel Nova 4un", "unidad"),
        ("Esponja Scotch Brite 3un", "unidad"),
        ("Limpiador Multiuso Mr Músculo 500ml", "unidad"),
        ("Bolsas de Basura Renova 30un", "unidad"),
    ]),
    "bebidas": ("Bebidas sin alcohol", "🥤", (700, 5500), [
        ("Bebida Coca-Cola 1.5L", "$/L"),
        ("Jugo Watts Néctar Durazno 1L", "$/L"),
        ("Agua Mineral Cachantún 1.5L", "$/L"),
        ("Bebida Sprite 1.5L", "$/L"),
        ("Jugo en Polvo Kapo 500g", "unidad"),
        ("Té Helado Lipton 1.5L", "$/L"),
        ("Bebida Isotónica Powerade 500ml", "unidad"),
    ]),
    "lacteos": ("Lácteos", "🥛", (900, 4800), [
        ("Leche Soprole Entera 1L", "$/L"),
        ("Yoghurt Yoghu 1kg", "$/kg"),
        ("Queso Gauda Colún 400g", "$/kg"),
        ("Mantequilla Watts 250g", "$/kg"),
        ("Crema Nestlé 200ml", "unidad"),
        ("Leche Condensada Nestlé 397g", "unidad"),
        ("Queso Crema Philadelphia 200g", "unidad"),
        ("Yogurt Griego Soprole 4un", "unidad"),
    ]),
    "carnes": ("Carnes y pescados", "🥩", (3000, 9000), [
        ("Pechuga de Pollo kg", "$/kg"),
        ("Salmón Fresco kg", "$/kg"),
        ("Carne Molida Especial kg", "$/kg"),
        ("Longaniza Colchagüina kg", "$/kg"),
        ("Jamón de Pavo San Jorge 200g", "$/kg"),
        ("Filete de Merluza kg", "$/kg"),
        ("Chorizo Parrillero kg", "$/kg"),
        ("Costillar de Cerdo kg", "$/kg"),
    ]),
    "cuidado": ("Cuidado personal", "🧴", (1200, 6500), [
        ("Shampoo Sedal 340ml", "$/L"),
        ("Jabón Dove 90g", "unidad"),
        ("Pasta de Dientes Colgate 90g", "unidad"),
        ("Desodorante Rexona 150ml", "$/L"),
        ("Toallitas Húmedas Babysec 50un", "unidad"),
        ("Acondicionador Sedal 340ml", "$/L"),
        ("Protector Solar Nivea 200ml", "unidad"),
        ("Máquina de Afeitar Gillette 2un", "unidad"),
    ]),
    "congelados": ("Congelados", "🧊", (1400, 4800), [
        ("Helado Bresler 1L", "$/L"),
        ("Papas Fritas Congeladas McCain 750g", "$/kg"),
        ("Pizza Congelada Rapipollo 400g", "unidad"),
        ("Verduras Congeladas McCain Mix 500g", "$/kg"),
        ("Empanadas de Pino Congeladas 6un", "unidad"),
        ("Nuggets de Pollo Sopraval 400g", "$/kg"),
        ("Berries Congelados Vital 500g", "$/kg"),
    ]),
    "snacks": ("Snacks", "🍪", (600, 3200), [
        ("Galletas Costa Tritón", "unidad"),
        ("Papas Fritas Lays 150g", "unidad"),
        ("Chocolate Sahne Nuss", "unidad"),
        ("Barra de Cereal Nature Valley", "unidad"),
        ("Maní Confitado Evercrisp 200g", "unidad"),
        ("Galletas de Agua McKay 200g", "unidad"),
        ("Snack de Queso Doritos 150g", "unidad"),
        ("Palomitas de Maíz Karamba 90g", "unidad"),
    ]),
}

NOW = datetime(2026, 7, 2, 18, 51, 0, tzinfo=timezone(timedelta(hours=-4)))  # hora de Chile (referencia)

def slugify(text):
    text = text.lower()
    repl = {"á":"a","é":"e","í":"i","ó":"o","ú":"u","ñ":"n"}
    for a,b in repl.items():
        text = text.replace(a,b)
    out = []
    for ch in text:
        out.append(ch if ch.isalnum() else "-")
    slug = "".join(out)
    while "--" in slug:
        slug = slug.replace("--","-")
    return slug.strip("-")

def round_price(n):
    return int(round(n / 10.0) * 10)

def gen_products(min_total=120, max_total=140):
    products = []
    pid = 1

    combos = []
    for cat_id, (label, icon, price_range, items) in CATEGORIES.items():
        for name, unit in items:
            # cada producto aparece en 1 a 3 supermercados distintos
            n_stores = random.randint(1, 3)
            chosen_stores = random.sample(STORES, n_stores)
            for store in chosen_stores:
                combos.append((cat_id, label, icon, price_range, name, unit, store))

    random.shuffle(combos)
    target = random.randint(min_total, max_total)
    combos = combos[:target] if len(combos) > target else combos

    for cat_id, label, icon, price_range, name, unit, store in combos:
        low, high = price_range
        old_price = round_price(random.uniform(low, high))
        discount_pct = random.randint(15, 45)
        new_price = round_price(old_price * (1 - discount_pct / 100))
        real_discount = round((1 - new_price / old_price) * 100)
        minutes_ago = random.randint(2, 300)
        updated_at = NOW - timedelta(minutes=minutes_ago)

        products.append({
            "id": f"demo-{pid:04d}",
            "supermercado": store["nombre"],
            "nombre": name,
            "categoria": cat_id,
            "categoria_label": label,
            "categoria_icono": icon,
            "precio_actual": new_price,
            "precio_anterior": old_price,
            "descuento_pct": real_discount,
            "unidad_precio": unit,
            "actualizado": updated_at.isoformat(),
            "url_oferta": f"{store['url']}/producto/{slugify(name)}",
            "fuente": "demo",
            "es_demo": True
        })
        pid += 1

    return products

def main():
    products = gen_products()
    payload = {
        "meta": {
            "generado_el": NOW.isoformat(),
            "total_productos": len(products),
            "fuente_datos": "demo",
            "es_demo": True,
            "aviso": (
                "Estos son datos de DEMOSTRACION generados automaticamente. "
                "No representan precios reales de supermercados. "
                "Se reemplazaran cuando se conecte una fuente de datos real "
                "mediante actualizar_ofertas.py."
            ),
            "supermercados": [s["nombre"] for s in STORES],
            "categorias": [
                {"id": k, "label": v[0], "icono": v[1]} for k, v in CATEGORIES.items()
            ]
        },
        "productos": products
    }

    with open("ofertas.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"ofertas.json generado con {len(products)} productos (demo).")

if __name__ == "__main__":
    main()
