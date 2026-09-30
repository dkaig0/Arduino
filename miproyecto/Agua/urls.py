from django.urls import path, register_converter

from . import views
from .convertidores import IdFechaConverter

register_converter(IdFechaConverter, "idfecha")

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("tinaco/<idfecha:tinaco_id>/", views.detalle_tinaco, name="detalle_tinaco"),
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
]
