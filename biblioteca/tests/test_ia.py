"""Pruebas de la fase 2 (IA). n8n se simula: no se llama a ningún servicio real."""

import json
from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse

from biblioteca.models import Anotacion, Libro
from biblioteca.services import ia
from biblioteca.services.prestamos import prestar

from .base import ConUsuario


def post_json(client, url, datos):
    return client.post(url, data=json.dumps(datos), content_type="application/json")


class ServicioIATests(ConUsuario):
    def test_clasificar_normaliza_genero_y_etiquetas(self):
        with patch.object(ia, "_llamar", return_value={"genero": "Fantasy", "etiquetas": "Magia, Dragones , ,Épica"}):
            r = ia.clasificar("El hobbit", "Tolkien")
        self.assertEqual(r, {"genero": "Fantasía", "etiquetas": ["magia", "dragones", "épica"]})

    def test_clasificar_envia_la_lista_de_generos(self):
        with patch.object(ia, "_llamar", return_value={"genero": "Novela", "etiquetas": []}) as llamar:
            ia.clasificar("Rayuela")
        ruta, datos = llamar.call_args[0]
        self.assertEqual((ruta, datos["tarea"]), ("exlibris-tarea", "clasificar"))
        self.assertIn("Fantasía", datos["generos"])

    def test_respuesta_envuelta_en_lista_u_output(self):
        from io import BytesIO

        class Resp(BytesIO):
            def __enter__(self): return self
            def __exit__(self, *a): pass

        with patch("biblioteca.services.ia.urlopen", return_value=Resp(b'[{"output": {"resumen": "ok"}}]')):
            self.assertEqual(ia._llamar("exlibris-tarea", {}), {"resumen": "ok"})

    def test_n8n_apagado(self):
        from urllib.error import URLError
        with patch("biblioteca.services.ia.urlopen", side_effect=URLError("refused")):
            with self.assertRaisesMessage(ia.IANoDisponible, "n8n"):
                ia._llamar("exlibris-tarea", {})

    @override_settings(N8N_SECRET="clave-compartida")
    def test_envia_cabecera_secreta(self):
        from io import BytesIO

        class Resp(BytesIO):
            def __enter__(self): return self
            def __exit__(self, *a): pass

        with patch("biblioteca.services.ia.urlopen", return_value=Resp(b'{"a": 1}')) as abrir:
            ia._llamar("x", {})
        self.assertEqual(abrir.call_args[0][0].get_header("X-exlibris-secret"), "clave-compartida")

    def test_resumir_sin_anotaciones(self):
        with self.assertRaises(ValueError):
            ia.resumir(self.libro())

    def test_resumir_limita_el_texto(self):
        libro = self.libro()
        for i in range(80):
            Anotacion.objects.create(libro=libro, texto="x" * 300, pagina=i)
        with patch.object(ia, "_llamar", return_value={"resumen": "Temas: x"}) as llamar:
            ia.resumir(libro)
        notas = llamar.call_args[0][1]["anotaciones"]
        self.assertLessEqual(sum(len(n["texto"]) for n in notas), ia.MAX_CARACTERES)

    def test_respuesta_sin_texto(self):
        with patch.object(ia, "_llamar", return_value={"otra": 1}):
            with self.assertRaises(ia.IANoDisponible):
                ia.borrador_resena(self.libro())


