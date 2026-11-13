"""
Backend de autenticación del proyecto.

authenticate() de Django recorre los backends de AUTHENTICATION_BACKENDS
(settings.py) para comprobar usuario y contraseña. Este backend hereda del
que trae Django (ModelBackend) y agrega dos cosas:
- Aceptar el nombre de usuario O el correo en el campo de ingreso.
- Bloquear la cuenta 1 minuto tras 3 intentos fallidos (ver bloqueo.py).
Como Django Admin también usa authenticate(), el bloqueo rige en los dos logins.
"""

# ModelBackend es el backend estándar de Django: busca la cuenta y revisa la contraseña.
from django.contrib.auth.backends import ModelBackend

# PermissionDenied le indica a authenticate() que rechace el ingreso sin seguir revisando.
from django.core.exceptions import PermissionDenied

# Q permite buscar por una condición O por otra (nombre O correo).
from django.db.models import Q

# Contadores de intentos fallidos y bloqueo temporal.
from . import bloqueo

# El modelo de usuario del proyecto.
from .models import Usuario


class NombreOCorreoBackend(ModelBackend):
    """Permite iniciar sesión con el nombre o el correo, con bloqueo por intentos fallidos."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        """Devuelve la cuenta si los datos son correctos, o None si no lo son."""
        # Si falta alguno de los dos datos no hay nada que revisar.
        if username is None or password is None:
            return None

        # Si la cuenta está bloqueada, ni siquiera se revisa la contraseña:
        # mientras dure el bloqueo, tampoco la contraseña correcta permite entrar.
        if bloqueo.segundos_restantes(username):
            raise PermissionDenied

        # Se busca una cuenta cuyo nombre O cuyo correo coincida con lo escrito.
        # select_related trae el rol en la misma consulta.
        # Protección contra inyección SQL: filter() arma una consulta parametrizada,
        # es decir, envía el SQL y el texto escrito por separado. Aunque alguien
        # escriba "' OR '1'='1", MariaDB lo compara como un nombre más.
        usuario = (
            Usuario.objects.select_related("rol")
            .filter(Q(nombre_usuario=username) | Q(email_usuario=username))
            .first()
        )

        if usuario is None:
            # Aunque la cuenta no exista, se calcula un hash igual: así la respuesta
            # tarda lo mismo y un atacante no puede adivinar qué cuentas existen
            # midiendo el tiempo (Django hace lo mismo en ModelBackend).
            Usuario().set_password(password)
            # También se cuenta el intento, para responder igual que con una cuenta real.
            bloqueo.registrar_fallo(username)
            return None

        # check_password compara lo escrito con el hash guardado;
        # user_can_authenticate rechaza cuentas desactivadas.
        if usuario.check_password(password) and self.user_can_authenticate(usuario):
            # Ingreso correcto: se borran los intentos fallidos acumulados.
            bloqueo.limpiar(username)
            return usuario

        # Contraseña incorrecta: se suma un intento (al tercero, la cuenta se bloquea).
        bloqueo.registrar_fallo(username)
        return None

    def get_user(self, user_id):
        """
        En cada visita, Django usa el Id guardado en la sesión para recuperar la cuenta.

        Se reescribe solo para traer también el rol en la misma consulta,
        porque casi todas las páginas lo consultan.
        """
        usuario = Usuario.objects.select_related("rol").filter(pk=user_id).first()
        if usuario is not None and self.user_can_authenticate(usuario):
            return usuario
        return None
