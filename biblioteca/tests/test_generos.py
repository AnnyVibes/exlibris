from django.test import SimpleTestCase
from django.urls import reverse

from biblioteca.models import Libro
from biblioteca.services.generos import GENEROS, sugerir

from .base import ConUsuario


class SugerirGeneroTests(SimpleTestCase):
    def test_categorias_en_ingles(self):
        self.assertEqual(sugerir("Juvenile Fiction"), "Infantil")
        self.assertEqual(sugerir("Science Fiction"), "Ciencia ficción")
        self.assertEqual(sugerir("Biography & Autobiography"), "Biografía y memorias")
        self.assertEqual(sugerir("Comics & Graphic Novels"), "Cómic y manga")
        self.assertEqual(sugerir("Fiction"), "Novela")

    def test_realismo_magico_no_es_fantasia(self):
        self.assertEqual(sugerir("Magic realism", "Fiction"), "Novela")

    def test_palabras_completas(self):
        """«art» no debe coincidir dentro de «heart»."""
        self.assertEqual(sugerir("Heart"), "")

    def test_nombre_de_la_lista_sin_tildes(self):
        self.assertEqual(sugerir("poesia"), "Poesía")

    def test_desconocido(self):
        self.assertEqual(sugerir("Xyz"), "")
        self.assertEqual(sugerir(), "")

    def test_toda_la_lista_se_reconoce(self):
        for genero in GENEROS:
            self.assertEqual(sugerir(genero), genero)


class GeneroFormularioTests(ConUsuario):
    def test_genero_es_una_lista_de_opciones(self):
        r = self.client.get(reverse("libro_nuevo"))
        self.assertContains(r, '<select name="genero"')
        self.assertContains(r, '<option value="Fantasía">Fantasía</option>', html=True)

    def test_genero_fuera_de_la_lista_se_rechaza(self):
        r = self.client.post(reverse("libro_nuevo"), {"titulo": "X", "estado": "por_leer", "genero": "Inventado"})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Libro.objects.filter(titulo="X").exists())

    def test_genero_valido(self):
        self.client.post(reverse("libro_nuevo"), {"titulo": "Dune", "estado": "por_leer", "genero": "Ciencia ficción"})
        self.assertEqual(Libro.objects.get(titulo="Dune").genero, "Ciencia ficción")


class FiltrosBibliotecaTests(ConUsuario):
    def test_estado_y_genero_se_combinan(self):
        self.libro(titulo="A", estado="leido", genero="Novela")
        self.libro(titulo="B", estado="leyendo", genero="Novela")
        self.libro(titulo="C", estado="leido", genero="Poesía")
        r = self.client.get(reverse("biblioteca"), {"estado": "leido", "genero": "Novela"})
        self.assertEqual([l.titulo for l in r.context["libros"]], ["A"])
        # Los enlaces de los filtros conservan el otro filtro
        enlaces_estado = {etiqueta: url for etiqueta, _, url, _ in r.context["estados_nav"]}
        self.assertIn("genero=Novela", enlaces_estado["Leyendo"])

    def test_generos_solo_en_biblioteca(self):
        self.libro(genero="Poesía")
        self.assertNotIn("generos_nav", self.client.get(reverse("inicio")).context)
        r = self.client.get(reverse("biblioteca"))
        self.assertEqual([(n, c) for n, c, _, _ in r.context["generos_nav"]], [("Poesía", 1)])

    def test_estado_invalido_se_ignora(self):
        self.libro()
        r = self.client.get(reverse("biblioteca"), {"estado": "xxx"})
        self.assertEqual(len(r.context["libros"]), 1)
