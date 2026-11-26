import json

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme, urlencode
from django.views.decorators.http import require_POST

from .forms import (
    AnotacionForm, CuentaForm, LibroForm, PerfilForm, PreferenciaLibreroForm, PrestamoEditarForm, PrestamoForm, ProgresoForm, RegistroForm,
    ResenaForm,
)
from .models import Anotacion, Libro, Perfil, PreferenciaLibrero, Prestamo, Resena
from .services import catalogo, estadisticas, ia
from .services.isbn import ISBNInvalido, normalizar
from .services.prestamos import PrestamoError, devolver, prestar


def _libro_del_usuario(request, pk):
    return get_object_or_404(Libro, pk=pk, propietario=request.user)


class EntrarView(LoginView):
    """Inicio de sesión. Sin «Recordarme», la sesión termina al cerrar el navegador."""

    redirect_authenticated_user = True

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        if not self.request.POST.get("recordarme"):
            self.request.session.set_expiry(0)
        return respuesta


def registro(request):
    if request.user.is_authenticated:
        return redirect("inicio")
    form = RegistroForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        usuario = form.save()
        login(request, usuario)
        messages.success(request, "¡Tu biblioteca está lista!")
        return redirect("inicio")
    campos = [
        (form["username"], "usuario", "text", "username"),
        (form["email"], "correo", "email", "email"),
        (form["password1"], "candado", "password", "new-password"),
        (form["password2"], "candado", "password", "new-password"),
    ]
    return render(request, "registration/registro.html", {"form": form, "campos": campos})


@login_required
def inicio(request):
    libros = Libro.objects.filter(propietario=request.user)
    resumen = estadisticas.resumen(request.user)
    return render(request, "biblioteca/inicio.html", {
        "resumen": resumen,
        "leyendo": libros.filter(estado=Libro.Estado.LEYENDO).order_by("-actualizado").first(),
        "recientes": libros[:4],
    })


@login_required
def biblioteca(request):
    base = Libro.objects.filter(propietario=request.user)
    q = request.GET.get("q", "").strip()
    estado = request.GET.get("estado", "")
    estado = estado if estado in Libro.Estado.values else ""
    genero = request.GET.get("genero", "").strip()

    libros = base.annotate(n_anotaciones=Count("anotaciones")).select_related("resena")
    if q:
        libros = libros.filter(
            Q(titulo__icontains=q) | Q(autores__icontains=q) | Q(isbn__icontains=q) | Q(genero__icontains=q)
        )
    if estado:
        libros = libros.filter(estado=estado)
    if genero:
        libros = libros.filter(genero__iexact=genero)

    vista_actual = "lista" if request.GET.get("vista") == "lista" else ""

    def enlace(**cambios):
        """Querystring que conserva los demás filtros (búsqueda, estado y género se combinan)."""
        params = {"q": q, "estado": estado, "genero": genero, "vista": vista_actual, **cambios}
        return "?" + urlencode({k: v for k, v in params.items() if v}) if any(params.values()) else "?"

    por_estado = dict(base.values_list("estado").annotate(n=Count("id")))
    estados_nav = [("Todos", base.count(), enlace(estado=""), not estado)] + [
        (etiqueta, por_estado.get(valor, 0), enlace(estado=valor), estado == valor)
        for valor, etiqueta in Libro.Estado.choices
    ]
    generos_nav = [
        (nombre, n, enlace(genero="" if genero.lower() == nombre.lower() else nombre), genero.lower() == nombre.lower())
        for nombre, n in estadisticas.generos(request.user, limite=30)
    ]
    # Vista «librero» (por defecto): estantes por estado de lectura. Vista «lista»: rejilla de tarjetas.
    vista = "lista" if request.GET.get("vista") == "lista" else "librero"
    estantes = [
        ("leyendo", "Leyendo ahora", "planta"),
        ("por_leer", "Por leer", "pila"),
        ("leido", "Leídos", "luna"),
    ]
    MAX_POR_ESTANTE = 10  # después de 10 aparece «Ver los N libros», que abre la lista de esa categoría
    secciones = []
    for valor, titulo, adorno in estantes:
        if estado and estado != valor:
            continue
        del_estante = [l for l in libros if l.estado == valor]
        secciones.append({
            "valor": valor, "titulo": titulo, "adorno": adorno, "total": len(del_estante),
            "libros": del_estante[:MAX_POR_ESTANTE],
            "hay_mas": len(del_estante) > MAX_POR_ESTANTE,
            "url_lista": enlace(estado=valor, vista="lista"),
        })
    preferencia = PreferenciaLibrero.de(request.user)
    return render(request, "biblioteca/biblioteca.html", {
        "libros": libros, "q": q, "estado": estado, "genero": genero,
        "estados_nav": estados_nav, "generos_nav": generos_nav,
        "sin_genero": base.filter(genero="").count(),
        "vista": vista, "secciones": secciones,
        "opciones_estado": [(v, e, por_estado.get(v, 0)) for v, e in Libro.Estado.choices],
        "opciones_genero": estadisticas.generos(request.user, limite=30),
        "enlace_lista": enlace(vista="lista"), "enlace_librero": enlace(vista=""),
        "preferencia": preferencia, "preferencia_form": PreferenciaLibreroForm(instance=preferencia),
    })


