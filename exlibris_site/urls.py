from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("biblioteca.urls")),
]

if settings.DEBUG:
    # En desarrollo Django sirve las portadas subidas; en producción las sirve el servidor web.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
