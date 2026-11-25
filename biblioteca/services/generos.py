"""Lista cerrada de géneros y traducción de las categorías que devuelven los catálogos."""

import re
import unicodedata

GENEROS = [
    "Novela", "Cuento", "Poesía", "Teatro", "Fantasía", "Ciencia ficción", "Misterio y policial",
    "Terror", "Romance", "Novela histórica", "Clásicos", "Juvenil", "Infantil", "Cómic y manga",
    "Biografía y memorias", "Ensayo", "Historia", "Filosofía", "Psicología", "Desarrollo personal",
    "Ciencia", "Tecnología", "Negocios y economía", "Arte y diseño", "Religión y espiritualidad",
    "Cocina", "Viajes", "Educación y estudio", "Otro",
]

# Palabras clave (sin tildes, en minúsculas) → género. El orden importa: lo más específico primero.
CLAVES = [
    (("magic realism", "realismo magico"), "Novela"),
    (("comic", "comics", "manga", "graphic novel", "graphic novels", "historieta", "historietas"), "Cómic y manga"),
    (("juvenile", "infantil", "children", "picture book"), "Infantil"),
    (("young adult", "juvenil"), "Juvenil"),
    (("science fiction", "ciencia ficcion", "sci-fi", "dystopia", "distopia"), "Ciencia ficción"),
    (("fantasy", "fantasia", "fantastic", "magic"), "Fantasía"),
    (("mystery", "detective", "crime", "thriller", "policial", "suspense", "misterio"), "Misterio y policial"),
    (("horror", "terror", "ghost"), "Terror"),
    (("romance", "love stories", "romantica"), "Romance"),
    (("historical fiction", "novela historica"), "Novela histórica"),
    (("poetry", "poesia", "poems", "poemas"), "Poesía"),
    (("drama", "theater", "teatro", "plays"), "Teatro"),
    (("short stories", "cuentos", "cuento"), "Cuento"),
    (("biography", "autobiography", "memoir", "biografia", "memorias"), "Biografía y memorias"),
    (("self-help", "autoayuda", "personal development", "desarrollo personal"), "Desarrollo personal"),
    (("psychology", "psicologia"), "Psicología"),
    (("philosophy", "filosofia"), "Filosofía"),
    (("religion", "spiritual", "bible", "espiritualidad"), "Religión y espiritualidad"),
    (("business", "economics", "finance", "negocios", "economia", "management"), "Negocios y economía"),
    (("computers", "technology", "programming", "tecnologia", "informatica"), "Tecnología"),
    (("science", "ciencia", "mathematics", "physics", "biology", "nature"), "Ciencia"),
    (("history", "historia"), "Historia"),
    (("art", "design", "arte", "diseno", "photography", "music"), "Arte y diseño"),
    (("cooking", "cocina", "recipes"), "Cocina"),
    (("travel", "viajes"), "Viajes"),
    (("education", "study", "textbook", "educacion", "language arts", "foreign language"), "Educación y estudio"),
    (("essay", "essays", "ensayo", "ensayos", "criticism", "literary collections"), "Ensayo"),
    (("classic", "classics", "clasico", "clasicos"), "Clásicos"),
    (("fiction", "novel", "novels", "ficcion", "novela", "novelas", "literature", "literatura"), "Novela"),
]


def _plano(texto):
    texto = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode()
    return texto.lower()


def sugerir(*textos):
    """Elige un género de la lista a partir de categorías libres (p. ej. «Juvenile Fiction»).

    Devuelve "" si no se puede deducir, para que la persona lo elija.
    """
    plano = " | ".join(_plano(t) for t in textos if t)
    if not plano:
        return ""
    for genero in GENEROS:
        if _plano(genero) == plano.strip():
            return genero
    for claves, genero in CLAVES:
        # Palabras completas: «art» no debe coincidir con «heart» ni «party».
        if any(re.search(rf"\b{re.escape(c)}\b", plano) for c in claves):
            return genero
    return ""
