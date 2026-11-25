from django.urls import reverse

from .base import ConUsuario


class SeccionGenerosTests(ConUsuario):
    def test_enlace_en_la_barra_lateral(self):
        r = self.client.get(reverse("inicio"))
        self.assertContains(r, f'href="{reverse("generos")}"')

    def test_una_tarjeta_por_genero_con_conteo(self):
        self.libro(titulo="A", genero="Novela", estado="leido")
        self.libro(titulo="B", genero="Novela")
        self.libro(titulo="C", genero="Poesía")
        self.libro(titulo="Sin", genero="")
        self.libro(titulo="Ajeno", genero="Terror", propietario=self.otro)
        r = self.client.get(reverse("generos"))
        tarjetas = {t["nombre"]: (t["total"], t["leidos"]) for t in r.context["tarjetas"]}
        self.assertEqual(tarjetas, {"Novela": (2, 1), "Poesía": (1, 0)})
        self.assertEqual(r.context["sin_genero"], 1)
        self.assertContains(r, "?genero=Novela")

    def test_vacio(self):
        self.assertContains(self.client.get(reverse("generos")), "Todavía no hay géneros")

    def test_requiere_sesion(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("generos")).status_code, 302)


class MensajesTests(ConUsuario):
    def test_mensaje_con_boton_cerrar(self):
        libro = self.libro()
        r = self.client.post(reverse("anotacion_crear", args=[libro.pk]), {"texto": "Idea"}, follow=True)
        self.assertContains(r, 'class="cerrar-mensaje"')
