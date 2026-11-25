"""Búsqueda de datos de un libro por ISBN en APIs públicas y gratuitas.

Primero Open Library y, para los campos que falten, Google Books.
Ninguna de las dos requiere API key para estas consultas.
"""

import json
import logging
import re
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from django.conf import settings

from .generos import sugerir

logger = logging.getLogger(__name__)

CAMPOS = ("titulo", "autores", "editorial", "anio", "paginas", "portada_url", "descripcion", "genero")
OPEN_LIBRARY = "https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
GOOGLE_BOOKS = "https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"


def _get_json(url):
    req = Request(url, headers={"User-Agent": "ExLibris/1.0 (proyecto academico)"})
    try:
        with urlopen(req, timeout=getattr(settings, "CATALOGO_TIMEOUT", 6)) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (URLError, TimeoutError, ValueError, OSError) as exc:
        logger.warning("Fallo consultando %s: %s", url, exc)
        return None


def _anio(texto):
    m = re.search(r"\d{4}", texto or "")
    return int(m.group()) if m else None


def _https(url):
    return url.replace("http://", "https://", 1) if url else ""


def desde_open_library(isbn):
    data = _get_json(OPEN_LIBRARY.format(isbn=quote(isbn)))
    libro = (data or {}).get(f"ISBN:{isbn}")
    if not libro:
        return {}
    descripcion = libro.get("notes") or ""
    if isinstance(descripcion, dict):
        descripcion = descripcion.get("value", "")
    sujetos = libro.get("subjects") or []
    return {
        "titulo": libro.get("title", ""),
        "autores": ", ".join(a.get("name", "") for a in libro.get("authors", [])),
        "editorial": ", ".join(p.get("name", "") for p in libro.get("publishers", [])),
        "anio": _anio(libro.get("publish_date")),
        "paginas": libro.get("number_of_pages"),
        "portada_url": _https((libro.get("cover") or {}).get("medium", "")),
        "descripcion": descripcion,
        "genero": sugerir(*(x.get("name", "") for x in sujetos[:8])),
    }


def desde_google_books(isbn):
    data = _get_json(GOOGLE_BOOKS.format(isbn=quote(isbn)))
    items = (data or {}).get("items") or []
    if not items:
        return {}
    info = items[0].get("volumeInfo", {})
    return {
        "titulo": info.get("title", ""),
        "autores": ", ".join(info.get("authors", [])),
        "editorial": info.get("publisher", ""),
        "anio": _anio(info.get("publishedDate")),
        "paginas": info.get("pageCount"),
        "portada_url": _https((info.get("imageLinks") or {}).get("thumbnail", "")),
        "descripcion": info.get("description", ""),
        "genero": sugerir(*(info.get("categories") or [])),
    }


def buscar_por_isbn(isbn):
    """Devuelve un dict con los datos encontrados (vacío si no se encontró nada)."""
    resultado = desde_open_library(isbn)
    if not resultado or any(not resultado.get(c) for c in CAMPOS):
        respaldo = desde_google_books(isbn)
        for campo in CAMPOS:
            if not resultado.get(campo) and respaldo.get(campo):
                resultado[campo] = respaldo[campo]
    if not resultado.get("titulo"):
        return {}
    resultado["isbn"] = isbn
    return {k: v for k, v in resultado.items() if v not in (None, "")}
