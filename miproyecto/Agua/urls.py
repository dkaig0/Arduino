from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),#Ruta / donde se muestra dashboard
    path("tinaco/<int:tinaco_id>/", views.detalle_tinaco, name="detalle_tinaco"), #ruta tinaco /id y muestra detalle del tinaco con el id proporcionado
    path("login/", views.login, name="login"),#ruta login/ donde se muestra el formulario de inicio de sesión
    path("logout/", views.logout, name="logout"),#ruta logout/ donde se cierra la sesión y se redirige al login
]
