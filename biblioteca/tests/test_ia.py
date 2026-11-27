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
