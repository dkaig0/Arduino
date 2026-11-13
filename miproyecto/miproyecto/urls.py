"""
Rutas principales del proyecto: el primer archivo que Django revisa al llegar una visita.
"""

# admin trae las rutas del panel de administración.
from django.contrib import admin

# include permite derivar las direcciones a las rutas de una aplicación.
from django.urls import include, path

urlpatterns = [
    # Panel Django Admin; su configuración está en Agua/admin.py.
    path("admin/", admin.site.urls),
    # El resto del sitio lo atiende la aplicación Agua (ver Agua/urls.py).
    path("", include("Agua.urls")),
]
