from datetime import datetime

FORMATO = "%Y%m%d%H%M%S%f"


class IdFechaConverter:
    """Pasa un Id de tipo fecha a la URL como 20 dígitos (año...microsegundos) y viceversa."""

    regex = r"\d{20}"

    def to_python(self, valor):
        return datetime.strptime(valor, FORMATO)

    def to_url(self, valor):
        return valor.strftime(FORMATO)
