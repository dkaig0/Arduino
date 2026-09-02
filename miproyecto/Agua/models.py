from django.db import models

PH_MINIMO_BEBIBLE = 6.5#pH minimo
PH_MAXIMO_BEBIBLE = 8.5#pH maximo


def clasificar_ph(ph):#Función para clasifiar ph
    if ph < PH_MINIMO_BEBIBLE:
        return "No bebible (ácida)"
    elif ph > PH_MAXIMO_BEBIBLE:
        return "No bebible (alcalina)"
    else:
        return "Bebible"


#Clase Tinaco
class Tinaco(models.Model):
    nombre = models.CharField(max_length=80)#Nombre del tinaco
    ubicacion = models.CharField(max_length=120)#jUbicación del tinaco
    capacidad_litros = models.IntegerField(default=1100)#capacidad del tinaco en litros
    ph_actual = models.FloatField(default=7.0)#pH actual del tinaco
    fecha_medicion = models.DateTimeField(auto_now=True)#Fecha de la última medición del pH del tinaco

    def __str__(self):#Constructor de la clase Tinaco, devuelve el nombre del tinaco
        return self.nombre

    def estado(self):#Devuelve el estado del tinaco según su pH actual, utilizando la función clasificar_ph para determinar si el agua es bebible o no.
        return clasificar_ph(self.ph_actual)

    def es_bebible(self):#Comprueba si el tinaco es bebible, devolviendo True si el estado del tinaco es "Bebible" y False en caso contrario.
        return self.estado() == "Bebible"

    def posicion_escala(self):#Devuelve la posición del tinaco en la escala de pH, calculando el porcentaje del pH actual respecto al rango total de pH (0 a 14) y devolviendo un valor entero entre 0 y 100.
        return int(self.ph_actual / 14 * 100)