@login_required
@require_POST
def librero_preferencias(request):
    form = PreferenciaLibreroForm(request.POST, instance=PreferenciaLibrero.de(request.user))
    if form.is_valid():
        form.save()  # Sin aviso: el cambio de diseño ya se ve en el librero
    else:
        messages.error(request, "Elige un diseño y un color de la lista.")
    siguiente = request.POST.get("siguiente", "")
    if url_has_allowed_host_and_scheme(siguiente, allowed_hosts={request.get_host()}):
        return redirect(siguiente)
    return redirect("biblioteca")


@login_required
def generos(request):
    """Sección «Géneros»: una tarjeta por género con sus libros más recientes."""
    libros = Libro.objects.filter(propietario=request.user).exclude(genero="")
    tarjetas = []
    for nombre, total in estadisticas.generos(request.user, limite=50):
        tarjetas.append({
            "nombre": nombre, "total": total,
            "libros": list(libros.filter(genero=nombre).order_by("-creado")[:5]),
            "leidos": libros.filter(genero=nombre, estado=Libro.Estado.LEIDO).count(),
        })
    return render(request, "biblioteca/generos.html", {
        "tarjetas": tarjetas,
        "sin_genero": Libro.objects.filter(propietario=request.user, genero="").count(),
    })


@login_required
def escanear(request):
    return render(request, "biblioteca/escanear.html")


@login_required
def libro_nuevo(request):
    """Alta de un libro. Con ?isbn= busca sus datos en el catálogo y precarga el formulario."""
    if request.method == "POST":
        form = LibroForm(request.POST, request.FILES, propietario=request.user)
        if form.is_valid():
            libro = form.save(commit=False)
            libro.propietario = request.user
            libro.save()
            messages.success(request, f"«{libro.titulo}» se agregó a tu biblioteca.")
            return redirect("libro_detalle", pk=libro.pk)
        return render(request, "biblioteca/libro_form.html", {"form": form, "nuevo": True})

    inicial, aviso, isbn_buscado = {}, None, request.GET.get("isbn", "").strip()
    if isbn_buscado:
        try:
            isbn = normalizar(isbn_buscado)
        except ISBNInvalido as exc:
            aviso = str(exc)
        else:
            existente = Libro.objects.filter(propietario=request.user, isbn=isbn).first()
            if existente:
                messages.info(request, "Ese libro ya está en tu biblioteca.")
                return redirect("libro_detalle", pk=existente.pk)
            inicial = catalogo.buscar_por_isbn(isbn) or {"isbn": isbn}
            if "titulo" not in inicial:
                aviso = "No encontramos ese ISBN en el catálogo. Completa los datos a mano."
    form = LibroForm(initial=inicial, propietario=request.user)
    return render(request, "biblioteca/libro_form.html", {
        "form": form, "nuevo": True, "aviso": aviso, "isbn_buscado": isbn_buscado,
        "encontrado": bool(inicial.get("titulo")), "portada": inicial.get("portada_url", ""),
    })


