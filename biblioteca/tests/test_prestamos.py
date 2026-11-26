from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from biblioteca.models import Prestamo
from biblioteca.services.prestamos import PrestamoError, devolver, prestar

from .base import ConUsuario


class PrestamoServicioTests(ConUsuario):
    def test_no_se_presta_dos_veces(self):
        libro = self.libro()
        prestar(libro, "Lucía")
        with self.assertRaises(PrestamoError):
            prestar(libro, "Pedro")

    def test_tras_devolver_se_puede_prestar_otra_vez(self):
        libro = self.libro()
        devolver(prestar(libro, "Lucía"))
        prestar(libro, "Pedro")
        self.assertEqual(libro.prestamos.count(), 2)
        self.assertEqual(libro.prestamo_activo.persona, "Pedro")

    def test_fecha_de_devolucion_pasada(self):
        with self.assertRaises(PrestamoError):
            prestar(self.libro(), "Lucía", devolver_el=timezone.localdate() - timedelta(days=1))

    def test_persona_obligatoria(self):
        with self.assertRaises(PrestamoError):
            prestar(self.libro(), "   ")

    def test_vencido(self):
        p = prestar(self.libro(), "Lucía", devolver_el=timezone.localdate())
        self.assertFalse(p.vencido)
        Prestamo.objects.filter(pk=p.pk).update(devolver_el=timezone.localdate() - timedelta(days=3))
        p.refresh_from_db()
        self.assertTrue(p.vencido)


class PrestamoVistasTests(ConUsuario):
    def test_prestar_y_devolver_desde_la_web(self):
        libro = self.libro()
        self.client.post(reverse("prestamo_crear", args=[libro.pk]), {"persona": "Lucía", "contacto": "6000-0000"})
        r = self.client.get(reverse("prestamos"))
        self.assertContains(r, "Lucía")
        self.assertContains(self.client.get(reverse("inicio")), "Lucía")  # panel lateral
        p = libro.prestamo_activo
        r = self.client.post(reverse("prestamo_devolver", args=[p.pk]), {"siguiente": f"/libros/{libro.pk}/"})
        self.assertRedirects(r, f"/libros/{libro.pk}/")
        p.refresh_from_db()
        self.assertEqual(p.devuelto_el, timezone.localdate())

    def test_redireccion_externa_ignorada(self):
        p = prestar(self.libro(), "Lucía")
        r = self.client.post(reverse("prestamo_devolver", args=[p.pk]), {"siguiente": "https://malicioso.example"})
        self.assertRedirects(r, reverse("prestamos"))

    def test_segundo_prestamo_muestra_error(self):
        libro = self.libro()
        prestar(libro, "Lucía")
        r = self.client.post(reverse("prestamo_crear", args=[libro.pk]), {"persona": "Pedro"}, follow=True)
        self.assertContains(r, "ya está compartido")
        self.assertEqual(libro.prestamos.count(), 1)

    def test_no_devuelve_prestamo_ajeno(self):
        from biblioteca.models import Libro
        p = prestar(Libro.objects.create(propietario=self.otro, titulo="Ajeno"), "X")
        self.assertEqual(self.client.post(reverse("prestamo_devolver", args=[p.pk])).status_code, 404)


class ConteoDiasTests(ConUsuario):
    def test_dias_compartido_y_plazo(self):
        hoy = timezone.localdate()
        p = prestar(self.libro(), "Lucía", devolver_el=hoy + timedelta(days=5))
        Prestamo.objects.filter(pk=p.pk).update(prestado_el=hoy - timedelta(days=3))
        p.refresh_from_db()
        self.assertEqual((p.dias, p.dias_para_devolver), (3, 5))
        r = self.client.get(reverse("prestamos"))
        self.assertContains(r, "Faltan 5 días")
        self.assertContains(r, "¿Ya lo devolvió?")
        self.assertContains(r, "Sí, devuelto")

    def test_vencido_y_hoy(self):
        hoy = timezone.localdate()
        p = prestar(self.libro(), "Lucía", devolver_el=hoy)
        self.assertContains(self.client.get(reverse("prestamos")), "Vence hoy")
        Prestamo.objects.filter(pk=p.pk).update(devolver_el=hoy - timedelta(days=2))
        self.assertContains(self.client.get(reverse("prestamos")), "Vencido hace 2 días")

    def test_duracion_en_historial(self):
        hoy = timezone.localdate()
        p = prestar(self.libro(), "Lucía")
        Prestamo.objects.filter(pk=p.pk).update(prestado_el=hoy - timedelta(days=7))
        p.refresh_from_db(); devolver(p); p.refresh_from_db()
        self.assertEqual(p.dias, 7)
        self.assertIsNone(p.dias_para_devolver)
        self.assertContains(self.client.get(reverse("prestamos")), "7 días")