class VistasIATests(ConUsuario):
    def test_clasificar(self):
        with patch.object(ia, "_llamar", return_value={"genero": "Poesía", "etiquetas": ["amor"]}):
            r = post_json(self.client, reverse("ia_clasificar"), {"titulo": "Veinte poemas"})
        self.assertEqual(r.json(), {"genero": "Poesía", "etiquetas": ["amor"]})

    def test_clasificar_sin_titulo(self):
        self.assertEqual(post_json(self.client, reverse("ia_clasificar"), {"titulo": " "}).status_code, 400)

    def test_ia_apagada_devuelve_503_con_mensaje(self):
        with patch.object(ia, "_llamar", side_effect=ia.IANoDisponible("La IA no está disponible.")):
            r = post_json(self.client, reverse("ia_clasificar"), {"titulo": "X"})
        self.assertEqual((r.status_code, r.json()["error"]), (503, "La IA no está disponible."))

    def test_borrador_de_resena_no_guarda(self):
        libro = self.libro()
        with patch.object(ia, "_llamar", return_value={"resena": "Un libro inolvidable."}) as llamar:
            r = post_json(self.client, reverse("ia_resena", args=[libro.pk]), {"calificacion": "5"})
        self.assertEqual(r.json()["texto"], "Un libro inolvidable.")
        self.assertEqual(llamar.call_args[0][1]["calificacion"], 5)
        self.assertFalse(hasattr(Libro.objects.get(pk=libro.pk), "resena") and Libro.objects.get(pk=libro.pk).resena)

    def test_resumir_guarda_y_muestra(self):
        libro = self.libro()
        Anotacion.objects.create(libro=libro, texto="La Maga y el azar")
        with patch.object(ia, "_llamar", return_value={"resumen": "Tus notas hablan del azar."}):
            r = self.client.post(reverse("ia_resumir", args=[libro.pk]), follow=True)
        libro.refresh_from_db()
        self.assertEqual(libro.resumen_ia, "Tus notas hablan del azar.")
        self.assertIsNotNone(libro.resumen_ia_fecha)
        self.assertContains(r, "Tus notas hablan del azar.")

    def test_resumir_con_ia_apagada_no_borra_el_anterior(self):
        libro = self.libro(resumen_ia="Resumen viejo")
        Anotacion.objects.create(libro=libro, texto="nota")
        with patch.object(ia, "_llamar", side_effect=ia.IANoDisponible("La IA no está disponible.")):
            r = self.client.post(reverse("ia_resumir", args=[libro.pk]), follow=True)
        self.assertContains(r, "No se pudo completar")
        libro.refresh_from_db()
        self.assertEqual(libro.resumen_ia, "Resumen viejo")

    def test_no_usa_ia_en_libro_ajeno(self):
        ajeno = Libro.objects.create(propietario=self.otro, titulo="A")
        self.assertEqual(post_json(self.client, reverse("ia_resena", args=[ajeno.pk]), {}).status_code, 404)
        self.assertEqual(self.client.post(reverse("ia_resumir", args=[ajeno.pk])).status_code, 404)

    def test_agente(self):
        with patch.object(ia, "_llamar", return_value={"output": "Rayuela la tiene Lucía."}) as llamar:
            r = post_json(self.client, reverse("ia_agente"), {"mensaje": "¿Quién tiene Rayuela?", "sesion": "abc"})
        self.assertEqual(r.json()["respuesta"], "Rayuela la tiene Lucía.")
        datos = llamar.call_args[0][1]
        self.assertEqual(datos["sesion"], f"exlibris-{self.usuario.pk}-abc")
        self.assertEqual(ia.usuario_de_token(datos["token"]), self.usuario.pk)
        self.assertTrue(datos["api"].endswith("/api/ia"))

    def test_agente_requiere_mensaje_post_y_sesion(self):
        self.assertEqual(post_json(self.client, reverse("ia_agente"), {"mensaje": ""}).status_code, 400)
        self.assertEqual(self.client.get(reverse("ia_agente")).status_code, 405)
        self.client.logout()
        self.assertEqual(post_json(self.client, reverse("ia_agente"), {"mensaje": "hola"}).status_code, 302)

    def test_paginas_con_botones_de_ia(self):
        libro = self.libro()
        Anotacion.objects.create(libro=libro, texto="nota")
        self.assertContains(self.client.get(reverse("asistente")), "Asistente IA")
        self.assertContains(self.client.get(reverse("libro_detalle", args=[libro.pk])), "Sugerir borrador con IA")
        self.assertContains(self.client.get(reverse("libro_detalle", args=[libro.pk])), "Resumir con IA")
        self.assertContains(self.client.get(reverse("libro_nuevo")), "Sugerir con IA")


