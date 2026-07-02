"""
scrapers/utils.py
------------------
Utilidades compartidas para todos los conectores de datos (scrapers/APIs).

Principios de scraping responsable que sigue este módulo:
  1. Revisa robots.txt del sitio ANTES de pedir cualquier URL, y respeta lo
     que diga (si una ruta está en Disallow, no se pide).
  2. Se identifica con un User-Agent real que dice quién es el bot y da un
     contacto, en vez de simular ser un navegador.
  3. Limita la velocidad de las peticiones (rate limiting) para no cargar
     el sitio del supermercado.
  4. Reintenta con backoff exponencial ante errores de red, pero nunca
     insiste indefinidamente.
  5. Nunca toca rutas que impliquen login, carrito o datos de usuarios:
     solo catálogo público / listado de productos.
"""

import time
import random
import urllib.robotparser
from urllib.parse import urlparse

import requests

USER_AGENT = (
    "PocasLucasBot/1.0 (+https://pocaslucas.cl/bot; "
    "radar de ofertas para consumidores; contacto: hola@pocaslucas.cl)"
)

DEFAULT_TIMEOUT = 12          # segundos
MIN_DELAY_SECONDS = 1.5       # espera mínima entre requests al mismo sitio
MAX_RETRIES = 3

_robots_cache = {}


def _robots_url(base_url):
    parsed = urlparse(base_url)
    return f"{parsed.scheme}://{parsed.netloc}/robots.txt"


def is_allowed(url, user_agent=USER_AGENT):
    """
    Revisa robots.txt con timeout real. urllib.robotparser.read() no permite
    timeout y puede colgarse si el DNS/red falla; por eso descargamos el
    robots.txt con requests y luego lo parseamos. Si no se puede leer, se
    permite la URL puntual y el error real se manejará en la petición.
    """
    robots_txt = _robots_url(url)
    if robots_txt not in _robots_cache:
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_txt)
        try:
            resp = requests.get(robots_txt, headers={"User-Agent": user_agent}, timeout=5)
            if resp.status_code >= 400:
                rp = None
            else:
                rp.parse(resp.text.splitlines())
        except Exception:
            rp = None
        _robots_cache[robots_txt] = rp

    rp = _robots_cache[robots_txt]
    if rp is None:
        return True
    try:
        return rp.can_fetch(user_agent, url)
    except Exception:
        return True


class PoliteSession:
    """
    Envoltorio sobre requests.Session que:
      - respeta robots.txt en cada get(),
      - espera un mínimo entre requests (con jitter aleatorio),
      - reintenta con backoff ante errores transitorios,
      - nunca lanza excepción "silenciosa": si algo falla después de los
        reintentos, deja que la excepción suba para que el orquestador
        decida qué hacer (y NO borre datos previos).
    """

    def __init__(self, min_delay=MIN_DELAY_SECONDS, max_retries=MAX_RETRIES):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept": "application/json, text/html;q=0.8",
        })
        self.min_delay = min_delay
        self.max_retries = max_retries
        self._last_request_ts = 0.0

    def _wait_turn(self):
        elapsed = time.monotonic() - self._last_request_ts
        wait = self.min_delay - elapsed
        if wait > 0:
            time.sleep(wait + random.uniform(0, 0.4))
        self._last_request_ts = time.monotonic()

    def get(self, url, **kwargs):
        if not is_allowed(url):
            raise PermissionError(
                f"robots.txt no permite pedir esta URL para nuestro bot: {url}"
            )

        kwargs.setdefault("timeout", DEFAULT_TIMEOUT)

        last_exc = None
        for attempt in range(1, self.max_retries + 1):
            self._wait_turn()
            try:
                resp = self.session.get(url, **kwargs)
                if resp.status_code == 429:
                    # Nos pidieron bajar el ritmo: esperamos harto más y reintentamos.
                    time.sleep(5 * attempt)
                    continue
                resp.raise_for_status()
                return resp
            except requests.RequestException as exc:
                last_exc = exc
                time.sleep(1.5 * attempt)

        raise ConnectionError(
            f"No se pudo obtener {url} después de {self.max_retries} intentos: {last_exc}"
        )


def slugify(text):
    text = text.lower()
    repl = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ñ": "n"}
    for a, b in repl.items():
        text = text.replace(a, b)
    out = "".join(ch if ch.isalnum() else "-" for ch in text)
    while "--" in out:
        out = out.replace("--", "-")
    return out.strip("-")


def clamp_discount(precio_actual, precio_anterior):
    if not precio_anterior or precio_anterior <= 0:
        return 0
    pct = round((1 - (precio_actual / precio_anterior)) * 100)
    return max(0, min(pct, 90))


# Productos que no queremos mostrar en Pocas Lucas. El foco es supermercado
# cotidiano, no productos con restricción de edad u otros rubros sensibles.
RESTRICTED_KEYWORDS = {
    "cerveza", "vino", "pisco", "ron", "whisky", "vodka", "tequila", "gin",
    "licor", "licores", "espumante", "champagne", "sour", "six pack",
    "cigarro", "cigarrillo", "tabaco", "vape", "vaporizador", "nicotina",
}


def is_restricted_product(text):
    t = slugify(text or "").replace("-", " ")
    return any(k in t for k in RESTRICTED_KEYWORDS)
