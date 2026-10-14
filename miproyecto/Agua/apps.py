"""Configuración de la aplicación Agua dentro del proyecto."""

# AppConfig es la clase base con la que Django describe cada aplicación.
from django.apps import AppConfig


class AguaConfig(AppConfig):
    """Datos básicos de la aplicación."""

    # Nombre de la carpeta de la aplicación, tal como aparece en INSTALLED_APPS.
    name = 'Agua'