@login_required
def libro_detalle(request, pk):
    libro = _libro_del_usuario(request, pk)
    resena = Resena.objects.filter(libro=libro).first()
    return render(request, "biblioteca/libro_detalle.html", {
        "libro": libro,
        "anotaciones": libro.anotaciones.all(),
        "prestamos": libro.prestamos.all(),
        "prestamo_activo": libro.prestamo_activo,
        "progreso_form": ProgresoForm(instance=libro),
        "resena_form": ResenaForm(instance=resena),
        "resena": resena,
        "anotacion_form": AnotacionForm(auto_id="anotacion_%s"),  # ids únicos: la reseña también tiene «texto»
        "prestamo_form": PrestamoForm(auto_id="compartir_%s"),
    })


@login_required
def libro_editar(request, pk):
    libro = _libro_del_usuario(request, pk)
    portada_anterior = libro.portada.name
    form = LibroForm(request.POST or None, request.FILES or None, instance=libro, propietario=request.user)
    if request.method == "POST" and form.is_valid():
        libro = form.save()
        if portada_anterior and portada_anterior != libro.portada.name:
            libro.portada.storage.delete(portada_anterior)  # no dejar imágenes huérfanas
        messages.success(request, "Cambios guardados.")
        return redirect("libro_detalle", pk=libro.pk)
    return render(request, "biblioteca/libro_form.html", {"form": form, "libro": libro, "portada": libro.imagen_portada})


@login_required
@require_POST
def libro_eliminar(request, pk):
    libro = _libro_del_usuario(request, pk)
    titulo = libro.titulo
    if libro.portada:
        libro.portada.delete(save=False)
    libro.delete()
    messages.success(request, f"«{titulo}» se eliminó de tu biblioteca.", extra_tags="eliminado")
    return redirect("biblioteca")


@login_required
@require_POST
def progreso_actualizar(request, pk):
    libro = _libro_del_usuario(request, pk)
    form = ProgresoForm(request.POST, instance=libro)
    if form.is_valid():
        libro = form.save(commit=False)
        if libro.estado == Libro.Estado.LEIDO and libro.paginas:
            libro.pagina_actual = libro.paginas
        libro.save()
        messages.success(request, "Progreso actualizado.")
    else:
        messages.error(request, " ".join(e for errs in form.errors.values() for e in errs))
    return redirect("libro_detalle", pk=libro.pk)


@login_required
@require_POST
def resena_guardar(request, pk):
    libro = _libro_del_usuario(request, pk)
    form = ResenaForm(request.POST, instance=Resena.objects.filter(libro=libro).first())
    if form.is_valid():
        resena = form.save(commit=False)
        resena.libro = libro
        resena.save()
        messages.success(request, "Reseña guardada.")
    else:
        messages.error(request, "Elige una calificación de 1 a 5 estrellas.")
    return redirect("libro_detalle", pk=libro.pk)


@login_required
@require_POST
def anotacion_crear(request, pk):
    libro = _libro_del_usuario(request, pk)
    form = AnotacionForm(request.POST)
    if form.is_valid():
        anotacion = form.save(commit=False)
        anotacion.libro = libro
        anotacion.save()
        messages.success(request, f"Anotación guardada. Llevas {libro.anotaciones.count()} en este libro.")
    else:
        messages.error(request, "La anotación no puede estar vacía.")
    return redirect("libro_detalle", pk=libro.pk)