class APIAgenteTests(ConUsuario):
    def cabecera(self, usuario=None):
        return {"HTTP_X_EXLIBRIS_TOKEN": ia.token_para(usuario or self.usuario)}

    def test_sin_token_o_token_falso(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("api_ia_libros")).status_code, 401)
        self.assertEqual(self.client.get(reverse("api_ia_libros"), HTTP_X_EXLIBRIS_TOKEN="falso").status_code, 401)

    @override_settings(IA_TOKEN_MINUTOS=0)
    def test_token_caducado(self):
        import time
        token = ia.token_para(self.usuario)
        time.sleep(1.1)
        self.assertEqual(self.client.get(reverse("api_ia_libros"), HTTP_X_EXLIBRIS_TOKEN=token).status_code, 401)

    def test_libros_solo_de_quien_pregunta(self):
        self.client.logout()
        self.libro(titulo="Rayuela", estado="leido")
        Libro.objects.create(propietario=self.otro, titulo="Secreto")
        r = self.client.get(reverse("api_ia_libros"), {"q": ""}, **self.cabecera())
        self.assertEqual([l["titulo"] for l in r.json()["libros"]], ["Rayuela"])
        r = self.client.get(reverse("api_ia_libros"), {"estado": "por_leer"}, **self.cabecera())
        self.assertEqual(r.json()["total"], 0)

    def test_compartidos_y_detalle(self):
        self.client.logout()
        libro = self.libro(titulo="Rayuela")
        Anotacion.objects.create(libro=libro, texto="La Maga", pagina=3)
        prestar(libro, "Lucía")
        r = self.client.get(reverse("api_ia_compartidos"), **self.cabecera())
        self.assertEqual(r.json()["compartidos"][0]["persona"], "Lucía")
        d = self.client.get(reverse("api_ia_libro", args=[libro.pk]), **self.cabecera()).json()
        self.assertEqual((d["compartido_con"], d["notas"][0]["texto"]), ("Lucía", "La Maga"))
        ajeno = Libro.objects.create(propietario=self.otro, titulo="X")
        self.assertEqual(self.client.get(reverse("api_ia_libro", args=[ajeno.pk]), **self.cabecera()).status_code, 404)

    def test_anotaciones_y_resumen(self):
        self.client.logout()
        libro = self.libro(genero="Novela")
        Anotacion.objects.create(libro=libro, texto="El tiempo es circular")
        r = self.client.get(reverse("api_ia_anotaciones"), {"q": "tiempo"}, **self.cabecera())
        self.assertEqual(len(r.json()["anotaciones"]), 1)
        r = self.client.get(reverse("api_ia_resumen"), **self.cabecera())
        self.assertEqual((r.json()["total"], r.json()["generos"]), (1, {"Novela": 1}))

    def test_solo_lectura(self):
        self.client.logout()
        self.assertEqual(self.client.post(reverse("api_ia_libros"), **self.cabecera()).status_code, 405)


class FormatoRespuestasTests(ConUsuario):
    def test_markdown_simple_y_seguro(self):
        from biblioteca.templatetags.exlibris import markdown_simple
        html = markdown_simple("Tienes:\n\n* **Rayuela** con Lucía\n* <script>x</script>\n\nFin *bien*")
        self.assertIn("<ul><li><strong>Rayuela</strong> con Lucía</li>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<script>", html)
        self.assertIn("<em>bien</em>", html)

    def test_borrador_sin_marcas(self):
        with patch.object(ia, "_llamar", return_value={"resena": "* Me **encantó** el final."}):
            self.assertEqual(ia.borrador_resena(self.libro()), "Me encantó el final.")

    def test_resumen_se_muestra_con_formato(self):
        libro = self.libro(resumen_ia="**Temas:**\n- azar\n- juego")
        Anotacion.objects.create(libro=libro, texto="x")
        r = self.client.get(reverse("libro_detalle", args=[libro.pk]))
        self.assertContains(r, "<strong>Temas:</strong>", html=False)
        self.assertContains(r, "<li>azar</li>", html=False)


class LimpiarIdsTests(ConUsuario):
    def test_quita_ids_de_la_respuesta(self):
        casos = {
            "* **Rayuela** (ID: 25) con Lucía.": "* **Rayuela** con Lucía.",
            "Tienes «Ficciones» (id 7).": "Tienes «Ficciones».",
            "El libro Sapiens, ID: 12, está en lectura.": "El libro Sapiens, está en lectura.",
            "Rayuela [ID#3] te la devolvió.": "Rayuela te la devolvió.",
            "Leíste 25 libros este año.": "Leíste 25 libros este año.",
        }
        for entrada, esperado in casos.items():
            self.assertEqual(ia.limpiar_ids(entrada), esperado)

    def test_agente_devuelve_sin_ids(self):
        with patch.object(ia, "_llamar", return_value={"respuesta": "**Cuerpo humano** (ID: 25) con Carla."}):
            r = post_json(self.client, reverse("ia_agente"), {"mensaje": "hola"})
        self.assertEqual(r.json()["respuesta"], "**Cuerpo humano** con Carla.")


