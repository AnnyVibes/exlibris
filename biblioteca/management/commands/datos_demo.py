"""Crea un usuario de demostración con libros, reseñas, anotaciones y préstamos.

Uso: python manage.py datos_demo  (usuario «demo», contraseña «exlibris-demo»)
"""

from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from biblioteca.models import Anotacion, Libro, Prestamo, Resena

LIBROS = [
    ("9780307474728", "Cien años de soledad", "Gabriel García Márquez", "Novela", 417, "leyendo", 212, 5),
    ("9788437604947", "Rayuela", "Julio Cortázar", "Novela", 736, "leido", 736, 4),
    ("9788466338141", "Ficciones", "Jorge Luis Borges", "Cuento", 224, "leido", 224, 5),
    ("9788420674209", "Pedro Páramo", "Juan Rulfo", "Novela", 136, "por_leer", 0, None),
    ("9788497592208", "Veinte poemas de amor", "Pablo Neruda", "Poesía", 112, "leido", 112, 4),
    ("9788499089515", "Sapiens", "Yuval Noah Harari", "Historia", 496, "leyendo", 120, None),
    ("9788498381498", "Harry Potter y la piedra filosofal", "J. K. Rowling", "Fantasía", 264, "leido", 264, 5),
    ("9788420412146", "El túnel", "Ernesto Sabato", "Novela", 160, "abandonado", 40, 2),
]
NOTAS = {
    "Cien años de soledad": [
        (14, "El hielo como descubrimiento: la primera escena ya mezcla lo mágico con lo cotidiano."),
        (98, "Árbol genealógico: los Aurelianos son introvertidos y los José Arcadio impulsivos."),
        (201, "La lluvia de flores amarillas. Volver a leer este capítulo."),
    ],
    "Sapiens": [(45, "La revolución cognitiva: el poder de creer en ficciones compartidas.")],
    "Ficciones": [(31, "Tlön: un mundo que se inventa a sí mismo a través de una enciclopedia.")],
}


class Command(BaseCommand):
    help = "Crea datos de demostración para el usuario «demo»."

    def handle(self, *args, **opciones):
        usuario, creado = User.objects.get_or_create(username="demo", defaults={"email": "demo@example.com", "first_name": "Lectora", "last_name": "Demo"})
        if creado:
            usuario.set_password("exlibris-demo")
            usuario.save()
        Libro.objects.filter(propietario=usuario).delete()
        hoy = timezone.localdate()
        libros = {}
        for isbn, titulo, autor, genero, paginas, estado, actual, estrellas in LIBROS:
            libro = Libro.objects.create(
                propietario=usuario, isbn=isbn, titulo=titulo, autores=autor, genero=genero,
                paginas=paginas, estado=estado, pagina_actual=actual,
            )
            libros[titulo] = libro
            if estrellas:
                Resena.objects.create(libro=libro, calificacion=estrellas, texto="")
        for titulo, notas in NOTAS.items():
            for pagina, texto in notas:
                Anotacion.objects.create(libro=libros[titulo], pagina=pagina, texto=texto)
        Prestamo.objects.create(libro=libros["Rayuela"], persona="Lucía", contacto="6000-1234", prestado_el=hoy - timedelta(days=20), devolver_el=hoy - timedelta(days=2))
        Prestamo.objects.create(libro=libros["Ficciones"], persona="Carlos", prestado_el=hoy - timedelta(days=5), devolver_el=hoy + timedelta(days=10))
        Prestamo.objects.create(libro=libros["Harry Potter y la piedra filosofal"], persona="Sofía", prestado_el=hoy - timedelta(days=60), devuelto_el=hoy - timedelta(days=30))
        self.stdout.write(self.style.SUCCESS("Listo: usuario «demo» / contraseña «exlibris-demo»"))