def _siguiente(request, por_defecto):
    """URL de retorno segura (solo del mismo sitio)."""
    siguiente = request.POST.get("siguiente") or request.GET.get("siguiente") or ""
    if url_has_allowed_host_and_scheme(siguiente, allowed_hosts={request.get_host()}):
        return siguiente
    return por_defecto


@login_required
def anotacion_editar(request, pk):
    anotacion = get_object_or_404(Anotacion, pk=pk, libro__propietario=request.user)
    volver = _siguiente(request, reverse("libro_detalle", args=[anotacion.libro_id]))
    form = AnotacionForm(request.POST or None, instance=anotacion)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "La anotación se actualizó.")
        return redirect(volver)
    return render(request, "biblioteca/anotacion_editar.html", {"form": form, "anotacion": anotacion, "volver": volver})


@login_required
def prestamo_editar(request, pk):
    prestamo = get_object_or_404(Prestamo, pk=pk, libro__propietario=request.user)
    volver = _siguiente(request, reverse("prestamos"))
    form = PrestamoEditarForm(request.POST or None, instance=prestamo)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Se actualizaron los datos de «{prestamo.libro.titulo}».")
        return redirect(volver)
    return render(request, "biblioteca/prestamo_editar.html", {"form": form, "prestamo": prestamo, "volver": volver})


@login_required
@require_POST
def anotacion_eliminar(request, pk):
    anotacion = get_object_or_404(Anotacion, pk=pk, libro__propietario=request.user)
    libro_id = anotacion.libro_id
    anotacion.delete()
    messages.success(request, "La anotación se eliminó.", extra_tags="eliminado")
    return redirect("libro_detalle", pk=libro_id)


@login_required
def anotaciones(request):
    q = request.GET.get("q", "").strip()
    lista = Anotacion.objects.filter(libro__propietario=request.user).select_related("libro")
    if q:
        lista = lista.filter(Q(texto__icontains=q) | Q(libro__titulo__icontains=q))
    return render(request, "biblioteca/anotaciones.html", {
        "anotaciones": lista, "q": q,
        "por_libro": estadisticas.mas_anotados(request.user, limite=10),
    })


@login_required
@require_POST
def prestamo_crear(request, pk):
    libro = _libro_del_usuario(request, pk)
    form = PrestamoForm(request.POST)
    if form.is_valid():
        try:
            prestar(libro, **form.cleaned_data)
        except PrestamoError as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, f"Compartiste «{libro.titulo}» con {form.cleaned_data['persona']}.")
    else:
        messages.error(request, "Revisa los datos para compartir el libro.")
    return redirect("libro_detalle", pk=libro.pk)


@login_required
@require_POST
def prestamo_devolver(request, pk):
    prestamo = get_object_or_404(Prestamo, pk=pk, libro__propietario=request.user)
    try:
        devolver(prestamo)
    except PrestamoError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, f"«{prestamo.libro.titulo}» volvió a casa.")
    siguiente = request.POST.get("siguiente", "")
    if url_has_allowed_host_and_scheme(siguiente, allowed_hosts={request.get_host()}):
        return redirect(siguiente)
    return redirect("prestamos")


@login_required
def prestamos(request):
    todos = Prestamo.objects.filter(libro__propietario=request.user).select_related("libro")
    return render(request, "biblioteca/prestamos.html", {
        "activos": todos.filter(devuelto_el__isnull=True).order_by("devolver_el", "prestado_el"),
        "historial": todos.filter(devuelto_el__isnull=False)[:30],
    })


@login_required
def estadisticas_view(request):
    resumen = estadisticas.resumen(request.user)
    generos = estadisticas.generos(request.user, limite=8)
    return render(request, "biblioteca/estadisticas.html", {
        "resumen": resumen,
        "mas_anotados": estadisticas.mas_anotados(request.user),
        "grafico_estados": {
            "labels": list(resumen["por_estado"].keys()), "data": list(resumen["por_estado"].values()),
        },
        "grafico_generos": {"labels": [g for g, _ in generos], "data": [n for _, n in generos]},
    })


