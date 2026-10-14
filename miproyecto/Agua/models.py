"""
Modelos de la aplicación: la representación en Python de las tablas de la base de datos.

Las tablas ya existen en la base "bd" de MariaDB (se crearon con bd_tinacos.sql),
por eso todos los modelos llevan managed = False: Django las lee y escribe,
pero nunca las crea ni las modifica.
Los Id de Usuario, Tinaco, Medicion y Ubicacion son la fecha y hora
(con microsegundos) en que se creó el registro.
"""

# models trae las herramientas para describir tablas (campos, relaciones, etc.).
from django.db import models

# timezone.now entrega la fecha y hora actual; se usa como valor por defecto de los Id.
from django.utils import timezone

# Límite inferior del rango en que el agua se considera bebible.
PH_MINIMO_BEBIBLE = 6.5
# Límite superior del rango en que el agua se considera bebible.
PH_MAXIMO_BEBIBLE = 8.5

# Nombre exacto del rol que puede crear, editar y eliminar (está en la tabla rol).
ROL_ADMINISTRADOR = "Administrador"


def clasificar_ph(ph):
    """Recibe un valor de pH y devuelve en palabras si el agua se puede beber."""
    # Si el pH es menor que el mínimo, el agua está ácida.
    if ph < PH_MINIMO_BEBIBLE:
        return "No bebible (ácida)"
    # Si es mayor que el máximo, está alcalina.
    elif ph > PH_MAXIMO_BEBIBLE:
        return "No bebible (alcalina)"
    # Si no entró en ningún caso anterior, está dentro del rango permitido.
    else:
        return "Bebible"


class Rol(models.Model):
    """Tabla rol: los perfiles que puede tener una cuenta (Administrador o Usuario)."""

    # Clave primaria numérica que MariaDB va aumentando sola (columna Id_rol).
    id_rol = models.AutoField(primary_key=True, db_column="Id_rol")
    # Nombre del rol, texto de hasta 30 caracteres (columna Rol).
    rol = models.CharField(max_length=30, db_column="Rol")

    class Meta:
        # Django no administra esta tabla: ya existe en la base.
        managed = False
        # Nombre real de la tabla en MariaDB.
        db_table = "rol"

    def __str__(self):
        # Texto que representa al rol cuando se muestra en pantalla.
        return self.rol


class Usuario(models.Model):
    """Tabla usuario: las cuentas que pueden iniciar sesión en el sistema."""

    # Clave primaria: la fecha y hora exacta en que se creó la cuenta.
    id_usuario = models.DateTimeField(primary_key=True, default=timezone.now, db_column="Id_usuario")
    # Nombre con el que la persona inicia sesión.
    nombre_usuario = models.CharField(max_length=20)
    # Correo de la cuenta; unique=True impide que se repita en la tabla.
    email_usuario = models.CharField(max_length=30, unique=True)
    # Contraseña guardada cifrada (nunca en texto plano).
    password_usuario = models.CharField(max_length=255)
    # Relación con la tabla rol: cada usuario tiene un rol.
    # RESTRICT impide borrar un rol que todavía tenga usuarios.
    rol = models.ForeignKey(Rol, on_delete=models.RESTRICT, db_column="Rol_Id_rol")

    class Meta:
        managed = False
        db_table = "usuario"
        # Los usuarios se listan ordenados por fecha de creación.
        ordering = ["id_usuario"]

    def __str__(self):
        # Al mostrar un usuario se ve su nombre.
        return self.nombre_usuario

    def es_admin(self):
        """Devuelve True si la cuenta tiene el rol Administrador."""
        return self.rol.rol == ROL_ADMINISTRADOR


