from django.contrib import admin

from .models import Anotacion, Libro, PreferenciaLibrero, Prestamo, Resena


@admin.register(Libro)
class LibroAdmin(admin.ModelAdmin):
    list_display = ("titulo", "autores", "isbn", "estado", "propietario")
    list_filter = ("estado", "genero")
    search_fields = ("titulo", "autores", "isbn")


admin.site.register(Resena)
admin.site.register(Anotacion)
admin.site.register(Prestamo)
admin.site.register(PreferenciaLibrero)
