"""
Rutas principales del proyecto: el primer archivo que Django revisa al llegar una visita.
"""

# include permite derivar las direcciones a las rutas de una aplicación.
from django.urls import include, path

urlpatterns = [
    # Todo el sitio lo atiende la aplicación Agua (ver Agua/urls.py).
    path("", include("Agua.urls")),
]
