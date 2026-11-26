from .models import Anotacion, Perfil
from .services.estadisticas import prestamos_activos


def panel_lateral(request):
    """Datos del panel derecho (préstamos y última anotación) en todas las páginas."""
    if not request.user.is_authenticated:
        return {}
    return {
        "perfil_usuario": Perfil.de(request.user),
        "panel_prestamos": prestamos_activos(request.user)[:4],
        "panel_anotacion": Anotacion.objects.filter(libro__propietario=request.user)
        .select_related("libro").first(),
    }
