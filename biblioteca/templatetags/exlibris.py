from django import template
from django.utils.safestring import mark_safe

register = template.Library()

# Iconos de trazo simple (24×24) para no depender de una librería externa.
ICONOS = {
    "inicio": '<path d="M3 11.5 12 4l9 7.5"/><path d="M5 10v10h14V10"/><path d="M10 20v-6h4v6"/>',
    "libros": '<path d="M4 5a2 2 0 0 1 2-2h5v16H6a2 2 0 0 0-2 2z"/><path d="M20 5a2 2 0 0 0-2-2h-5v16h5a2 2 0 0 1 2 2z"/>',
    "escanear": '<path d="M4 8V5a1 1 0 0 1 1-1h3M16 4h3a1 1 0 0 1 1 1v3M20 16v3a1 1 0 0 1-1 1h-3M8 20H5a1 1 0 0 1-1-1v-3"/><path d="M7 8v8M10 8v8M13 8v8M16 8v8"/>',
    "nota": '<path d="M5 4h10l4 4v12H5z"/><path d="M15 4v4h4M8 12h8M8 16h5"/>',
    "prestamo": '<path d="M7 7h11l-3-3M17 17H6l3 3"/>',
    "grafico": '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    "ia": '<path d="M12 3l1.8 4.7L18.5 9.5l-4.7 1.8L12 16l-1.8-4.7L5.5 9.5l4.7-1.8z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/>',
    "usuario": '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    "salir": '<path d="M14 4h5v16h-5M10 8l-4 4 4 4M6 12h10"/>',
    "buscar": '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
    "mas": '<path d="M12 5v14M5 12h14"/>',
    "camara": '<path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="3.5"/>',
    "corazon": '<path d="M12 20s-7-4.5-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.5-7 10-7 10z"/>',
    "campana": '<path d="M6 16V11a6 6 0 0 1 12 0v5l2 2H4z"/><path d="M10 20a2 2 0 0 0 4 0"/>',
    "estrella": '<path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z"/>',
    "puntos": '<circle cx="5" cy="12" r="1.3"/><circle cx="12" cy="12" r="1.3"/><circle cx="19" cy="12" r="1.3"/>',
    "carpeta": '<path d="M3 6a1 1 0 0 1 1-1h5l2 2h9a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1z"/>',
    "editar": '<path d="M4 20h4L19 9l-4-4L4 16z"/>',
    "basura": '<path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/>',
    "check": '<path d="m5 12 5 5 9-10"/>',
    "flor": '<circle cx="12" cy="12" r="2.5"/><path d="M12 9.5C10 6 10.5 3 12 3s2 3 0 6.5M14.5 12c3.5-2 6.5-1.5 6.5 0s-3 2-6.5 0M12 14.5c2 3.5 1.5 6.5 0 6.5s-2-3 0-6.5M9.5 12C6 14 3 13.5 3 12s3-2 6.5 0"/>',
    "calendario": '<rect x="4" y="5" width="16" height="15" rx="2"/><path d="M4 10h16M9 3v4M15 3v4"/>',
    "etiqueta": '<path d="M3 12V4h8l9 9-8 8z"/><circle cx="7.5" cy="8.5" r="1.3"/>',
    "alerta": '<circle cx="12" cy="12" r="9"/><path d="M12 7.5v5.5M12 16.5h.01"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5.5M12 7.5h.01"/>',
    "subir": '<path d="M12 16V4M7 9l5-5 5 5"/><path d="M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3"/>',
    "imagen": '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="m21 16-5-5-9 9"/>',
    "lista": '<path d="M9 6h11M9 12h11M9 18h11"/><circle cx="4.5" cy="6" r="1"/><circle cx="4.5" cy="12" r="1"/><circle cx="4.5" cy="18" r="1"/>',
    "candado": '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
    "correo": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m4 7 8 6 8-6"/>',
    "ayuda": '<circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.7.3-1 .9-1 1.7M12 17h.01"/>',
}


@register.simple_tag
def icono(nombre, clase="icono"):
    trazos = ICONOS.get(nombre, "")
    return mark_safe(
        f'<svg class="{clase}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{trazos}</svg>'
    )


@register.filter
def estrellas(valor):
    try:
        n = int(round(float(valor)))
    except (TypeError, ValueError):
        return ""
    return "★" * n + "☆" * (5 - n)


# Colores de lomo/tapa para los libros dibujados (coinciden con .c0 … .c5 del CSS).
COLORES_LIBRO = ["#8b7fd1", "#f07167", "#4a6fa5", "#5fa777", "#ec8fb4", "#6d5bd0"]


@register.filter
def color_libro(libro):
    """Índice de color estable para un libro (según su id)."""
    try:
        return int(libro.pk or 0) % len(COLORES_LIBRO)
    except (AttributeError, TypeError, ValueError):
        return 0


@register.simple_tag
def libro_icono(color=0, simbolo="", clase=""):
    """Libro de pie dibujado en SVG: tapa de color, páginas abajo y cinta separadora."""
    c = COLORES_LIBRO[int(color) % len(COLORES_LIBRO)]
    texto = (
        f'<text x="27" y="22" text-anchor="middle" font-size="10" font-family="system-ui,sans-serif" '
        f'font-weight="700" fill="{c}">{simbolo}</text>' if simbolo else ""
    )
    return mark_safe(
        f'<svg class="{clase}" viewBox="0 0 50 56" aria-hidden="true">'
        f'<rect x="6" y="2" width="38" height="46" rx="4" fill="{c}"/>'
        f'<rect x="6" y="2" width="6" height="46" rx="3" fill="#000" opacity=".13"/>'
        f'<rect x="16" y="12" width="22" height="14" rx="3" fill="#fff" opacity=".9"/>{texto}'
        f'<rect x="16" y="31" width="22" height="2.5" rx="1.2" fill="#fff" opacity=".55"/>'
        f'<path d="M10 43h34v8H13a3 3 0 0 1-3-3z" fill="#fffdf8" stroke="{c}" stroke-width="3"/>'
        f'<path d="M32 43v12l3.5-3 3.5 3V43z" fill="#f4b942"/></svg>'
    )
