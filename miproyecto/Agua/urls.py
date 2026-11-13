"""
Rutas de la aplicación: relaciona cada dirección del sitio con la vista que la atiende.
"""

# path define una ruta; register_converter enseña a Django a leer los Id con forma de fecha.
from django.urls import path, register_converter

# Las vistas que responden a cada dirección.
from . import views

# El convertidor propio, porque los Id de este proyecto son fechas.
from .convertidores import IdFechaConverter

# Se registra con el nombre "idfecha", que es como se usa más abajo en las rutas.
register_converter(IdFechaConverter, "idfecha")

# Lista de rutas. Django las revisa en orden hasta encontrar la que calza.
urlpatterns = [
    # Entrar y salir
    # El name sirve para generar enlaces con {% url 'login' %} en los templates.
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
    # Guarda la decisión de la ventana de cookies (aceptar, rechazar o volver a preguntar).
    path("cookies/", views.guardar_cookies, name="guardar_cookies"),
    # Lectura (los dos roles)
    # La ruta vacía es la página de inicio del sitio.
    path("", views.dashboard, name="dashboard"),
    # <idfecha:tinaco_id> toma los 20 dígitos de la dirección y los convierte en fecha.
    path("tinaco/<idfecha:tinaco_id>/", views.detalle_tinaco, name="detalle_tinaco"),
    # Usuarios (solo administrador)
    path("usuarios/", views.usuarios, name="usuarios"),
    path("usuarios/nuevo/", views.usuario_nuevo, name="usuario_nuevo"),
    path("usuarios/<idfecha:usuario_id>/editar/", views.usuario_editar, name="usuario_editar"),
    path("usuarios/<idfecha:usuario_id>/eliminar/", views.usuario_eliminar, name="usuario_eliminar"),
    # Página para asignarle tinacos a un usuario.
    path("usuarios/<idfecha:usuario_id>/tinacos/", views.usuario_tinacos, name="usuario_tinacos"),
    # Tinacos (solo administrador)
    path("tinacos/nuevo/", views.tinaco_nuevo, name="tinaco_nuevo"),
    path("tinaco/<idfecha:tinaco_id>/editar/", views.tinaco_editar, name="tinaco_editar"),
    path("tinaco/<idfecha:tinaco_id>/eliminar/", views.tinaco_eliminar, name="tinaco_eliminar"),
    # Mediciones (solo administrador)
    # La medición nueva cuelga del tinaco, porque necesita saber a cuál pertenece.
    path("tinaco/<idfecha:tinaco_id>/medicion/nueva/", views.medicion_nueva, name="medicion_nueva"),
    path("medicion/<idfecha:medicion_id>/editar/", views.medicion_editar, name="medicion_editar"),
    path("medicion/<idfecha:medicion_id>/eliminar/", views.medicion_eliminar, name="medicion_eliminar"),
    # Ubicaciones (solo administrador)
    path("tinaco/<idfecha:tinaco_id>/ubicacion/nueva/", views.ubicacion_nueva, name="ubicacion_nueva"),
    path("ubicacion/<idfecha:ubicacion_id>/editar/", views.ubicacion_editar, name="ubicacion_editar"),
    path("ubicacion/<idfecha:ubicacion_id>/eliminar/", views.ubicacion_eliminar, name="ubicacion_eliminar"),
]
