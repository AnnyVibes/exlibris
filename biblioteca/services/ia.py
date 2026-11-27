"""Integración con la IA generativa a través de n8n (fase 2).

Django no llama al LLM directamente: envía la tarea a un webhook de n8n, donde un workflow
(como el del Lab 14) usa Gemini u Ollama y devuelve JSON. Si n8n no está encendido, la app
sigue funcionando y solo muestra «IA no disponible».

Webhooks:
  POST {N8N_URL}/exlibris-tarea   {"tarea": "clasificar" | "resumir" | "resena", ...}
  POST {N8N_URL}/exlibris-agente  {"mensaje", "sesion", "token", "api", "persona"}
"""

import json
import logging
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.core import signing

from .generos import GENEROS, sugerir

logger = logging.getLogger(__name__)
SAL_TOKEN = "exlibris.ia.token"
MAX_ANOTACIONES = 60          # límite de notas que se envían al modelo
MAX_CARACTERES = 12000        # y de texto total, para no exceder el contexto


class IANoDisponible(Exception):
    """n8n no responde, devolvió un error o una respuesta que no se puede usar."""


# ------------------------------------------------------------------ transporte
def _llamar(ruta, datos, timeout=None):
    url = f"{settings.N8N_URL}/{ruta}"
    cuerpo = json.dumps(datos, ensure_ascii=False, default=str).encode("utf-8")
    cabeceras = {"Content-Type": "application/json", "Accept": "application/json"}
    if settings.N8N_SECRET:
        cabeceras["X-ExLibris-Secret"] = settings.N8N_SECRET
    req = Request(url, data=cuerpo, headers=cabeceras, method="POST")
    try:
        with urlopen(req, timeout=timeout or settings.N8N_TIMEOUT) as resp:
            texto = resp.read().decode("utf-8")
    except HTTPError as exc:
        logger.warning("n8n respondió %s en %s", exc.code, url)
        raise IANoDisponible("La IA respondió con un error. Revisa el workflow en n8n.") from exc
    except (URLError, TimeoutError, OSError) as exc:
        logger.warning("No se pudo conectar con n8n en %s: %s", url, exc)
        raise IANoDisponible("La IA no está disponible. ¿Está encendido n8n?") from exc
    try:
        respuesta = json.loads(texto)
    except ValueError as exc:
        raise IANoDisponible("La IA devolvió una respuesta que no es JSON.") from exc
    # n8n a veces envuelve la respuesta en una lista o en «output»
    if isinstance(respuesta, list) and respuesta:
        respuesta = respuesta[0]
    if isinstance(respuesta, dict) and isinstance(respuesta.get("output"), dict):
        respuesta = respuesta["output"]
    if not isinstance(respuesta, dict):
        raise IANoDisponible("La IA devolvió una respuesta inesperada.")
    return respuesta


def _texto(respuesta, *claves):
    for clave in claves:
        valor = respuesta.get(clave)
        if isinstance(valor, str) and valor.strip():
            return valor.strip()
    raise IANoDisponible("La IA no devolvió texto.")


def _datos_libro(libro):
    return {
        "titulo": libro.titulo, "autores": libro.autores, "genero": libro.genero,
        "paginas": libro.paginas, "descripcion": (libro.descripcion or "")[:1500],
    }


def _anotaciones(libro):
    notas, total = [], 0
    for n in libro.anotaciones.order_by("pagina", "creado")[:MAX_ANOTACIONES]:
        texto = n.texto.strip()
        if total + len(texto) > MAX_CARACTERES:
            break
        total += len(texto)
        notas.append({"pagina": n.pagina, "texto": texto})
    return notas


# ------------------------------------------------------------------ tareas
def clasificar(titulo, autores="", descripcion=""):
    """Devuelve {"genero": uno de GENEROS (o ""), "etiquetas": [hasta 5]}."""
    respuesta = _llamar("exlibris-tarea", {
        "tarea": "clasificar", "titulo": titulo, "autores": autores,
        "descripcion": (descripcion or "")[:1500], "generos": GENEROS,
    })
    genero = str(respuesta.get("genero") or "").strip()
    if genero not in GENEROS:
        genero = sugerir(genero)  # el modelo pudo responder «Fantasy» o «fantasía»
    etiquetas = respuesta.get("etiquetas") or []
    if isinstance(etiquetas, str):
        etiquetas = [e for e in etiquetas.split(",")]
    etiquetas = [str(e).strip().lower()[:30] for e in etiquetas if str(e).strip()][:5]
    return {"genero": genero, "etiquetas": etiquetas}


def resumir(libro):
    notas = _anotaciones(libro)
    if not notas:
        raise ValueError("El libro no tiene anotaciones para resumir.")
    respuesta = _llamar("exlibris-tarea", {"tarea": "resumir", "libro": _datos_libro(libro), "anotaciones": notas})
    return _texto(respuesta, "resumen", "texto")


