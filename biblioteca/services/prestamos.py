"""Reglas de negocio de los préstamos."""

from django.db import transaction
from django.utils import timezone

from ..models import Prestamo


class PrestamoError(ValueError):
    pass


@transaction.atomic
def prestar(libro, persona, contacto="", devolver_el=None, notas=""):
    persona = (persona or "").strip()
    if not persona:
        raise PrestamoError("Indica con quién compartes el libro.")
    if libro.prestamos.select_for_update().filter(devuelto_el__isnull=True).exists():
        raise PrestamoError("Este libro ya está compartido con alguien. Registra la devolución primero.")
    hoy = timezone.localdate()
    if devolver_el and devolver_el < hoy:
        raise PrestamoError("La fecha de devolución no puede estar en el pasado.")
    return Prestamo.objects.create(
        libro=libro, persona=persona, contacto=contacto, prestado_el=hoy,
        devolver_el=devolver_el, notas=notas,
    )


def devolver(prestamo):
    if not prestamo.activo:
        raise PrestamoError("Este libro ya fue devuelto.")
    prestamo.devuelto_el = timezone.localdate()
    prestamo.save(update_fields=["devuelto_el"])
    return prestamo
