from unittest.mock import patch

from django.urls import reverse

from biblioteca.models import Libro

from .base import ConUsuario


class AccesoTests(ConUsuario):
    def test_paginas_requieren_sesion(self):
        self.client.logout()
        for nombre in ("inicio", "biblioteca", "escanear", "libro_nuevo", "anotaciones", "prestamos", "estadisticas"):
            r = self.client.get(reverse(nombre))
            self.assertEqual(r.status_code, 302, nombre)
            self.assertIn(reverse("login"), r["Location"])

    def test_paginas_cargan_con_sesion(self):
        self.libro(estado=Libro.Estado.LEYENDO, genero="Novela")
        for nombre in ("inicio", "biblioteca", "escanear", "libro_nuevo", "anotaciones", "prestamos", "estadisticas"):
            self.assertEqual(self.client.get(reverse(nombre)).status_code, 200, nombre)

    def test_no_ve_libros_de_otro_usuario(self):
        ajeno = Libro.objects.create(propietario=self.otro, titulo="Secreto")
        self.assertEqual(self.client.get(reverse("libro_detalle", args=[ajeno.pk])).status_code, 404)
        self.assertNotContains(self.client.get(reverse("biblioteca")), "Secreto")
        self.assertEqual(self.client.post(reverse("libro_eliminar", args=[ajeno.pk])).status_code, 404)
        self.assertTrue(Libro.objects.filter(pk=ajeno.pk).exists())

    def test_registro_crea_cuenta_e_inicia_sesion(self):
        self.client.logout()
        r = self.client.post(reverse("registro"), {
            "username": "carla", "email": "carla@example.com",
            "password1": "Una-clave-larga-99", "password2": "Una-clave-larga-99",
        })
        self.assertRedirects(r, reverse("inicio"))
        self.assertEqual(self.client.get(reverse("inicio")).status_code, 200)


class AltaLibroTests(ConUsuario):
    def test_alta_manual_normaliza_isbn(self):
        r = self.client.post(reverse("libro_nuevo"), {
            "isbn": "0-307-47472-0", "titulo": "Cien años de soledad", "estado": "por_leer",
        })
        libro = Libro.objects.get(titulo="Cien años de soledad")
        self.assertRedirects(r, reverse("libro_detalle", args=[libro.pk]))
        self.assertEqual(libro.isbn, "9780307474728")
        self.assertEqual(libro.propietario, self.usuario)

    def test_alta_sin_isbn(self):
        self.client.post(reverse("libro_nuevo"), {"titulo": "Libro viejo sin código", "estado": "leido"})
        self.assertTrue(Libro.objects.filter(titulo="Libro viejo sin código", isbn="").exists())

    def test_isbn_invalido_no_guarda(self):
        r = self.client.post(reverse("libro_nuevo"), {"isbn": "123", "titulo": "X", "estado": "por_leer"})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "no es válido")
        self.assertFalse(Libro.objects.filter(titulo="X").exists())

    def test_isbn_repetido_en_mi_biblioteca(self):
        self.libro(isbn="9780307474728")
        r = self.client.post(reverse("libro_nuevo"), {"isbn": "9780307474728", "titulo": "Otra vez", "estado": "por_leer"})
        self.assertContains(r, "Ya tienes este libro")

    def test_mismo_isbn_en_otra_biblioteca_si_se_permite(self):
        Libro.objects.create(propietario=self.otro, titulo="Rayuela", isbn="9780307474728")
        self.client.post(reverse("libro_nuevo"), {"isbn": "9780307474728", "titulo": "Rayuela", "estado": "por_leer"})
        self.assertEqual(Libro.objects.filter(propietario=self.usuario, isbn="9780307474728").count(), 1)

    @patch("biblioteca.views.catalogo.buscar_por_isbn")
    def test_busqueda_por_isbn_precarga_formulario(self, buscar):
        """Al escanear se llega a /libros/nuevo/?isbn=… con los datos del catálogo ya puestos."""
        buscar.return_value = {"isbn": "9780307474728", "titulo": "Cien años de soledad", "autores": "García Márquez"}
        r = self.client.get(reverse("libro_nuevo"), {"isbn": "978-0307474728"})
        buscar.assert_called_once_with("9780307474728")
        self.assertContains(r, 'value="Cien años de soledad"')
        self.assertContains(r, "Encontramos el libro")

    @patch("biblioteca.views.catalogo.buscar_por_isbn", return_value={})
    def test_isbn_no_encontrado_permite_completar_a_mano(self, _):
        r = self.client.get(reverse("libro_nuevo"), {"isbn": "9780307474728"})
        self.assertContains(r, "Completa los datos a mano")
        self.assertContains(r, 'value="9780307474728"')

    @patch("biblioteca.views.catalogo.buscar_por_isbn")
    def test_escanear_un_libro_que_ya_tengo_lleva_a_su_ficha(self, buscar):
        libro = self.libro(isbn="9780307474728")
        r = self.client.get(reverse("libro_nuevo"), {"isbn": "9780307474728"})
        self.assertRedirects(r, reverse("libro_detalle", args=[libro.pk]))
        buscar.assert_not_called()

    def test_isbn_escaneado_invalido_muestra_aviso(self):
        r = self.client.get(reverse("libro_nuevo"), {"isbn": "7501055363278"})
        self.assertContains(r, "no es válido")


