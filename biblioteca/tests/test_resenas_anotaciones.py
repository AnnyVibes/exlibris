from django.urls import reverse

from biblioteca.models import Anotacion, Resena

from .base import ConUsuario


class ResenaTests(ConUsuario):
    def test_crear_y_editar_una_sola_resena(self):
        libro = self.libro()
        url = reverse("resena_guardar", args=[libro.pk])
        self.client.post(url, {"calificacion": 4, "texto": "Muy bueno"})
        self.client.post(url, {"calificacion": 5, "texto": "Lo releí: excelente"})
        self.assertEqual(Resena.objects.filter(libro=libro).count(), 1)
        resena = Resena.objects.get(libro=libro)
        self.assertEqual((resena.calificacion, resena.texto), (5, "Lo releí: excelente"))

    def test_calificacion_fuera_de_rango(self):
        libro = self.libro()
        self.client.post(reverse("resena_guardar", args=[libro.pk]), {"calificacion": 9})
        self.assertFalse(Resena.objects.exists())


class AnotacionTests(ConUsuario):
    def test_conteo_de_anotaciones(self):
        libro = self.libro()
        url = reverse("anotacion_crear", args=[libro.pk])
        self.client.post(url, {"texto": "Primera idea", "pagina": 10})
        r = self.client.post(url, {"texto": "Segunda idea"}, follow=True)
        self.assertEqual(libro.anotaciones.count(), 2)
        self.assertContains(r, "Llevas 2 en este libro")
        self.assertContains(self.client.get(reverse("anotaciones")), "Primera idea")

    def test_anotacion_vacia(self):
        libro = self.libro()
        self.client.post(reverse("anotacion_crear", args=[libro.pk]), {"texto": ""})
        self.assertEqual(libro.anotaciones.count(), 0)

    def test_buscar_anotaciones(self):
        libro = self.libro()
        Anotacion.objects.create(libro=libro, texto="El tiempo es circular")
        Anotacion.objects.create(libro=libro, texto="Me gusta la Maga")
        r = self.client.get(reverse("anotaciones"), {"q": "circular"})
        resultados = [n.texto for n in r.context["anotaciones"]]
        self.assertEqual(resultados, ["El tiempo es circular"])

    def test_no_borra_anotacion_ajena(self):
        from biblioteca.models import Libro
        ajeno = Libro.objects.create(propietario=self.otro, titulo="Ajeno")
        nota = Anotacion.objects.create(libro=ajeno, texto="privada")
        self.assertEqual(self.client.post(reverse("anotacion_eliminar", args=[nota.pk])).status_code, 404)
        self.assertNotContains(self.client.get(reverse("anotaciones")), "privada")
        self.assertTrue(Anotacion.objects.filter(pk=nota.pk).exists())


class IdsUnicosTests(ConUsuario):
    def test_ficha_del_libro_sin_ids_repetidos(self):
        import re
        libro = self.libro()
        html = self.client.get(reverse("libro_detalle", args=[libro.pk])).content.decode()
        ids = re.findall(r'\sid="([^"]+)"', html)
        repetidos = {i for i in ids if ids.count(i) > 1}
        self.assertEqual(repetidos, set())
