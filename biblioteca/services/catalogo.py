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
    return _desde_volumen(items[0].get("volumeInfo", {}))


def _desde_volumen(info):
    """Convierte un volumen de Google Books al formato de Ex Libris."""
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


# ------------------------------------------------------------------ búsqueda por título y autor
GOOGLE_BUSQUEDA = "https://www.googleapis.com/books/v1/volumes?q={q}&printType=books&maxResults=10"
OPEN_LIBRARY_BUSQUEDA = "https://openlibrary.org/search.json?title={titulo}&author={autor}&limit=5&fields=isbn"


def _isbn13_validos(candidatos):
    from .isbn import ISBNInvalido, normalizar

    vistos = []
    for c in candidatos:
        try:
            isbn = normalizar(str(c))
        except ISBNInvalido:
            continue
        if isbn not in vistos:
            vistos.append(isbn)
    return vistos


def buscar_por_titulo(titulo, autor=""):
    """Busca un libro por título (y autor). Devuelve sus datos con el ISBN (prefiere ediciones en español
    y, entre los resultados, el que trae más datos). Devuelve {} si no encuentra nada."""
    titulo, autor = (titulo or "").strip(), (autor or "").strip()
    if not titulo:
        return {}
    q = f"intitle:{titulo}" + (f"+inauthor:{autor}" if autor else "")
    for idioma in ("&langRestrict=es", ""):
        data = _get_json(GOOGLE_BUSQUEDA.format(q=quote(q, safe=":+")) + idioma)
        candidatos = []
        for item in (data or {}).get("items") or []:
            info = item.get("volumeInfo") or {}
            ids = info.get("industryIdentifiers") or []
            validos = _isbn13_validos(i.get("identifier") for i in ids if i.get("type") in ("ISBN_13", "ISBN_10"))
            if validos:
                datos = _desde_volumen(info)
                datos["isbn"] = validos[0]
                candidatos.append(datos)
        if candidatos:
            # el primero de Google es el más relevante; entre los 3 primeros se elige el más completo
            mejor = max(candidatos[:3], key=lambda d: sum(1 for c in CAMPOS if d.get(c)))
            return {k: v for k, v in mejor.items() if v not in (None, "")}
    data = _get_json(OPEN_LIBRARY_BUSQUEDA.format(titulo=quote(titulo), autor=quote(autor)))
    for doc in (data or {}).get("docs") or []:
        validos = _isbn13_validos(doc.get("isbn") or [])
        if validos:
            return {"isbn": validos[0]}
    return {}


def buscar_isbn_por_titulo(titulo, autor=""):
    return buscar_por_titulo(titulo, autor).get("isbn", "")


def completar_datos(isbn="", titulo="", autor=""):
    """Datos más completos posibles. Sin ISBN, primero lo busca por título y autor; luego consulta ese ISBN
    y rellena lo que falte con el resultado de la búsqueda por título (otra edición del mismo libro)."""
    por_titulo = None
    if not isbn and titulo:
        por_titulo = buscar_por_titulo(titulo, autor)
        isbn = por_titulo.get("isbn", "")
    datos = buscar_por_isbn(isbn) if isbn else {}
    if titulo and (not datos or any(not datos.get(c) for c in CAMPOS)):
        if por_titulo is None:
            por_titulo = buscar_por_titulo(titulo, autor)
        for campo in CAMPOS:
            if not datos.get(campo) and por_titulo.get(campo):
                datos[campo] = por_titulo[campo]
    if isbn:
        datos["isbn"] = isbn
    return datos


def completar_libro(libro):
    """Rellena SOLO los campos vacíos de un libro con los catálogos. Devuelve la lista de campos completados."""
    from .generos import GENEROS

    datos = completar_datos(libro.isbn, libro.titulo, libro.autores)
    completados = []
    for campo in ("autores", "editorial", "anio", "paginas", "portada_url", "descripcion", "genero", "isbn"):
        valor = datos.get(campo)
        if not valor or getattr(libro, campo):
            continue
        if campo == "portada_url" and libro.portada:
            continue
        if campo == "genero" and valor not in GENEROS:
            continue
        if campo == "isbn" and type(libro).objects.filter(propietario=libro.propietario, isbn=valor).exclude(pk=libro.pk).exists():
            continue
        setattr(libro, campo, valor[:500] if isinstance(valor, str) and campo == "portada_url" else valor)
        completados.append(campo)
    if completados:
        libro.save()
    return completados
