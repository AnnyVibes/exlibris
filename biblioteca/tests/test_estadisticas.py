from biblioteca.models import Anotacion, Resena
from biblioteca.services import estadisticas
from biblioteca.services.prestamos import prestar

from .base import ConUsuario


class EstadisticasTests(ConUsuario):
    def test_resumen(self):
        a = self.libro(estado="leido", paginas=300, genero="novela")
        b = self.libro(titulo="Ficciones", estado="leyendo", paginas=200, genero="Novela")
        self.libro(titulo="Ajeno", propietario=self.otro, estado="leido")
        Resena.objects.create(libro=a, calificacion=4)
        Resena.objects.create(libro=b, calificacion=5)
        Anotacion.objects.create(libro=a, texto="x")
        prestar(b, "Lucía")
        r = estadisticas.resumen(self.usuario)
        self.assertEqual(r["total"], 2)
        self.assertEqual(r["leidos"], 1)
        self.assertEqual(r["paginas_leidas"], 300)
        self.assertEqual(r["anotaciones"], 1)
        self.assertEqual(r["prestados"], 1)
        self.assertEqual(r["calificacion_media"], 4.5)
        self.assertEqual(estadisticas.generos(self.usuario), [("Novela", 2)])