def borrador_resena(libro, calificacion=None):
    respuesta = _llamar("exlibris-tarea", {
        "tarea": "resena", "libro": _datos_libro(libro), "anotaciones": _anotaciones(libro),
        "calificacion": calificacion,
    })
    # La reseña va a un cuadro de texto simple: se quitan las marcas de formato (**negrita**, viñetas).
    texto = _texto(respuesta, "resena", "texto")
    texto = re.sub(r"\*\*(.+?)\*\*|__(.+?)__", lambda m: m.group(1) or m.group(2), texto)
    return re.sub(r"(?m)^\s*[*\-•]\s+", "", texto).strip()


# ------------------------------------------------------------------ agente
def token_para(usuario):
    """Token firmado con el id de la persona; las herramientas del agente lo envían a /api/ia/."""
    return signing.dumps({"u": usuario.pk}, salt=SAL_TOKEN)


def usuario_de_token(token):
    """Devuelve el id de usuario o None si el token no es válido o caducó."""
    try:
        datos = signing.loads(token, salt=SAL_TOKEN, max_age=settings.IA_TOKEN_MINUTOS * 60)
    except signing.BadSignature:
        return None
    return datos.get("u")


def preguntar(usuario, mensaje, sesion):
    perfil = getattr(usuario, "perfil", None)
    respuesta = _llamar("exlibris-agente", {
        "mensaje": mensaje[:2000],
        "sesion": f"exlibris-{usuario.pk}-{sesion}",
        "token": token_para(usuario),
        "api": f"{settings.EXLIBRIS_API_URL}/api/ia",
        "persona": {
            "nombre": usuario.first_name or usuario.username,
            "tratamiento": perfil.get_tratamiento_display() if perfil else "Lectora",
        },
    })
    return limpiar_ids(_texto(respuesta, "respuesta", "output", "texto"))


_ID_ENTRE_PARENTESIS = re.compile(r"\s*[(\[]\s*(?:id|ID|Id)\s*(?:del libro)?\s*[:#=]?\s*\d+\s*[)\]]")
_ID_SUELTO = re.compile(r"[,;]?\s*\b(?:id|ID|Id)\s*(?:del libro)?\s*[:#=]\s*\d+\b")


def limpiar_ids(texto):
    """Quita los identificadores internos («(ID: 25)», «ID: 25») que el agente usa para sus herramientas."""
    texto = _ID_ENTRE_PARENTESIS.sub("", texto)
    texto = _ID_SUELTO.sub("", texto)
    return re.sub(r"[ \t]+([.,;:])", r"\1", texto).strip()


# ------------------------------------------------------------------ agregar libros desde el asistente
def agregar_libro(usuario, titulo, autores="", isbn=""):
    """Agrega un libro a la biblioteca de la persona. Busca el ISBN y los datos en los catálogos públicos.

    Devuelve {"creado": bool, "libro": {...}, "mensaje": str}. No duplica: si ya lo tiene, lo indica.
    """
    from ..models import Libro
    from . import catalogo
    from .isbn import ISBNInvalido, normalizar

    titulo, autores = (titulo or "").strip()[:255], (autores or "").strip()[:255]
    if not titulo and not isbn:
        raise ValueError("Falta el título del libro.")
    try:
        isbn = normalizar(isbn) if isbn else ""
    except ISBNInvalido:
        isbn = ""
    datos = catalogo.completar_datos(isbn, titulo, autores)
    isbn = isbn or datos.get("isbn", "")

    existente = None
    if isbn:
        existente = Libro.objects.filter(propietario=usuario, isbn=isbn).first()
    if existente is None and titulo:
        existente = Libro.objects.filter(propietario=usuario, titulo__iexact=titulo).first()
    if existente:
        return {"creado": False, "libro": _resumen_libro(existente),
                "mensaje": "Ese libro ya estaba en la biblioteca; no se agregó de nuevo."}

    libro = Libro.objects.create(
        propietario=usuario,
        isbn=isbn,
        titulo=titulo or datos.get("titulo", ""),
        autores=autores or datos.get("autores", ""),
        editorial=datos.get("editorial", "")[:255],
        anio=datos.get("anio"),
        paginas=datos.get("paginas"),
        portada_url=datos.get("portada_url", "")[:500],
        descripcion=datos.get("descripcion", ""),
        genero=datos.get("genero", ""),
        estado=Libro.Estado.POR_LEER,
    )
    mensaje = "Libro agregado como «Por leer»." + ("" if isbn else " No se encontró su ISBN en los catálogos.")
    return {"creado": True, "libro": _resumen_libro(libro), "mensaje": mensaje}


def _resumen_libro(libro):
    return {"titulo": libro.titulo, "autores": libro.autores, "isbn": libro.isbn, "genero": libro.genero,
            "paginas": libro.paginas, "editorial": libro.editorial, "anio": libro.anio,
            "estado": libro.get_estado_display(), "tiene_portada": bool(libro.imagen_portada)}
