import json
from pathlib import Path

from django.core.management.base import BaseCommand

from Agua.models import Tinaco

ARCHIVO_DATOS = Path(__file__).resolve().parent.parent.parent / "datos.json"


class Command(BaseCommand):
    help = "Carga los tinacos de ejemplo definidos en datos.json."

    def handle(self, *args, **options):
        with open(ARCHIVO_DATOS, encoding="utf-8") as archivo:
            datos = json.load(archivo)

        Tinaco.objects.all().delete()

        for fila in datos["tinacos"]:
            tinaco = Tinaco.objects.create(
                id=fila["id"],
                nombre=fila["nombre"],
                ubicacion=fila["ubicacion"],
                capacidad_litros=fila["capacidad_litros"],
                ph_actual=fila["ph_actual"],
            )
            self.stdout.write(f"Creado {tinaco.nombre} (pH {tinaco.ph_actual} - {tinaco.estado()})")

        self.stdout.write(self.style.SUCCESS("Datos de ejemplo cargados."))
