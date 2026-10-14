#!/usr/bin/env python
"""
Herramienta de línea de comandos de Django.

Con este archivo se ejecutan las órdenes del proyecto, por ejemplo:
    python manage.py runserver     -> levanta el servidor de pruebas
    python manage.py makemigrations -> crea las migraciones
    python manage.py migrate        -> las aplica en la base de datos
"""
# os permite leer y escribir variables de entorno.
import os
# sys da acceso a los argumentos escritos en la terminal y a las rutas de búsqueda.
import sys
# Path maneja rutas de carpetas.
from pathlib import Path


# Carpeta que contiene a este archivo, subiendo un nivel.
BASE_DIR = Path(__file__).resolve().parent.parent
# Se agrega esa carpeta a las rutas de búsqueda para que Python encuentre el proyecto.
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


def main():
    """Ejecuta la orden que se escribió en la terminal."""
    # Le indica a Django cuál es el archivo de configuración del proyecto.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'miproyecto.settings')
    try:
        # Función de Django que interpreta y ejecuta la orden.
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # Si Django no está instalado, se explica el problema en vez de fallar sin aviso.
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    # sys.argv trae lo escrito después de "python manage.py".
    execute_from_command_line(sys.argv)


# Esto solo se ejecuta cuando el archivo se corre directamente, no al importarlo.
if __name__ == '__main__':
    main()
