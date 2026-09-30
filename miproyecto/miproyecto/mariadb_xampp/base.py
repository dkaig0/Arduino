"""
Backend MySQL de Django adaptado al MariaDB 10.4 que trae XAMPP.

Django 6.1 exige MariaDB 10.11 o superior. Este backend baja ese mínimo y
desactiva lo que MariaDB 10.4 no soporta: INSERT ... RETURNING (llegó en
la 10.5) y el tipo UUID nativo (llegó en la 10.7).
"""

from django.db.backends.mysql import base, features


class DatabaseFeatures(features.DatabaseFeatures):
    minimum_database_version = (10, 4)
    can_return_columns_from_insert = False
    has_native_uuid_field = False


class DatabaseWrapper(base.DatabaseWrapper):
    features_class = DatabaseFeatures
