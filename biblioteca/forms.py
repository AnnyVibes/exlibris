from io import BytesIO

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image, UnidentifiedImageError
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Anotacion, Libro, PreferenciaLibrero, Prestamo, Resena
from .services.isbn import ISBNInvalido, normalizar


FORMATOS_PORTADA = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}
PORTADA_MAX_LADO = 900  # px: suficiente para verse nítida y no llenar el disco


def _preparar_portada(archivo):
    """Valida que sea una imagen JPG/PNG/WEBP y la reduce a un tamaño razonable."""
    limite = getattr(settings, "PORTADA_MAX_MB", 5)
    if archivo.size > limite * 1024 * 1024:
        raise forms.ValidationError(f"La imagen pesa más de {limite} MB. Elige una más liviana.")
    try:
        imagen = Image.open(archivo)
        imagen.load()
    except (UnidentifiedImageError, OSError):
        raise forms.ValidationError("Ese archivo no es una imagen válida.")
    if imagen.format not in FORMATOS_PORTADA:
        raise forms.ValidationError("Usa una imagen JPG, PNG o WEBP.")
    if max(imagen.size) <= PORTADA_MAX_LADO:
        archivo.seek(0)
        return archivo
    formato = imagen.format
    imagen.thumbnail((PORTADA_MAX_LADO, PORTADA_MAX_LADO))
    salida = BytesIO()
    if formato == "JPEG" and imagen.mode not in ("RGB", "L"):
        imagen = imagen.convert("RGB")
    imagen.save(salida, format=formato, quality=88)
    return InMemoryUploadedFile(
        salida, "portada", archivo.name, FORMATOS_PORTADA[formato], salida.tell(), None
    )


class LibroForm(forms.ModelForm):
    class Meta:
        model = Libro
        fields = [
            "isbn", "titulo", "autores", "editorial", "anio", "paginas",
            "genero", "estado", "portada", "portada_url", "descripcion",
        ]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 4}),
            "portada": forms.ClearableFileInput(attrs={"accept": "image/jpeg,image/png,image/webp"}),
        }
        help_texts = {
            "portada": "JPG, PNG o WEBP, hasta 5 MB. Si subes una imagen, se usa en lugar del enlace.",
            "portada_url": "Opcional: el enlace de una imagen en internet.",
        }

    def __init__(self, *args, propietario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.propietario = propietario
        self.fields["isbn"].widget.attrs.update({"inputmode": "numeric", "placeholder": "978…"})
        self.fields["titulo"].widget.attrs.update({"placeholder": "Título del libro"})
        self.fields["autores"].widget.attrs.update({"placeholder": "Autor o autores"})
        self.fields["portada_url"].widget.attrs.update({"placeholder": "https://…"})
        self.fields["genero"].choices = [("", "Elige un género…")] + list(self.fields["genero"].choices)[1:]

    def clean_portada(self):
        archivo = self.cleaned_data.get("portada")
        # Sin archivo nuevo: se conserva la portada actual (o se quita si marcó «Borrar»).
        if not archivo or archivo is False or not hasattr(archivo, "content_type"):
            return archivo
        return _preparar_portada(archivo)

    def clean_isbn(self):
        valor = self.cleaned_data.get("isbn", "")
        if not valor:
            return ""
        try:
            isbn = normalizar(valor)
        except ISBNInvalido as exc:
            raise forms.ValidationError(str(exc))
        repetidos = Libro.objects.filter(propietario=self.propietario, isbn=isbn)
        if self.instance.pk:
            repetidos = repetidos.exclude(pk=self.instance.pk)
        if repetidos.exists():
            raise forms.ValidationError("Ya tienes este libro en tu biblioteca.")
        return isbn


class ProgresoForm(forms.ModelForm):
    class Meta:
        model = Libro
        fields = ["estado", "pagina_actual"]

    def clean(self):
        datos = super().clean()
        pagina = datos.get("pagina_actual") or 0
        if self.instance.paginas and pagina > self.instance.paginas:
            self.add_error("pagina_actual", f"El libro tiene {self.instance.paginas} páginas.")
        return datos


class ResenaForm(forms.ModelForm):
    calificacion = forms.TypedChoiceField(
        label="Calificación", coerce=int,
        choices=[(i, "★" * i) for i in range(5, 0, -1)],
        widget=forms.RadioSelect,
    )

    class Meta:
        model = Resena
        fields = ["calificacion", "texto"]
        widgets = {"texto": forms.Textarea(attrs={"rows": 4, "placeholder": "¿Qué te pareció?"})}


class AnotacionForm(forms.ModelForm):
    class Meta:
        model = Anotacion
        fields = ["pagina", "texto"]
        widgets = {
            "texto": forms.Textarea(attrs={"rows": 3, "placeholder": "Una idea, una cita, algo que se te ocurrió…"}),
            "pagina": forms.NumberInput(attrs={"placeholder": "Pág."}),
        }


class PrestamoForm(forms.ModelForm):
    class Meta:
        model = Prestamo
        fields = ["persona", "contacto", "devolver_el", "notas"]
        widgets = {
            "devolver_el": forms.DateInput(attrs={"type": "date"}),
            "persona": forms.TextInput(attrs={"placeholder": "¿A quién?"}),
            "contacto": forms.TextInput(attrs={"placeholder": "Teléfono o correo (opcional)"}),
        }


class RegistroForm(UserCreationForm):
    email = forms.EmailField(label="Correo")

    class Meta:
        model = User
        fields = ["username", "email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Nombre de usuario"
        self.fields["password1"].label = "Contraseña"
        self.fields["password2"].label = "Repite la contraseña"

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con ese correo.")
        return email


class PreferenciaLibreroForm(forms.ModelForm):
    class Meta:
        model = PreferenciaLibrero
        fields = ["estilo", "color"]
        widgets = {"estilo": forms.RadioSelect, "color": forms.RadioSelect}
