from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from biblioteca.models import Anotacion, Libro
from biblioteca.services.prestamos import devolver, prestar

from .base import ConUsuario


class EditarAnotacionTests(ConUsuario):
    def test_editar_texto_y_pagina(self):
        libro = self.libro()
        nota = Anotacion.objects.create(libro=libro, texto="Idea vieja", pagina=3)
        self.assertContains(self.client.get(reverse("libro_detalle", args=[libro.pk])), reverse("anotacion_editar", args=[nota.pk]))
        r = self.client.post(reverse("anotacion_editar", args=[nota.pk]), {"texto": "Idea nueva", "pagina": 10})
        self.assertRedirects(r, reverse("libro_detalle", args=[libro.pk]))
        nota.refresh_from_db()
        self.assertEqual((nota.texto, nota.pagina), ("Idea nueva", 10))

    def test_vuelve_a_la_pagina_de_origen(self):
        nota = Anotacion.objects.create(libro=self.libro(), texto="x")
        r = self.client.post(reverse("anotacion_editar", args=[nota.pk]), {"texto": "y", "siguiente": "/anotaciones/"})
        self.assertRedirects(r, "/anotaciones/")
        r = self.client.post(reverse("anotacion_editar", args=[nota.pk]), {"texto": "z", "siguiente": "https://malo.example"})
        self.assertRedirects(r, reverse("libro_detalle", args=[nota.libro_id]))

    def test_texto_vacio_no_se_guarda(self):
        nota = Anotacion.objects.create(libro=self.libro(), texto="x")
        self.assertEqual(self.client.post(reverse("anotacion_editar", args=[nota.pk]), {"texto": ""}).status_code, 200)
        nota.refresh_from_db()
        self.assertEqual(nota.texto, "x")

    def test_no_edita_anotacion_ajena(self):
        nota = Anotacion.objects.create(libro=Libro.objects.create(propietario=self.otro, titulo="A"), texto="privada")
        self.assertEqual(self.client.get(reverse("anotacion_editar", args=[nota.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("anotacion_editar", args=[nota.pk]), {"texto": "hack"}).status_code, 404)


class EditarCompartidoTests(ConUsuario):
    def test_editar_datos(self):
        p = prestar(self.libro(), "Lucía")
        self.assertContains(self.client.get(reverse("prestamos")), reverse("prestamo_editar", args=[p.pk]))
        hoy = timezone.localdate()
        r = self.client.post(reverse("prestamo_editar", args=[p.pk]), {
            "persona": "Lucía M.", "contacto": "6000", "prestado_el": hoy - timedelta(days=4),
            "devolver_el": hoy + timedelta(days=3), "notas": "con cuidado",
        })
        self.assertRedirects(r, reverse("prestamos"))
        p.refresh_from_db()
        self.assertEqual((p.persona, p.dias, p.notas), ("Lucía M.", 4, "con cuidado"))

    def test_fechas_invalidas(self):
        p = prestar(self.libro(), "Lucía")
        hoy = timezone.localdate()
        r = self.client.post(reverse("prestamo_editar", args=[p.pk]), {"persona": "L", "prestado_el": hoy + timedelta(days=1)})
        self.assertContains(r, "no puede ser futura")
        r = self.client.post(reverse("prestamo_editar", args=[p.pk]), {
            "persona": "L", "prestado_el": hoy, "devolver_el": hoy - timedelta(days=2)})
        self.assertContains(r, "no puede ser antes")

    def test_editar_uno_ya_devuelto(self):
        p = prestar(self.libro(), "Lucía")
        devolver(p)
        r = self.client.post(reverse("prestamo_editar", args=[p.pk]), {"persona": "Lucía R.", "prestado_el": timezone.localdate()})
        self.assertRedirects(r, reverse("prestamos"))
        p.refresh_from_db()
        self.assertEqual(p.persona, "Lucía R.")

    def test_no_edita_compartido_ajeno(self):
        p = prestar(Libro.objects.create(propietario=self.otro, titulo="A"), "X")
        self.assertEqual(self.client.get(reverse("prestamo_editar", args=[p.pk])).status_code, 404)
