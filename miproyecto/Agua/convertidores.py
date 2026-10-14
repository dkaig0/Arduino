"""
Convertidor de Id para las direcciones del sitio.

En este proyecto las claves primarias son fechas con hora y microsegundos.
Una fecha no se puede escribir tal cual en una dirección web (lleva espacios y
dos puntos), así que se convierte en 20 dígitos seguidos y viceversa.
Ejemplo: 01-08-2026 09:15:00 se escribe como 20260801091500000000.
"""

# datetime permite pasar de texto a fecha y de fecha a texto.
from datetime import datetime

# Orden de los dígitos: año, mes, día, hora, minuto, segundo y microsegundos.
FORMATO = "%Y%m%d%H%M%S%f"


class IdFechaConverter:
    """Pasa un Id de tipo fecha a la URL como 20 dígitos (año...microsegundos) y viceversa."""

    # Django solo acepta la dirección si coincide con esto: exactamente 20 dígitos.
    regex = r"\d{20}"

    def to_python(self, valor):
        """De los 20 dígitos de la dirección a una fecha que entiende Python."""
        # Si el texto no es una fecha válida, Django responde 404.
        return datetime.strptime(valor, FORMATO)

    def to_url(self, valor):
        """De una fecha a los 20 dígitos, al generar enlaces en los templates."""
        return valor.strftime(FORMATO)
