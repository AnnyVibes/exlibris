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
            "password1": "Una-clave-larga-99", "password2": "Una-clave-larga-99", "tratamiento": "lector",
        })
        self.assertRedirects(r, reverse("inicio"))
        self.assertEqual(self.client.get(reverse("inicio")).status_code, 200)
        from biblioteca.models import Perfil
        from django.contrib.auth.models import User
        self.assertEqual(Perfil.de(User.objects.get(username="carla")).tratamiento, "lector")


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

    @patch("biblioteca.views.catalogo.buscar_por_titulo", return_value={"paginas": 417, "descripcion": "Macondo"})
    @patch("biblioteca.views.catalogo.buscar_por_isbn")
    def test_busqueda_por_isbn_precarga_formulario(self, buscar, _titulo):
        """Al escanear se llega a /libros/nuevo/?isbn=… con los datos del catálogo ya puestos."""
        buscar.return_value = {"isbn": "9780307474728", "titulo": "Cien años de soledad", "autores": "García Márquez"}
        r = self.client.get(reverse("libro_nuevo"), {"isbn": "978-0307474728"})
        buscar.assert_called_once_with("9780307474728")
        self.assertContains(r, 'value="Cien años de soledad"')
        self.assertContains(r, "Encontramos el libro")
        self.assertContains(r, 'value="417"')  # completado por título: esa edición no traía páginas

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


class AccesoPantallaTests(ConUsuario):
    def test_login_con_recordarme_mantiene_la_sesion(self):
        self.client.logout()
        self.client.post(reverse("login"), {"username": "ana", "password": "clave-segura-123", "recordarme": "on"})
        self.assertFalse(self.client.session.get_expire_at_browser_close())

    def test_login_sin_recordarme_expira_al_cerrar(self):
        self.client.logout()
        self.client.post(reverse("login"), {"username": "ana", "password": "clave-segura-123"})
        self.assertTrue(self.client.session.get_expire_at_browser_close())
        self.assertEqual(self.client.get(reverse("inicio")).status_code, 200)

    def test_login_incorrecto_muestra_error(self):
        self.client.logout()
        r = self.client.post(reverse("login"), {"username": "ana", "password": "mal"})
        self.assertContains(r, "Usuario o contraseña incorrectos")

    def test_registro_muestra_errores_por_campo(self):
        self.client.logout()
        r = self.client.post(reverse("registro"), {"username": "ana", "email": "x@example.com", "password1": "a", "password2": "b"})
        self.assertContains(r, 'class="acceso-error-campo"')
        self.assertContains(r, "Te damos la bienvenida", count=0)


class CacheEstaticosTests(ConUsuario):
    def test_css_con_version_para_evitar_cache_vieja(self):
        import re
        self.client.logout()
        html = self.client.get(reverse("login")).content.decode()
        self.assertRegex(html, r'exlibris\.css\?v=\d+')


class CacheImagenesTests(ConUsuario):
    def test_imagenes_con_version(self):
        self.client.logout()
        html = self.client.get(reverse("login")).content.decode()
        self.assertRegex(html, r'exlibris\.css\?v=\d+')
        self.assertNotRegex(html, r'\.(svg|css)["\')]')  # ningún estático sin versión


class CompletarDatosFormularioTests(ConUsuario):
    def post(self, datos):
        import json
        return self.client.post(reverse("completar_datos"), data=json.dumps(datos), content_type="application/json")

    def test_la_ia_completa_y_valida(self):
        from unittest.mock import patch
        from biblioteca.services import ia
        respuesta = {"autores": "Julio Cortázar", "editorial": "Alfaguara", "anio": 1963, "paginas": "633",
                     "genero": "zzz", "descripcion": "Una **novela** que se lee en varios órdenes.",
                     "isbn": "9788432221553"}  # dígito de control incorrecto: se descarta
        with patch.object(ia, "_llamar", return_value=respuesta) as llamar:
            r = self.post({"titulo": "Rayuela", "autores": "Julio Cortazar"})
        enviado = llamar.call_args[0][1]
        self.assertEqual((enviado["tarea"], enviado["titulo"]), ("completar", "Rayuela"))
        d = r.json()
        self.assertEqual((d["paginas"], d["anio"], d["editorial"]), (633, 1963, "Alfaguara"))
        self.assertEqual(d["descripcion"], "Una novela que se lee en varios órdenes.")
        self.assertNotIn("isbn", d)
        self.assertNotIn("genero", d)  # solo géneros de la lista

    def test_isbn_valido_y_datos_imposibles(self):
        from unittest.mock import patch
        from biblioteca.services import ia
        with patch.object(ia, "_llamar", return_value={"isbn": "978-84-322-2155-2", "anio": 3050, "paginas": 0, "genero": "Novela"}):
            d = self.post({"titulo": "Rayuela"}).json()
        self.assertEqual(d, {"isbn": "9788432221552", "genero": "Novela"})

    def test_requiere_titulo_e_ia_apagada(self):
        from unittest.mock import patch
        from biblioteca.services import ia
        self.assertEqual(self.post({"titulo": " ", "isbn": "9788432221552"}).status_code, 400)
        with patch.object(ia, "_llamar", side_effect=ia.IANoDisponible("La IA no está disponible.")):
            self.assertEqual(self.post({"titulo": "Rayuela"}).status_code, 503)

    def test_boton_en_el_formulario_y_no_en_la_ficha(self):
        libro = self.libro()
        self.assertContains(self.client.get(reverse("libro_editar", args=[libro.pk])), "Completar datos con IA")
        self.assertContains(self.client.get(reverse("libro_nuevo")), "Escribir con IA")
        self.assertNotContains(self.client.get(reverse("libro_detalle", args=[libro.pk])), "Completar datos")