class BibliotecaTests(ConUsuario):
    def test_busqueda_y_filtros(self):
        self.libro(titulo="Rayuela", estado="leido", genero="Novela")
        self.libro(titulo="Ficciones", autores="Borges", estado="leyendo", genero="Cuento")
        r = self.client.get(reverse("biblioteca"), {"q": "borges"})
        self.assertContains(r, "Ficciones")
        self.assertNotContains(r, "Rayuela")
        r = self.client.get(reverse("biblioteca"), {"estado": "leido"})
        self.assertContains(r, "Rayuela")
        self.assertNotContains(r, "Ficciones")
        r = self.client.get(reverse("biblioteca"), {"genero": "cuento"})
        self.assertContains(r, "Ficciones")

    def test_progreso(self):
        libro = self.libro()
        self.client.post(reverse("progreso_actualizar", args=[libro.pk]), {"estado": "leyendo", "pagina_actual": 150})
        libro.refresh_from_db()
        self.assertEqual(libro.progreso, 25)

    def test_progreso_no_supera_paginas(self):
        libro = self.libro()
        self.client.post(reverse("progreso_actualizar", args=[libro.pk]), {"estado": "leyendo", "pagina_actual": 900})
        libro.refresh_from_db()
        self.assertEqual(libro.pagina_actual, 0)

    def test_marcar_leido_completa_paginas(self):
        libro = self.libro()
        self.client.post(reverse("progreso_actualizar", args=[libro.pk]), {"estado": "leido", "pagina_actual": 10})
        libro.refresh_from_db()
        self.assertEqual(libro.progreso, 100)

    def test_editar_y_eliminar(self):
        libro = self.libro()
        self.client.post(reverse("libro_editar", args=[libro.pk]), {"titulo": "Rayuela (ed. 2019)", "estado": "leido"})
        libro.refresh_from_db()
        self.assertEqual(libro.titulo, "Rayuela (ed. 2019)")
        self.assertEqual(self.client.get(reverse("libro_eliminar", args=[libro.pk])).status_code, 405)
        self.client.post(reverse("libro_eliminar", args=[libro.pk]))
        self.assertFalse(Libro.objects.filter(pk=libro.pk).exists())


class EstadosTests(ConUsuario):
    def test_no_existe_abandonado(self):
        self.assertNotIn("abandonado", Libro.Estado.values)
        r = self.client.post(reverse("libro_nuevo"), {"titulo": "X", "estado": "abandonado"})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Libro.objects.filter(titulo="X").exists())
        self.assertNotContains(self.client.get(reverse("biblioteca")), "Abandonado")

    def test_migracion_pasa_abandonados_a_por_leer(self):
        from importlib import import_module

        from django.apps import apps
        migracion = import_module("biblioteca.migrations.0003_quitar_abandonado")
        libro = self.libro()
        Libro.objects.filter(pk=libro.pk).update(estado="abandonado")
        migracion.abandonados_a_por_leer(apps, None)
        libro.refresh_from_db()
        self.assertEqual(libro.estado, "por_leer")
