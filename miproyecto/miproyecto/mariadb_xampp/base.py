"""
Backend MySQL de Django adaptado al MariaDB 10.4 que trae XAMPP.

Django 6.1 exige MariaDB 10.11 o superior. Este backend baja ese mínimo y
desactiva lo que MariaDB 10.4 no soporta: INSERT ... RETURNING (llegó en
la 10.5) y el tipo UUID nativo (llegó en la 10.7).
Se usa desde settings.py con ENGINE = 'miproyecto.mariadb_xampp'.
"""

# base trae la conexión original de Django para MySQL y MariaDB.
# features es la lista de cosas que el motor de base de datos sabe hacer.
from django.db.backends.mysql import base, features


class DatabaseFeatures(features.DatabaseFeatures):
    """Copia de las capacidades estándar, corrigiendo tres puntos."""

    # Versión mínima aceptada: la 10.4 de XAMPP en vez de la 10.11.
    minimum_database_version = (10, 4)
    # MariaDB 10.4 no sabe devolver los datos recién insertados (INSERT ... RETURNING).
    can_return_columns_from_insert = False
    # El tipo UUID nativo recién aparece en MariaDB 10.7.
    has_native_uuid_field = False


class DatabaseWrapper(base.DatabaseWrapper):
    """La conexión de siempre, pero usando las capacidades corregidas de arriba."""

    features_class = DatabaseFeatures
