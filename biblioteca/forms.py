from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Anotacion, Libro, Prestamo, Resena
from .services.isbn import ISBNInvalido, normalizar


class LibroForm(forms.ModelForm):
    class Meta:
        model = Libro
        fields = [
            "isbn", "titulo", "autores", "editorial", "anio", "paginas",
            "genero", "estado", "portada_url", "descripcion",
        ]
        widgets = {"descripcion": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, propietario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.propietario = propietario
        self.fields["isbn"].widget.attrs.update({"inputmode": "numeric", "placeholder": "978…"})

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

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con ese correo.")
        return email
