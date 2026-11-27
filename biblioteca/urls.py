from django.contrib.auth import views as auth_views
from django.urls import path

from . import api_ia, views

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
    path("libros/<int:pk>/completar/", views.libro_completar, name="libro_completar"),
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
    # IA (fase 2)
    path("asistente/", views.asistente, name="asistente"),
    path("ia/agente/", views.ia_agente, name="ia_agente"),
    path("ia/clasificar/", views.ia_clasificar, name="ia_clasificar"),
    path("ia/libros/<int:pk>/resumir/", views.ia_resumir, name="ia_resumir"),
    path("ia/libros/<int:pk>/resena/", views.ia_resena, name="ia_resena"),
    # API para las herramientas del agente (token firmado)
    path("api/ia/libros/", api_ia.libros, name="api_ia_libros"),
    path("api/ia/libros/<int:pk>/", api_ia.libro, name="api_ia_libro"),
    path("api/ia/libros/agregar/", api_ia.agregar_libro, name="api_ia_agregar"),
    path("api/ia/compartidos/", api_ia.compartidos, name="api_ia_compartidos"),
    path("api/ia/anotaciones/", api_ia.anotaciones, name="api_ia_anotaciones"),
    path("api/ia/resumen/", api_ia.resumen, name="api_ia_resumen"),
]
