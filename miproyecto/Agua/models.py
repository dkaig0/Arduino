from django.db import models
from django.utils import timezone

PH_MINIMO_BEBIBLE = 6.5
PH_MAXIMO_BEBIBLE = 8.5


def clasificar_ph(ph):
    if ph < PH_MINIMO_BEBIBLE:
        return "No bebible (ácida)"
    elif ph > PH_MAXIMO_BEBIBLE:
        return "No bebible (alcalina)"
    else:
        return "Bebible"


# Las tablas ya existen en la base "bd" (creadas con bd_tinacos.sql),
# por eso managed = False: Django las usa, pero no las crea ni las modifica.
# Los Id de Usuario, Tinaco, Medicion y Ubicacion son la fecha y hora
# (con microsegundos) en que se creó el registro.


class Rol(models.Model):
    id_rol = models.AutoField(primary_key=True, db_column="Id_rol")
    rol = models.CharField(max_length=30, db_column="Rol")

    class Meta:
        managed = False
        db_table = "rol"

    def __str__(self):
        return self.rol


class Usuario(models.Model):
    id_usuario = models.DateTimeField(primary_key=True, default=timezone.now, db_column="Id_usuario")
    nombre_usuario = models.CharField(max_length=20)
    email_usuario = models.CharField(max_length=30, unique=True)
    password_usuario = models.CharField(max_length=255)
    rol = models.ForeignKey(Rol, on_delete=models.RESTRICT, db_column="Rol_Id_rol")

    class Meta:
        managed = False
        db_table = "usuario"

    def __str__(self):
        return self.nombre_usuario


class Tinaco(models.Model):
    id_tinaco = models.DateTimeField(primary_key=True, default=timezone.now, db_column="Id_Tinaco")
    nombre_tinaco = models.CharField(max_length=15, blank=True, null=True)
    capacidad_tinaco = models.IntegerField()
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.RESTRICT,
        db_column="Usuario_Id_usuario",
        related_name="tinacos",
    )

    class Meta:
        managed = False
        db_table = "tinaco"
        ordering = ["id_tinaco"]

    def __str__(self):
        return self.nombre_tinaco or f"Tinaco {self.id_tinaco}"

    def ultima_medicion(self):
        return self.mediciones.first()

    def ubicacion(self):
        return self.ubicaciones.first()


class Medicion(models.Model):
    id_medicion = models.DateTimeField(primary_key=True, default=timezone.now, db_column="Id_medicion")
    ph_medicion = models.DecimalField(max_digits=4, decimal_places=2)
    agua_medicion = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_medicion = models.DateTimeField(default=timezone.now)
    tinaco = models.ForeignKey(
        Tinaco,
        on_delete=models.CASCADE,
        db_column="Tinaco_Id_Tinaco",
        related_name="mediciones",
    )

    class Meta:
        managed = False
        db_table = "medicion"
        ordering = ["-fecha_medicion"]

    def __str__(self):
        return f"{self.tinaco} - pH {self.ph_medicion}"

    def estado(self):
        return clasificar_ph(self.ph_medicion)

    def es_bebible(self):
        return self.estado() == "Bebible"

    def posicion_escala(self):
        return int(self.ph_medicion / 14 * 100)

    def porcentaje_llenado(self):
        return int(self.agua_medicion / self.tinaco.capacidad_tinaco * 100)


class Ubicacion(models.Model):
    id_ubicacion = models.DateTimeField(primary_key=True, default=timezone.now, db_column="Id_ubicacion")
    region = models.CharField(max_length=42, db_column="Region")
    ciudad = models.CharField(max_length=20, db_column="Ciudad")
    comuna = models.CharField(max_length=20, db_column="Comuna")
    calle = models.CharField(max_length=50, db_column="Calle")
    numero = models.IntegerField(db_column="Numero")
    tinaco = models.ForeignKey(
        Tinaco,
        on_delete=models.CASCADE,
        db_column="Tinaco_Id_Tinaco",
        related_name="ubicaciones",
    )

    class Meta:
        managed = False
        db_table = "ubicacion"

    def __str__(self):
        return f"{self.calle} {self.numero}, {self.comuna}"
