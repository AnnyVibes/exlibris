"""API JSON de solo lectura para las herramientas del agente de IA (n8n).

Cada petición debe traer el token firmado que Django envía al agente en cada pregunta
(cabecera «X-ExLibris-Token» o parámetro «token»). El token identifica a la persona y caduca,
así el agente solo puede ver la biblioteca de quien pregunta.
"""

from functools import wraps

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import Anotacion, Libro, Prestamo
from .services import estadisticas
from .services import ia
from .services.ia import usuario_de_token

LIMITE = 25


def con_token(vista, metodo="GET"):
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        token = request.headers.get("X-ExLibris-Token") or request.GET.get("token", "")
        uid = usuario_de_token(token) if token else None
        usuario = get_user_model().objects.filter(pk=uid, is_active=True).first() if uid else None
        if usuario is None:
            return JsonResponse({"error": "Token inválido o caducado."}, status=401)
        request.usuario_ia = usuario
        return vista(request, *args, **kwargs)
    if metodo == "POST":
        # Autenticación por token firmado (no por cookie de sesión): no aplica CSRF.
        return csrf_exempt(require_POST(envoltura))
    return require_GET(envoltura)


def _libro(l):
    prestamo = next((p for p in l.prestamos.all() if p.devuelto_el is None), None)
    resena = getattr(l, "resena", None)
    return {
        "id": l.pk, "titulo": l.titulo, "autores": l.autores, "genero": l.genero,
        "estado": l.get_estado_display(), "paginas": l.paginas, "pagina_actual": l.pagina_actual,
        "progreso": l.progreso, "calificacion": resena.calificacion if resena else None,
        "anotaciones": getattr(l, "n_anotaciones", None),
        "compartido_con": prestamo.persona if prestamo else None,
    }


def _prestamo(p):
    return {
        "libro": p.libro.titulo, "libro_id": p.libro_id, "persona": p.persona, "contacto": p.contacto,
        "compartido_el": p.prestado_el, "devolver_el": p.devolver_el, "devuelto_el": p.devuelto_el,
        "dias": p.dias, "vencido": p.vencido,
    }


@con_token
def libros(request):
    """Busca libros. Filtros: q (título, autor, ISBN), estado (por_leer, leyendo, leido), genero."""
    qs = (Libro.objects.filter(propietario=request.usuario_ia)
          .select_related("resena").prefetch_related("prestamos")
          .annotate(n_anotaciones=Count("anotaciones")))
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(Q(titulo__icontains=q) | Q(autores__icontains=q) | Q(isbn__icontains=q))
    if request.GET.get("estado") in Libro.Estado.values:
        qs = qs.filter(estado=request.GET["estado"])
    if request.GET.get("genero"):
        qs = qs.filter(genero__iexact=request.GET["genero"].strip())
    total = qs.count()
    return JsonResponse({"total": total, "mostrando": min(total, LIMITE), "libros": [_libro(l) for l in qs[:LIMITE]]},
                        json_dumps_params={"ensure_ascii": False})


@con_token
def libro(request, pk):
    l = (Libro.objects.filter(propietario=request.usuario_ia, pk=pk)
         .select_related("resena").prefetch_related("prestamos", "anotaciones")
         .annotate(n_anotaciones=Count("anotaciones")).first())
    if l is None:
        return JsonResponse({"error": "No existe ese libro en la biblioteca."}, status=404)
    datos = _libro(l)
    datos.update({
        "descripcion": l.descripcion[:1500], "isbn": l.isbn, "editorial": l.editorial, "anio": l.anio,
        "resena": getattr(getattr(l, "resena", None), "texto", ""),
        "notas": [{"pagina": n.pagina, "texto": n.texto} for n in l.anotaciones.all()[:40]],
        "historial_compartido": [_prestamo(p) for p in l.prestamos.all()],
        "resumen_ia": l.resumen_ia,
    })
    return JsonResponse(datos, json_dumps_params={"ensure_ascii": False})


@con_token
def compartidos(request):
    """Libros compartidos ahora (y el historial si «todos=1»)."""
    qs = Prestamo.objects.filter(libro__propietario=request.usuario_ia).select_related("libro")
    if request.GET.get("todos") != "1":
        qs = qs.filter(devuelto_el__isnull=True)
    return JsonResponse({"compartidos": [_prestamo(p) for p in qs[:50]]}, json_dumps_params={"ensure_ascii": False})


@con_token
def anotaciones(request):
    """Busca en las anotaciones por texto (q)."""
    qs = Anotacion.objects.filter(libro__propietario=request.usuario_ia).select_related("libro")
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(Q(texto__icontains=q) | Q(libro__titulo__icontains=q))
    return JsonResponse({"anotaciones": [
        {"libro": n.libro.titulo, "libro_id": n.libro_id, "pagina": n.pagina, "texto": n.texto, "fecha": n.creado}
        for n in qs[:30]
    ]}, json_dumps_params={"ensure_ascii": False})


@con_token
def resumen(request):
    """Totales de la biblioteca y géneros."""
    datos = estadisticas.resumen(request.usuario_ia)
    datos["generos"] = dict(estadisticas.generos(request.usuario_ia, limite=30))
    return JsonResponse(datos, json_dumps_params={"ensure_ascii": False})


def agregar_libro(request):
    """Única acción de escritura del agente: agrega un libro (título, autores e ISBN opcional)."""
    import json
    try:
        datos = json.loads(request.body or b"{}")
    except ValueError:
        datos = None
    if not isinstance(datos, dict):
        datos = request.POST.dict()
    try:
        resultado = ia.agregar_libro(request.usuario_ia, str(datos.get("titulo", "")),
                                     str(datos.get("autores", "")), str(datos.get("isbn", "")))
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse(resultado, status=201 if resultado["creado"] else 200, json_dumps_params={"ensure_ascii": False})


agregar_libro = con_token(agregar_libro, metodo="POST")
