"""Cálculos del panel de inicio y de estadísticas."""

from collections import Counter

from django.db.models import Avg, Count

from ..models import Anotacion, Libro, Prestamo


def resumen(usuario):
    libros = Libro.objects.filter(propietario=usuario)
    por_estado = dict(libros.values_list("estado").annotate(n=Count("id")))
    prestamos = Prestamo.objects.filter(libro__propietario=usuario)
    return {
        "total": libros.count(),
        "por_estado": {
            etiqueta: por_estado.get(valor, 0) for valor, etiqueta in Libro.Estado.choices
        },
        "leidos": por_estado.get(Libro.Estado.LEIDO, 0),
        "leyendo": por_estado.get(Libro.Estado.LEYENDO, 0),
        "anotaciones": Anotacion.objects.filter(libro__propietario=usuario).count(),
        "prestados": prestamos.filter(devuelto_el__isnull=True).count(),
        "calificacion_media": libros.aggregate(m=Avg("resena__calificacion"))["m"],
        "paginas_leidas": sum(
            l.paginas or 0 for l in libros.filter(estado=Libro.Estado.LEIDO).only("paginas")
        ),
    }


def generos(usuario, limite=6):
    nombres = Libro.objects.filter(propietario=usuario).exclude(genero="").values_list("genero", flat=True)
    conteo = Counter(g.strip() for g in nombres)
    return sorted(conteo.items(), key=lambda par: (-par[1], par[0]))[:limite]


def mas_anotados(usuario, limite=5):
    return (
        Libro.objects.filter(propietario=usuario)
        .annotate(n_anotaciones=Count("anotaciones"))
        .filter(n_anotaciones__gt=0)
        .order_by("-n_anotaciones", "titulo")[:limite]
    )


def prestamos_activos(usuario):
    return (
        Prestamo.objects.filter(libro__propietario=usuario, devuelto_el__isnull=True)
        .select_related("libro")
        .order_by("devolver_el", "prestado_el")
    )