@login_required
def cuenta(request):
    perfil = Perfil.de(request.user)
    foto_anterior = perfil.foto.name
    datos = request.POST if request.method == "POST" else None
    cuenta_form = CuentaForm(datos, instance=request.user)
    perfil_form = PerfilForm(datos, request.FILES or None, instance=perfil)
    if request.method == "POST" and cuenta_form.is_valid() and perfil_form.is_valid():
        cuenta_form.save()
        perfil = perfil_form.save()
        if foto_anterior and foto_anterior != perfil.foto.name:
            perfil.foto.storage.delete(foto_anterior)
        messages.success(request, "Tus datos se actualizaron.")
        return redirect("cuenta")
    return render(request, "biblioteca/cuenta.html", {
        "cuenta_form": cuenta_form, "perfil_form": perfil_form, "perfil": perfil,
        "resumen": estadisticas.resumen(request.user),
    })


class CambiarClaveView(PasswordChangeView):
    template_name = "biblioteca/cambiar_clave.html"

    def get_success_url(self):
        return reverse("cuenta")

    def form_valid(self, form):
        messages.success(self.request, "Tu contraseña se cambió.")
        return super().form_valid(form)


# ------------------------------------------------------------------ IA (fase 2)
def _json(request):
    try:
        datos = json.loads(request.body or b"{}")
    except ValueError:
        return None
    return datos if isinstance(datos, dict) else None


def _error_ia(exc, estado=503):
    return JsonResponse({"error": str(exc)}, status=estado)


@login_required
@require_POST
def ia_clasificar(request):
    datos = _json(request)
    if datos is None or not str(datos.get("titulo", "")).strip():
        return JsonResponse({"error": "Escribe al menos el título del libro."}, status=400)
    try:
        resultado = ia.clasificar(datos["titulo"].strip(), str(datos.get("autores", "")), str(datos.get("descripcion", "")))
    except ia.IANoDisponible as exc:
        return _error_ia(exc)
    return JsonResponse(resultado)


@login_required
@require_POST
def ia_resena(request, pk):
    libro = _libro_del_usuario(request, pk)
    datos = _json(request) or {}
    try:
        calificacion = int(datos.get("calificacion") or 0) or None
    except (TypeError, ValueError):
        calificacion = None
    try:
        texto = ia.borrador_resena(libro, calificacion)
    except ia.IANoDisponible as exc:
        return _error_ia(exc)
    return JsonResponse({"texto": texto})


@login_required
@require_POST
def ia_resumir(request, pk):
    libro = _libro_del_usuario(request, pk)
    try:
        libro.resumen_ia = ia.resumir(libro)
    except ValueError as exc:
        messages.error(request, str(exc))
    except ia.IANoDisponible as exc:
        messages.error(request, str(exc))
    else:
        libro.resumen_ia_fecha = timezone.now()
        libro.save(update_fields=["resumen_ia", "resumen_ia_fecha"])
        messages.success(request, "La IA resumió tus anotaciones.")
    return redirect(f"{reverse('libro_detalle', args=[libro.pk])}#resumen-ia")


@login_required
def asistente(request):
    return render(request, "biblioteca/asistente.html", {
        "sugerencias": [
            "¿Qué libros tengo compartidos y con quién?",
            "¿Cuáles estoy leyendo y cuánto me falta?",
            "Recomiéndame qué leer después según lo que ya leí.",
            "¿Qué anoté sobre el tiempo o la memoria?",
        ],
    })


@login_required
@require_POST
def ia_agente(request):
    datos = _json(request)
    mensaje = str((datos or {}).get("mensaje", "")).strip()
    if not mensaje:
        return JsonResponse({"error": "Escribe una pregunta."}, status=400)
    sesion = str((datos or {}).get("sesion", ""))[:40] or "web"
    try:
        respuesta = ia.preguntar(request.user, mensaje, sesion)
    except ia.IANoDisponible as exc:
        return _error_ia(exc)
    return JsonResponse({"respuesta": respuesta})
