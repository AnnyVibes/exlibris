import shutil
import tempfile
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from PIL import Image

from biblioteca.models import Libro

from .base import ConUsuario

MEDIA = tempfile.mkdtemp(prefix="exlibris-test-media-")


def imagen(nombre="portada.png", tam=(300, 450), formato="PNG"):
    buffer = BytesIO()
    Image.new("RGB", tam, (139, 127, 209)).save(buffer, format=formato)
    return SimpleUploadedFile(nombre, buffer.getvalue(), content_type=f"image/{formato.lower()}")


@override_settings(MEDIA_ROOT=MEDIA)
class PortadaTests(ConUsuario):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def datos(self, **extra):
        return {"titulo": "Con portada", "estado": "por_leer", **extra}

    def test_subir_portada_al_crear(self):
        r = self.client.post(reverse("libro_nuevo"), self.datos(portada=imagen()))
        libro = Libro.objects.get(titulo="Con portada")
        self.assertRedirects(r, reverse("libro_detalle", args=[libro.pk]))
        self.assertTrue(libro.portada.name.startswith("portadas/"))
        self.assertEqual(libro.imagen_portada, libro.portada.url)
        self.assertContains(self.client.get(reverse("biblioteca")), libro.portada.url)

    def test_imagen_grande_se_reduce(self):
        self.client.post(reverse("libro_nuevo"), self.datos(portada=imagen(tam=(2000, 3000), formato="JPEG", nombre="g.jpg")))
        libro = Libro.objects.get(titulo="Con portada")
        with Image.open(libro.portada.path) as img:
            self.assertLessEqual(max(img.size), 900)

    def test_archivo_que_no_es_imagen(self):
        falso = SimpleUploadedFile("virus.png", b"esto no es una imagen", content_type="image/png")
        r = self.client.post(reverse("libro_nuevo"), self.datos(portada=falso))
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Libro.objects.filter(titulo="Con portada").exists())

    def test_formato_no_permitido(self):
        r = self.client.post(reverse("libro_nuevo"), self.datos(portada=imagen(nombre="p.gif", formato="GIF")))
        self.assertContains(r, "JPG, PNG o WEBP")

    @override_settings(PORTADA_MAX_MB=0)
    def test_limite_de_tamano(self):
        r = self.client.post(reverse("libro_nuevo"), self.datos(portada=imagen()))
        self.assertContains(r, "pesa más de")

    def test_subida_tiene_prioridad_sobre_enlace(self):
        self.client.post(reverse("libro_nuevo"), self.datos(portada=imagen(), portada_url="https://example.com/a.jpg"))
        libro = Libro.objects.get(titulo="Con portada")
        self.assertNotEqual(libro.imagen_portada, "https://example.com/a.jpg")

    def test_cambiar_y_quitar_borra_el_archivo_anterior(self):
        self.client.post(reverse("libro_nuevo"), self.datos(portada=imagen()))
        libro = Libro.objects.get(titulo="Con portada")
        primera = libro.portada.path
        self.client.post(reverse("libro_editar", args=[libro.pk]), self.datos(portada=imagen(nombre="otra.png")))
        libro.refresh_from_db()
        self.assertNotEqual(libro.portada.path, primera)
        import os
        self.assertFalse(os.path.exists(primera))
        segunda = libro.portada.path
        self.client.post(reverse("libro_editar", args=[libro.pk]), self.datos(**{"portada-clear": "on"}))
        libro.refresh_from_db()
        self.assertFalse(libro.portada)
        self.assertFalse(os.path.exists(segunda))

    def test_editar_sin_archivo_conserva_portada(self):
        self.client.post(reverse("libro_nuevo"), self.datos(portada=imagen()))
        libro = Libro.objects.get(titulo="Con portada")
        nombre = libro.portada.name
        self.client.post(reverse("libro_editar", args=[libro.pk]), self.datos(titulo="Nuevo título"))
        libro.refresh_from_db()
        self.assertEqual((libro.titulo, libro.portada.name), ("Nuevo título", nombre))

    def test_eliminar_libro_borra_su_portada(self):
        import os
        self.client.post(reverse("libro_nuevo"), self.datos(portada=imagen()))
        libro = Libro.objects.get(titulo="Con portada")
        ruta = libro.portada.path
        self.client.post(reverse("libro_eliminar", args=[libro.pk]))
        self.assertFalse(os.path.exists(ruta))
