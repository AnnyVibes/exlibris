from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase

from biblioteca.models import Libro


def correr(*args):
    call_command("datos_demo", *args, stdout=StringIO())


class DatosDemoTests(TestCase):
    def test_por_defecto_crea_la_cuenta_vacia(self):
        correr()
        demo = User.objects.get(username="demo")
        self.assertTrue(demo.check_password("exlibris-demo"))
        self.assertEqual(Libro.objects.filter(propietario=demo).count(), 0)

    def test_por_defecto_no_borra_lo_que_agregaste(self):
        correr()
        demo = User.objects.get(username="demo")
        Libro.objects.create(propietario=demo, titulo="Mío")
        correr()
        self.assertTrue(Libro.objects.filter(titulo="Mío").exists())

    def test_vaciar(self):
        correr("--ejemplos")
        self.assertEqual(Libro.objects.filter(propietario__username="demo").count(), 8)
        correr("--vaciar")
        self.assertEqual(Libro.objects.filter(propietario__username="demo").count(), 0)

    def test_no_toca_otras_cuentas(self):
        otra = User.objects.create_user("ana", password="x")
        Libro.objects.create(propietario=otra, titulo="De Ana")
        correr("--vaciar")
        self.assertTrue(Libro.objects.filter(titulo="De Ana").exists())
