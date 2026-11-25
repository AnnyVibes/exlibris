from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme, urlencode
from django.views.decorators.http import require_POST

from .forms import AnotacionForm, LibroForm, PrestamoForm, ProgresoForm, RegistroForm, ResenaForm
from .models import Anotacion, Libro, Prestamo, Resena
from .services import catalogo, estadisticas
from .services.isbn import ISBNInvalido, normalizar
from .services.prestamos import PrestamoError, devolver, prestar


def _libro_del_usuario(request, pk):
    return get_object_or_404(Libro, pk=pk, propietario=request.user)


def registro(request):
    if request.user.is_authenticated:
        return redirect("inicio")
    form = RegistroForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        usuario = form.save()
        login(request, usuario)
        messages.success(request, "¡Tu biblioteca está lista!")
        return redirect("inicio")
    return render(request, "registration/registro.html", {"form": form})


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

    def enlace(**cambios):
        """Querystring que conserva los demás filtros (búsqueda, estado y género se combinan)."""
        params = {"q": q, "estado": estado, "genero": genero, **cambios}
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
    return render(request, "biblioteca/biblioteca.html", {
        "libros": libros, "q": q, "estado": estado, "genero": genero,
        "estados_nav": estados_nav, "generos_nav": generos_nav,
        "sin_genero": base.filter(genero="").count(),
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
        "anotacion_form": AnotacionForm(),
        "prestamo_form": PrestamoForm(),
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
    messages.success(request, f"«{titulo}» se eliminó de tu biblioteca.")
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


@login_required
@require_POST
def anotacion_eliminar(request, pk):
    anotacion = get_object_or_404(Anotacion, pk=pk, libro__propietario=request.user)
    libro_id = anotacion.libro_id
    anotacion.delete()
    messages.success(request, "Anotación eliminada.")
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
            messages.success(request, f"Prestaste «{libro.titulo}» a {form.cleaned_data['persona']}.")
    else:
        messages.error(request, "Revisa los datos del préstamo.")
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
