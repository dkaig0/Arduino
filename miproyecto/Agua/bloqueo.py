"""
Bloqueo temporal de cuentas por intentos fallidos de inicio de sesión.

Protege contra ataques de fuerza bruta (probar contraseñas una tras otra):
después de INTENTOS_PERMITIDOS intentos fallidos seguidos, la cuenta queda
bloqueada SEGUNDOS_BLOQUEO segundos, aunque luego se escriba la contraseña correcta.

Los contadores se guardan en el caché de Django (memoria del servidor, ver
CACHES en settings.py), que borra solo cada dato cuando vence su tiempo.
Lo usan backends.py (aplica el bloqueo, también en el login de Django Admin)
y forms.py (muestra los mensajes).
"""

# hashlib convierte un texto en un código fijo (hash), para usarlo como nombre en el caché.
import hashlib

# math.ceil redondea hacia arriba (59.2 segundos se muestran como 60).
import math

# time.time entrega la hora actual en segundos.
import time

# cache es el caché de Django: guarda datos con un tiempo de vida.
from django.core.cache import cache

# Q permite buscar por nombre O por correo.
from django.db.models import Q

# Intentos fallidos seguidos que se toleran antes de bloquear la cuenta.
INTENTOS_PERMITIDOS = 3
# Duración del bloqueo: 1 minuto.
SEGUNDOS_BLOQUEO = 60
# Si pasan 15 minutos sin nuevos fallos, el contador de intentos vuelve a cero.
SEGUNDOS_MEMORIA_INTENTOS = 15 * 60


def _cuenta(identificador):
    """
    Identifica la cuenta a la que se refiere lo escrito en el login.

    Si existe, se usa su Id: así el nombre y el correo comparten el mismo contador.
    Si no existe, se usa el texto escrito, para que la respuesta sea igual que con
    una cuenta real (un atacante no puede averiguar qué cuentas existen).
    """
    # Se importa aquí porque models.py no debe depender de este archivo.
    from .models import Usuario

    usuario = (
        Usuario.objects.filter(Q(nombre_usuario=identificador) | Q(email_usuario=identificador))
        .only("pk")
        .first()
    )
    texto = usuario.pk.isoformat() if usuario else identificador.strip().lower()
    # El hash evita guardar en el caché el texto tal como lo escribieron.
    return hashlib.sha256(texto.encode()).hexdigest()


def segundos_restantes(identificador):
    """Devuelve cuántos segundos le quedan de bloqueo a la cuenta, o 0 si no está bloqueada."""
    # En el caché se guarda la hora exacta en que termina el bloqueo.
    desbloqueo = cache.get("bloqueo:" + _cuenta(identificador))
    if desbloqueo is None:
        return 0
    return max(0, math.ceil(desbloqueo - time.time()))


def intentos_restantes(identificador):
    """Cuántos intentos fallidos más se toleran antes del bloqueo."""
    return INTENTOS_PERMITIDOS - cache.get("intentos:" + _cuenta(identificador), 0)


def registrar_fallo(identificador):
    """Suma un intento fallido; al llegar al máximo, bloquea la cuenta."""
    cuenta = _cuenta(identificador)
    intentos = cache.get("intentos:" + cuenta, 0) + 1
    if intentos >= INTENTOS_PERMITIDOS:
        # Se guarda cuándo termina el bloqueo; el caché lo borra solo al vencer.
        cache.set("bloqueo:" + cuenta, time.time() + SEGUNDOS_BLOQUEO, timeout=SEGUNDOS_BLOQUEO)
        # El contador vuelve a cero: al terminar el bloqueo hay 3 intentos nuevos.
        cache.delete("intentos:" + cuenta)
    else:
        cache.set("intentos:" + cuenta, intentos, timeout=SEGUNDOS_MEMORIA_INTENTOS)


def limpiar(identificador):
    """Ingreso correcto: se olvidan los intentos fallidos anteriores."""
    cuenta = _cuenta(identificador)
    cache.delete_many(["intentos:" + cuenta, "bloqueo:" + cuenta])
