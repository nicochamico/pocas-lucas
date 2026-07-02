"""
scrapers/store_config.py
-------------------------
Configuración única de fuentes para Pocas Lucas.

Idea operacional:
- Las tiendas con conector VTEX pueden quedar activas; si fallan, el
  orquestador conserva los datos anteriores y deja registro en el log.
- Líder y Tottus quedan inactivos porque todavía no hay endpoint público
  JSON verificado.
- Las categorías y términos evitan licores/tabaco u otros productos con
  restricción de edad. Pocas Lucas se enfoca en supermercado cotidiano:
  despensa, aseo, lácteos, carnes, congelados, snacks y bebidas sin alcohol.
"""

CATEGORIAS = {
    "despensa": {"label": "Despensa", "icono": "🍚", "terminos_busqueda": ["arroz", "aceite", "fideos", "azucar", "harina", "cafe", "atun", "lentejas", "salsa tomate", "te"]},
    "aseo": {"label": "Aseo", "icono": "🧽", "terminos_busqueda": ["detergente", "papel higienico", "cloro", "lavaloza", "suavizante", "toalla papel", "limpiador"]},
    "bebidas": {"label": "Bebidas sin alcohol", "icono": "🥤", "terminos_busqueda": ["bebida", "jugo", "agua mineral", "te helado", "isotonica"]},
    "lacteos": {"label": "Lácteos", "icono": "🥛", "terminos_busqueda": ["leche", "yogurt", "queso", "mantequilla", "crema"]},
    "carnes": {"label": "Carnes y pescados", "icono": "🥩", "terminos_busqueda": ["pollo", "salmon", "carne molida", "merluza", "cerdo"]},
    "cuidado": {"label": "Cuidado personal", "icono": "🧴", "terminos_busqueda": ["shampoo", "jabon", "pasta dientes", "desodorante", "toallitas"]},
    "congelados": {"label": "Congelados", "icono": "🧊", "terminos_busqueda": ["helado", "papas congeladas", "pizza congelada", "verduras congeladas", "nuggets"]},
    "snacks": {"label": "Snacks", "icono": "🍪", "terminos_busqueda": ["galletas", "papas fritas", "chocolate", "barra cereal", "mani"]},
}

# activo=True no significa “garantizado”; significa “intentar actualizar”.
# Si falla, actualizar_ofertas.py conserva los productos previos de esa tienda.
STORES = {
    "jumbo": {
        "nombre": "Jumbo",
        "conector": "vtex",
        "dominio": "www.jumbo.cl",
        "activo": True,
        "nota": "Primer candidato VTEX. Si el endpoint no responde, se conserva lo previo.",
    },
    "santa_isabel": {
        "nombre": "Santa Isabel",
        "conector": "vtex",
        "dominio": "www.santaisabel.cl",
        "activo": True,
        "nota": "Primer candidato VTEX junto a Jumbo.",
    },
    "unimarc": {
        "nombre": "Unimarc",
        "conector": "vtex",
        "dominio": "www.unimarc.cl",
        "activo": False,
        "nota": "Dejar inactivo hasta verificar endpoint público estable.",
    },
    "ekono": {
        "nombre": "Ekono",
        "conector": "vtex",
        "dominio": "www.ekono.cl",
        "activo": False,
        "nota": "Dejar inactivo hasta verificar endpoint público estable.",
    },
    "lider": {
        "nombre": "Líder",
        "conector": "no_disponible",
        "dominio": "www.lider.cl",
        "activo": False,
        "nota": "Sin API pública equivalente verificada. Requiere inspección manual.",
    },
    "tottus": {
        "nombre": "Tottus",
        "conector": "no_disponible",
        "dominio": "www.tottus.cl",
        "activo": False,
        "nota": "Sin API pública equivalente verificada. Requiere inspección manual.",
    },
}
