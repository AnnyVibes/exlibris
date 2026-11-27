from io import BytesIO

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image, ImageOps, UnidentifiedImageError
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Anotacion, Libro, Perfil, PreferenciaLibrero, Prestamo, Resena
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
        ejemplos = {
            "isbn": "Ej.: 978-84-376-0494-7",
            "titulo": "Ej.: Cien años de soledad",
            "autores": "Ej.: Gabriel García Márquez",
            "editorial": "Ej.: Penguin Random House",
            "anio": "Ej.: 1967",
            "paginas": "Ej.: 417",
            "portada_url": "Ej.: https://…/portada.jpg",
            "descripcion": "De qué trata el libro (opcional)",
        }
        for campo, texto in ejemplos.items():
            self.fields[campo].widget.attrs["placeholder"] = texto
        self.fields["isbn"].widget.attrs["inputmode"] = "numeric"
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
        widgets = {"estado": forms.RadioSelect}

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
        widgets = {"texto": forms.Textarea(attrs={"rows": 4, "placeholder": "¿Qué te pareció el libro?"})}


class AnotacionForm(forms.ModelForm):
    class Meta:
        model = Anotacion
        fields = ["pagina", "texto"]
        widgets = {
            "texto": forms.Textarea(attrs={"rows": 3, "placeholder": "Una idea, una cita, algo que se te ocurrió…"}),
            "pagina": forms.NumberInput(attrs={"placeholder": "Ej.: 45"}),
        }


class PrestamoForm(forms.ModelForm):
    class Meta:
        model = Prestamo
        fields = ["persona", "contacto", "devolver_el", "notas"]
        widgets = {
            "devolver_el": forms.DateInput(attrs={"type": "date"}),
            "persona": forms.TextInput(attrs={"placeholder": "Ej.: Lucía"}),
            "contacto": forms.TextInput(attrs={"placeholder": "Ej.: 6000-1234 o correo (opcional)"}),
            "notas": forms.TextInput(attrs={"placeholder": "Ej.: me lo devuelve en clase (opcional)"}),
        }


class PrestamoEditarForm(forms.ModelForm):
    """Editar un libro compartido: también permite corregir la fecha en que se compartió."""

    class Meta:
        model = Prestamo
        fields = ["persona", "contacto", "prestado_el", "devolver_el", "notas"]
        widgets = {
            "prestado_el": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "devolver_el": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "persona": forms.TextInput(attrs={"placeholder": "Ej.: Lucía"}),
            "contacto": forms.TextInput(attrs={"placeholder": "Ej.: 6000-1234 o correo (opcional)"}),
            "notas": forms.TextInput(attrs={"placeholder": "Ej.: me lo devuelve en clase (opcional)"}),
        }

    def clean(self):
        datos = super().clean()
        desde, hasta = datos.get("prestado_el"), datos.get("devolver_el")
        from django.utils import timezone
        if desde and desde > timezone.localdate():
            self.add_error("prestado_el", "La fecha en que lo compartiste no puede ser futura.")
        if desde and hasta and hasta < desde:
            self.add_error("devolver_el", "La devolución no puede ser antes de la fecha en que lo compartiste.")
        if self.instance.devuelto_el and desde and desde > self.instance.devuelto_el:
            self.add_error("prestado_el", "No puede ser después de la fecha en que te lo devolvieron.")
        return datos


class RegistroForm(UserCreationForm):
    email = forms.EmailField(label="Correo")
    tratamiento = forms.ChoiceField(
        label="¿Cómo prefieres que te llamemos?", choices=Perfil.Tratamiento.choices,
        initial=Perfil.Tratamiento.LECTORA, widget=forms.RadioSelect,
    )

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


FOTO_LADO = 400  # px: la foto de perfil se recorta cuadrada


class CuentaForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        labels = {"first_name": "Nombre", "last_name": "Apellido", "email": "Correo"}
        widgets = {
            "first_name": forms.TextInput(attrs={"placeholder": "Ej.: Anllelina", "autocomplete": "given-name"}),
            "last_name": forms.TextInput(attrs={"placeholder": "Ej.: Varcasia", "autocomplete": "family-name"}),
            "email": forms.EmailInput(attrs={"placeholder": "Ej.: nombre@correo.com", "autocomplete": "email"}),
        }

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").lower()
        if email and User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Ya existe otra cuenta con ese correo.")
        return email


class PerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ["foto", "tratamiento"]
        widgets = {
            "foto": forms.ClearableFileInput(attrs={"accept": "image/jpeg,image/png,image/webp"}),
            "tratamiento": forms.RadioSelect,
        }

    def clean_foto(self):
        archivo = self.cleaned_data.get("foto")
        if not archivo or archivo is False or not hasattr(archivo, "content_type"):
            return archivo
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
        imagen = ImageOps.exif_transpose(imagen).convert("RGB")
        imagen = ImageOps.fit(imagen, (FOTO_LADO, FOTO_LADO))  # recorte cuadrado centrado
        salida = BytesIO()
        imagen.save(salida, format="JPEG", quality=88)
        nombre = archivo.name.rsplit(".", 1)[0] + ".jpg"
        return InMemoryUploadedFile(salida, "foto", nombre, "image/jpeg", salida.tell(), None)
