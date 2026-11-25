from django.contrib.auth.models import User
from django.test import TestCase

from biblioteca.models import Libro


class ConUsuario(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user("ana", "ana@example.com", "clave-segura-123")
        self.otro = User.objects.create_user("beto", "beto@example.com", "clave-segura-123")
        self.client.force_login(self.usuario)

    def libro(self, **extra):
        datos = {"propietario": self.usuario, "titulo": "Rayuela", "autores": "Julio Cortázar", "paginas": 600}
        datos.update(extra)
        return Libro.objects.create(**datos)