class Tinaco(models.Model):
    """Tabla tinaco: cada estanque de agua que se monitorea."""

    # Clave primaria: fecha y hora en que se registró el tinaco.
    id_tinaco = models.DateTimeField(primary_key=True, default=timezone.now, db_column="Id_Tinaco")
    # Nombre del tinaco. En la base acepta vacío, por eso blank y null.
    nombre_tinaco = models.CharField(max_length=15, blank=True, null=True)
    # Cuántos litros almacena el tinaco.
    capacidad_tinaco = models.IntegerField()
    # Relación con usuario: quién es el responsable del tinaco.
    usuario = models.ForeignKey(
        Usuario,
        # No se puede borrar un usuario que tenga tinacos a su cargo.
        on_delete=models.RESTRICT,
        # Nombre real de la columna en MariaDB.
        db_column="Usuario_Id_usuario",
        # Permite escribir usuario.tinacos para obtener sus tinacos.
        related_name="tinacos",
    )

    class Meta:
        managed = False
        db_table = "tinaco"
        # Se listan del más antiguo al más nuevo.
        ordering = ["id_tinaco"]

    def __str__(self):
        # Si el tinaco no tiene nombre, se muestra su Id para poder identificarlo.
        return self.nombre_tinaco or f"Tinaco {self.id_tinaco}"

    def ultima_medicion(self):
        """Entrega la medición más reciente del tinaco, o None si no tiene ninguna."""
        # mediciones ya viene ordenado de la más nueva a la más antigua.
        return self.mediciones.first()

    def ubicacion(self):
        """Entrega la dirección del tinaco, o None si todavía no tiene."""
        return self.ubicaciones.first()


class Medicion(models.Model):
    """Tabla medicion: cada lectura que envía el sensor de pH del Arduino."""

    # Clave primaria: fecha y hora en que se registró la medición.
    id_medicion = models.DateTimeField(primary_key=True, default=timezone.now, db_column="Id_medicion")
    # Valor de pH medido, con dos decimales (por ejemplo 7.20).
    ph_medicion = models.DecimalField(max_digits=4, decimal_places=2)
    # Litros de agua que tenía el tinaco en ese momento.
    agua_medicion = models.DecimalField(max_digits=10, decimal_places=2)
    # Momento en que se tomó la medición.
    fecha_medicion = models.DateTimeField(default=timezone.now)
    # Relación con tinaco: a qué tinaco pertenece esta medición.
    tinaco = models.ForeignKey(
        Tinaco,
        # Si se borra el tinaco, sus mediciones se borran con él.
        on_delete=models.CASCADE,
        db_column="Tinaco_Id_Tinaco",
        # Permite escribir tinaco.mediciones.
        related_name="mediciones",
    )

    class Meta:
        managed = False
        db_table = "medicion"
        # El signo menos ordena de la más reciente a la más antigua.
        ordering = ["-fecha_medicion"]

    def __str__(self):
        # Texto corto que identifica la medición.
        return f"{self.tinaco} - pH {self.ph_medicion}"

    def estado(self):
        """Dice si esta medición indica agua bebible o no, usando el pH."""
        return clasificar_ph(self.ph_medicion)

    def es_bebible(self):
        """Devuelve True solo cuando el agua está dentro del rango permitido."""
        return self.estado() == "Bebible"

    def posicion_escala(self):
        """Convierte el pH (0 a 14) en un porcentaje, para dibujar la marca en la escala."""
        return int(self.ph_medicion / 14 * 100)

    def porcentaje_llenado(self):
        """Calcula qué porcentaje del tinaco está lleno con el agua medida."""
        # Si la capacidad fuera inválida, dividir daría error o un número absurdo.
        if self.tinaco.capacidad_tinaco <= 0:
            return 0
        return int(self.agua_medicion / self.tinaco.capacidad_tinaco * 100)


class Ubicacion(models.Model):
    """Tabla ubicacion: la dirección física donde está instalado un tinaco."""

    # Clave primaria: fecha y hora en que se registró la dirección.
    id_ubicacion = models.DateTimeField(primary_key=True, default=timezone.now, db_column="Id_ubicacion")
    # Región donde está el tinaco.
    region = models.CharField(max_length=42, db_column="Region")
    # Ciudad de la dirección.
    ciudad = models.CharField(max_length=20, db_column="Ciudad")
    # Comuna de la dirección.
    comuna = models.CharField(max_length=20, db_column="Comuna")
    # Nombre de la calle.
    calle = models.CharField(max_length=50, db_column="Calle")
    # Número de la dirección.
    numero = models.IntegerField(db_column="Numero")
    # Relación con tinaco: de qué tinaco es esta dirección.
    tinaco = models.ForeignKey(
        Tinaco,
        # Si se borra el tinaco, su dirección se borra con él.
        on_delete=models.CASCADE,
        db_column="Tinaco_Id_Tinaco",
        # Permite escribir tinaco.ubicaciones.
        related_name="ubicaciones",
    )

    class Meta:
        managed = False
        db_table = "ubicacion"

    def __str__(self):
        # Dirección resumida, por ejemplo "Av. Los Leones 1250, Providencia".
        return f"{self.calle} {self.numero}, {self.comuna}"
