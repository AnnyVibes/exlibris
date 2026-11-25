from django.urls import reverse

from biblioteca.models import PreferenciaLibrero
from biblioteca.services.prestamos import prestar

from .base import ConUsuario


class LibreroVistaTests(ConUsuario):
    def test_por_defecto_muestra_el_librero_por_estado(self):
        self.libro(titulo="A", estado="leyendo")
        self.libro(titulo="B", estado="por_leer")
        self.libro(titulo="C", estado="leido")
        r = self.client.get(reverse("biblioteca"))
        self.assertEqual(r.context["vista"], "librero")
        estantes = {s["valor"]: [l.titulo for l in s["libros"]] for s in r.context["secciones"]}
        self.assertEqual(estantes, {"leyendo": ["A"], "por_leer": ["B"], "leido": ["C"]})
        self.assertContains(r, 'id="librero"')

    def test_filtro_de_estado_deja_un_solo_estante(self):
        self.libro(estado="leido")
        r = self.client.get(reverse("biblioteca"), {"estado": "leido"})
        self.assertEqual([s["valor"] for s in r.context["secciones"]], ["leido"])

    def test_vista_lista_y_los_filtros_la_conservan(self):
        self.libro(genero="Novela")
        r = self.client.get(reverse("biblioteca"), {"vista": "lista"})
        self.assertEqual(r.context["vista"], "lista")
        self.assertNotContains(r, 'id="librero"')
        enlaces = {e: u for e, _, u, _ in r.context["estados_nav"]}
        self.assertIn("vista=lista", enlaces["Leído"])

    def test_librero_vacio_muestra_estantes_con_ayuda(self):
        r = self.client.get(reverse("biblioteca"))
        self.assertContains(r, "Aquí irán los libros que tienes pendientes")

    def test_marca_de_prestamo(self):
        prestar(self.libro(estado="leido"), "Lucía")
        self.assertContains(self.client.get(reverse("biblioteca")), 'class="marca-prestamo"')


class PreferenciaLibreroTests(ConUsuario):
    def test_valores_por_defecto(self):
        r = self.client.get(reverse("biblioteca"))
        self.assertContains(r, "estilo-mueble librero-color-lila")

    def test_guardar_y_se_aplica(self):
        r = self.client.post(reverse("librero_preferencias"), {"estilo": "repisas", "color": "celeste", "siguiente": "/biblioteca/?estado=leido"})
        self.assertRedirects(r, "/biblioteca/?estado=leido")
        pref = PreferenciaLibrero.objects.get(usuario=self.usuario)
        self.assertEqual((pref.estilo, pref.color), ("repisas", "celeste"))
        self.assertContains(self.client.get(reverse("biblioteca")), "estilo-repisas librero-color-celeste")

    def test_valor_invalido_no_se_guarda(self):
        self.client.post(reverse("librero_preferencias"), {"estilo": "castillo", "color": "dorado"})
        pref = PreferenciaLibrero.de(self.usuario)
        self.assertEqual((pref.estilo, pref.color), ("mueble", "lila"))

    def test_cada_persona_tiene_su_preferencia(self):
        self.client.post(reverse("librero_preferencias"), {"estilo": "repisas", "color": "noche"})
        self.assertEqual(PreferenciaLibrero.de(self.otro).color, "lila")

    def test_requiere_post_y_sesion(self):
        self.assertEqual(self.client.get(reverse("librero_preferencias")).status_code, 405)
        self.client.logout()
        r = self.client.post(reverse("librero_preferencias"), {"estilo": "repisas", "color": "rosa"})
        self.assertEqual(r.status_code, 302)
        self.assertFalse(PreferenciaLibrero.objects.filter(color="rosa").exists())

    def test_redireccion_externa_ignorada(self):
        r = self.client.post(reverse("librero_preferencias"), {"estilo": "repisas", "color": "rosa", "siguiente": "https://malo.example"})
        self.assertRedirects(r, reverse("biblioteca"))
