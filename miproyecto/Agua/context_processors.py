"""
Datos que reciben automáticamente todos los templates.

Se activan en TEMPLATES -> context_processors de settings.py.
"""

# os.path.getmtime entrega la fecha de la última modificación de un archivo.
import os

# finders ubica en disco un archivo estático a partir de su nombre.
from django.contrib.staticfiles import finders

# Nombre de la cookie de consentimiento y sus valores posibles.
from .views import COOKIE_CONSENTIMIENTO, COOKIES_ACEPTADAS, DECISIONES_COOKIES


def version_css(request):
    """
    Versión de la hoja de estilos, para que el navegador no use una copia vieja.

    Los templates enlazan "estilos.css?v=<versión>". La versión es la fecha de la
    última modificación del archivo: cada vez que se edita el CSS cambia la dirección
    y el navegador descarga la versión nueva en vez de usar la que tenía guardada.
    """
    ruta = finders.find("Agua/estilos.css")
    return {"version_css": int(os.path.getmtime(ruta)) if ruta else 0}


def aviso_cookies(request):
    """
    Lee la cookie de consentimiento para decidir qué muestra cada página.

    - mostrar_aviso_cookies: True mientras la persona no haya aceptado ni rechazado
      (base.html y login.html muestran entonces la ventana de cookies).
    - cookies_aceptadas: True solo si aceptó; el dashboard lo usa para explicar
      por qué no aparece la fecha del ingreso anterior.
    """
    # --- Cookie de consentimiento: lectura ---
    decision = request.COOKIES.get(COOKIE_CONSENTIMIENTO)
    return {
        "mostrar_aviso_cookies": decision not in DECISIONES_COOKIES,
        "cookies_aceptadas": decision == COOKIES_ACEPTADAS,
    }
