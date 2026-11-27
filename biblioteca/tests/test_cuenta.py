import os
import shutil
import tempfile
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from PIL import Image

from biblioteca.models import Perfil

from .base import ConUsuario

MEDIA = tempfile.mkdtemp(prefix="exlibris-test-perfil-")


def foto(tam=(800, 500)):
    b = BytesIO()
    Image.new("RGB", tam, (200, 100, 150)).save(b, format="PNG")
    return SimpleUploadedFile("yo.png", b.getvalue(), content_type="image/png")


@override_settings(MEDIA_ROOT=MEDIA)
class CuentaTests(ConUsuario):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def datos(self, **extra):
        return {"first_name": "Ana", "last_name": "Pérez", "email": "ana@example.com", "tratamiento": "lectora", **extra}

    def test_mi_cuenta_en_el_menu_no_lleva_al_admin(self):
        r = self.client.get(reverse("inicio"))
        self.assertContains(r, f'href="{reverse("cuenta")}"')
        self.assertNotContains(r, "/admin/")

    def test_cambiar_nombre_y_tratamiento(self):
        r = self.client.post(reverse("cuenta"), self.datos(tratamiento="lector"))
        self.assertRedirects(r, reverse("cuenta"))
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.get_full_name(), "Ana Pérez")
        self.assertEqual(Perfil.de(self.usuario).tratamiento, "lector")
        self.assertContains(self.client.get(reverse("inicio")), "Lector · @ana")

    def test_solo_lectora_o_lector(self):
        self.assertEqual(Perfil.Tratamiento.values, ["lectora", "lector"])
        self.assertEqual(Perfil.de(self.usuario).get_tratamiento_display(), "Lectora")
        r = self.client.post(reverse("cuenta"), self.datos(tratamiento="neutro"))
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(self.client.get(reverse("cuenta")), "Persona lectora")

    def test_foto_se_recorta_cuadrada_y_reemplaza_la_anterior(self):
        self.client.post(reverse("cuenta"), self.datos(foto=foto()))
        perfil = Perfil.de(self.usuario)
        primera = perfil.foto.path
        with Image.open(primera) as img:
            self.assertEqual(img.size, (400, 400))
        self.assertContains(self.client.get(reverse("inicio")), perfil.foto.url)
        self.client.post(reverse("cuenta"), self.datos(foto=foto((300, 300))))
        perfil.refresh_from_db()
        self.assertFalse(os.path.exists(primera))

    def test_archivo_invalido(self):
        malo = SimpleUploadedFile("x.png", b"no", content_type="image/png")
        r = self.client.post(reverse("cuenta"), self.datos(foto=malo))
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context["perfil_form"].errors.get("foto"))
        self.assertFalse(Perfil.de(self.usuario).foto)

    def test_correo_de_otra_cuenta(self):
        r = self.client.post(reverse("cuenta"), self.datos(email="beto@example.com"))
        self.assertContains(r, "Ya existe otra cuenta con ese correo")

    def test_cambiar_contrasena(self):
        r = self.client.post(reverse("cambiar_clave"), {
            "old_password": "clave-segura-123", "new_password1": "Otra-clave-larga-77", "new_password2": "Otra-clave-larga-77"})
        self.assertRedirects(r, reverse("cuenta"))
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password("Otra-clave-larga-77"))
        self.assertEqual(self.client.get(reverse("inicio")).status_code, 200)  # sigue con la sesión iniciada

    def test_requiere_sesion(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("cuenta")).status_code, 302)


class PersonalizarTextoTests(ConUsuario):
    def test_boton_personalizar_con_texto(self):
        self.assertContains(self.client.get(reverse("biblioteca")), "Personalizar</summary>")
