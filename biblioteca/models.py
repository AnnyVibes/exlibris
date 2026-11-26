from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from .services.generos import GENEROS


class Libro(models.Model):
    """Un libro de la biblioteca personal de un usuario."""

    class Estado(models.TextChoices):
        POR_LEER = "por_leer", "Por leer"
        LEYENDO = "leyendo", "Leyendo"
        LEIDO = "leido", "Leído"

    propietario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="libros"
    )
    isbn = models.CharField("ISBN", max_length=13, blank=True)
    titulo = models.CharField("título", max_length=255)
    autores = models.CharField(max_length=255, blank=True)
    editorial = models.CharField(max_length=255, blank=True)
    anio = models.PositiveIntegerField("año", null=True, blank=True)
    paginas = models.PositiveIntegerField("páginas", null=True, blank=True)
    portada = models.ImageField("imagen de portada", upload_to="portadas/", blank=True)
    portada_url = models.URLField("enlace de la portada", max_length=500, blank=True)
    descripcion = models.TextField("descripción", blank=True)
    genero = models.CharField("género", max_length=80, blank=True, choices=[(g, g) for g in GENEROS])
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.POR_LEER)
    pagina_actual = models.PositiveIntegerField("página actual", default=0)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-creado"]
        constraints = [
            # Un mismo ISBN no se repite en la biblioteca de un usuario (los libros sin ISBN sí pueden).
            models.UniqueConstraint(
                fields=["propietario", "isbn"],
                condition=~Q(isbn=""),
                name="isbn_unico_por_usuario",
            )
        ]

    def __str__(self):
        return self.titulo

    @property
    def imagen_portada(self):
        """La imagen subida tiene prioridad sobre el enlace del catálogo."""
        if self.portada:
            return self.portada.url
        return self.portada_url

    @property
    def progreso(self):
        """Porcentaje leído (0–100) según la página actual."""
        if not self.paginas:
            return 100 if self.estado == self.Estado.LEIDO else 0
        return min(100, round(self.pagina_actual * 100 / self.paginas))

    @property
    def prestamo_activo(self):
        return self.prestamos.filter(devuelto_el__isnull=True).first()


class Resena(models.Model):
    """Reseña personal del libro (una por libro)."""

    libro = models.OneToOneField(Libro, on_delete=models.CASCADE, related_name="resena")
    calificacion = models.PositiveSmallIntegerField(
        "calificación", validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    texto = models.TextField(blank=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "reseña"

    def __str__(self):
        return f"{self.libro} · {self.calificacion}★"


class Anotacion(models.Model):
    """Idea o nota que se le ocurre al usuario mientras lee."""

    libro = models.ForeignKey(Libro, on_delete=models.CASCADE, related_name="anotaciones")
    pagina = models.PositiveIntegerField("página", null=True, blank=True)
    texto = models.TextField()
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado"]
        verbose_name = "anotación"
        verbose_name_plural = "anotaciones"

    def __str__(self):
        return self.texto[:40]


class Prestamo(models.Model):
    """Registro de a quién se prestó un libro y cuándo volvió."""

    libro = models.ForeignKey(Libro, on_delete=models.CASCADE, related_name="prestamos")
    persona = models.CharField("compartido con", max_length=120)
    contacto = models.CharField(max_length=120, blank=True)
    prestado_el = models.DateField("compartido el", default=timezone.localdate)
    devolver_el = models.DateField("fecha acordada de devolución", null=True, blank=True)
    devuelto_el = models.DateField("fecha de devolución", null=True, blank=True)
    notas = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-prestado_el", "-id"]
        verbose_name = "libro compartido"
        verbose_name_plural = "libros compartidos"
        constraints = [
            # Un libro solo puede tener un préstamo sin devolver a la vez.
            models.UniqueConstraint(
                fields=["libro"],
                condition=Q(devuelto_el__isnull=True),
                name="un_prestamo_activo_por_libro",
            )
        ]

    def __str__(self):
        return f"{self.libro} → {self.persona}"

    @property
    def activo(self):
        return self.devuelto_el is None

    @property
    def vencido(self):
        return self.activo and self.devolver_el is not None and self.devolver_el < timezone.localdate()


class PreferenciaLibrero(models.Model):
    """Cómo quiere ver cada persona su librero (se guarda en la cuenta, no en el navegador)."""

    class Color(models.TextChoices):
        LILA = "lila", "Lila"
        ROSA = "rosa", "Rosa"
        CELESTE = "celeste", "Celeste"
        MENTA = "menta", "Menta"
        MADERA = "madera", "Madera"
        NOCHE = "noche", "Noche"

    class Estilo(models.TextChoices):
        REPISAS = "repisas", "Repisas"
        MUEBLE = "mueble", "Mueble"

    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="preferencia_librero")
    color = models.CharField(max_length=10, choices=Color.choices, default=Color.LILA)
    estilo = models.CharField(max_length=10, choices=Estilo.choices, default=Estilo.MUEBLE)

    class Meta:
        verbose_name = "preferencia del librero"

    def __str__(self):
        return f"{self.usuario} · {self.color} / {self.estilo}"

    @classmethod
    def de(cls, usuario):
        return cls.objects.get_or_create(usuario=usuario)[0]