class AgregarLibroAgenteTests(ConUsuario):
    DATOS = {"isbn": "9780307474728", "titulo": "Cien años de soledad", "autores": "Gabriel García Márquez",
             "paginas": 417, "genero": "Novela"}

    def post(self, datos, usuario=None):
        self.client.logout()
        return self.client.post(reverse("api_ia_agregar"), data=json.dumps(datos), content_type="application/json",
                                HTTP_X_EXLIBRIS_TOKEN=ia.token_para(usuario or self.usuario))

    @patch("biblioteca.services.catalogo.buscar_por_isbn")
    @patch("biblioteca.services.catalogo.buscar_por_titulo")
    def test_busca_el_isbn_y_agrega(self, buscar_titulo, buscar_datos):
        buscar_titulo.return_value = {"isbn": "9780307474728", "titulo": "Cien años de soledad"}
        buscar_datos.return_value = dict(self.DATOS)
        r = self.post({"titulo": "Cien años de soledad", "autores": "García Márquez"})
        self.assertEqual(r.status_code, 201)
        buscar_titulo.assert_called_once_with("Cien años de soledad", "García Márquez")
        libro = Libro.objects.get(propietario=self.usuario, isbn="9780307474728")
        self.assertEqual((libro.estado, libro.genero, libro.paginas), ("por_leer", "Novela", 417))
        self.assertEqual(r.json()["libro"]["isbn"], "9780307474728")

    @patch("biblioteca.services.catalogo.buscar_por_isbn", return_value={})
    @patch("biblioteca.services.catalogo.buscar_por_titulo", return_value={"isbn": "9788437604572", "paginas": 736})
    def test_usa_el_isbn_que_da_la_persona(self, *_):
        self.post({"titulo": "Rayuela", "isbn": "0-307-47472-0"})
        libro = Libro.objects.get(titulo="Rayuela")
        self.assertEqual((libro.isbn, libro.paginas), ("9780307474728", 736))  # ISBN de la persona, datos completados

    @patch("biblioteca.services.catalogo.buscar_por_isbn", return_value={})
    @patch("biblioteca.services.catalogo.buscar_por_titulo", return_value={})
    def test_sin_isbn_igual_lo_agrega(self, *_):
        r = self.post({"titulo": "Libro raro", "autores": "Nadie"})
        self.assertEqual(r.status_code, 201)
        self.assertIn("No se encontró su ISBN", r.json()["mensaje"])

    @patch("biblioteca.services.catalogo.buscar_por_isbn", return_value={})
    @patch("biblioteca.services.catalogo.buscar_por_titulo", return_value={"isbn": "9780307474728"})
    def test_no_duplica(self, *_):
        self.libro(titulo="Otro título", isbn="9780307474728")
        r = self.post({"titulo": "Cien años de soledad"})
        self.assertEqual((r.status_code, r.json()["creado"]), (200, False))
        self.libro(titulo="Rayuela")
        r = self.post({"titulo": "rayuela"})
        self.assertFalse(r.json()["creado"])
        self.assertEqual(Libro.objects.filter(propietario=self.usuario).count(), 2)

    def test_requiere_token_titulo_y_post(self):
        self.client.logout()
        self.assertEqual(self.client.post(reverse("api_ia_agregar"), data="{}", content_type="application/json").status_code, 401)
        self.assertEqual(self.post({"titulo": " "}).status_code, 400)
        self.assertEqual(self.client.get(reverse("api_ia_agregar"), HTTP_X_EXLIBRIS_TOKEN=ia.token_para(self.usuario)).status_code, 405)

    @patch("biblioteca.services.catalogo.buscar_por_isbn", return_value={})
    @patch("biblioteca.services.catalogo.buscar_por_titulo", return_value={})
    def test_se_agrega_a_quien_pregunta(self, *_):
        self.post({"titulo": "Solo mío"}, usuario=self.otro)
        self.assertTrue(Libro.objects.filter(propietario=self.otro, titulo="Solo mío").exists())
        self.assertFalse(Libro.objects.filter(propietario=self.usuario, titulo="Solo mío").exists())


class BuscarIsbnPorTituloTests(ConUsuario):
    def test_prefiere_google_en_espanol_y_valida(self):
        from biblioteca.services import catalogo
        google = {"items": [{"volumeInfo": {"industryIdentifiers": [{"type": "ISBN_10", "identifier": "0307474720"}]}}]}
        with patch.object(catalogo, "_get_json", return_value=google) as get:
            self.assertEqual(catalogo.buscar_isbn_por_titulo("Cien años de soledad", "García Márquez"), "9780307474728")
        self.assertIn("langRestrict=es", get.call_args_list[0][0][0])

    def test_respaldo_open_library_y_nada(self):
        from biblioteca.services import catalogo

        def falso(url):
            return {"docs": [{"isbn": ["123", "9780307474728"]}]} if "openlibrary" in url else {"items": []}
        with patch.object(catalogo, "_get_json", side_effect=falso):
            self.assertEqual(catalogo.buscar_isbn_por_titulo("Cien años"), "9780307474728")
        with patch.object(catalogo, "_get_json", return_value=None):
            self.assertEqual(catalogo.buscar_isbn_por_titulo("X"), "")
