from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("entrar/", views.EntrarView.as_view(), name="login"),
    path("salir/", auth_views.LogoutView.as_view(), name="logout"),
    path("registro/", views.registro, name="registro"),
    path("cuenta/", views.cuenta, name="cuenta"),
    path("cuenta/contrasena/", views.CambiarClaveView.as_view(), name="cambiar_clave"),
    path("biblioteca/", views.biblioteca, name="biblioteca"),
    path("biblioteca/librero/", views.librero_preferencias, name="librero_preferencias"),
    path("generos/", views.generos, name="generos"),
    path("escanear/", views.escanear, name="escanear"),
    path("libros/nuevo/", views.libro_nuevo, name="libro_nuevo"),
    path("libros/<int:pk>/", views.libro_detalle, name="libro_detalle"),
    path("libros/<int:pk>/editar/", views.libro_editar, name="libro_editar"),
    path("libros/<int:pk>/eliminar/", views.libro_eliminar, name="libro_eliminar"),
    path("libros/<int:pk>/progreso/", views.progreso_actualizar, name="progreso_actualizar"),
    path("libros/<int:pk>/resena/", views.resena_guardar, name="resena_guardar"),
    path("libros/<int:pk>/anotaciones/", views.anotacion_crear, name="anotacion_crear"),
    path("libros/<int:pk>/prestar/", views.prestamo_crear, name="prestamo_crear"),
    path("anotaciones/", views.anotaciones, name="anotaciones"),
    path("anotaciones/<int:pk>/editar/", views.anotacion_editar, name="anotacion_editar"),
    path("anotaciones/<int:pk>/eliminar/", views.anotacion_eliminar, name="anotacion_eliminar"),
    path("prestamos/", views.prestamos, name="prestamos"),
    path("prestamos/<int:pk>/editar/", views.prestamo_editar, name="prestamo_editar"),
    path("prestamos/<int:pk>/devolver/", views.prestamo_devolver, name="prestamo_devolver"),
    path("estadisticas/", views.estadisticas_view, name="estadisticas"),
]
