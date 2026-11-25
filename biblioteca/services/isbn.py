"""Validación y normalización de ISBN (ISBN-10 e ISBN-13)."""

import re


class ISBNInvalido(ValueError):
    pass


def limpiar(valor: str) -> str:
    """Quita espacios y guiones y pasa la X final a mayúscula."""
    return re.sub(r"[\s-]", "", valor or "").upper()


def _valido_10(isbn: str) -> bool:
    if not re.fullmatch(r"\d{9}[\dX]", isbn):
        return False
    total = sum((10 - i) * (10 if c == "X" else int(c)) for i, c in enumerate(isbn))
    return total % 11 == 0


def _digito_control_13(doce: str) -> str:
    total = sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(doce))
    return str((10 - total % 10) % 10)


def _valido_13(isbn: str) -> bool:
    return (
        re.fullmatch(r"97[89]\d{10}", isbn) is not None
        and _digito_control_13(isbn[:12]) == isbn[12]
    )


def normalizar(valor: str) -> str:
    """Devuelve el ISBN-13 equivalente o lanza ISBNInvalido.

    Acepta ISBN-10 o ISBN-13, con o sin guiones. El código de barras EAN-13
    impreso en los libros es directamente su ISBN-13.
    """
    isbn = limpiar(valor)
    if len(isbn) == 13 and _valido_13(isbn):
        return isbn
    if len(isbn) == 10 and _valido_10(isbn):
        doce = "978" + isbn[:9]
        return doce + _digito_control_13(doce)
    raise ISBNInvalido("El ISBN no es válido. Revisa que tenga 10 o 13 dígitos correctos.")
