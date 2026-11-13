"""
Modelos de la aplicación: la representación en Python de las tablas de la base de datos.

Las tablas ya existen en la base "bd" de MariaDB (se crearon con bd_tinacos.sql),
por eso todos los modelos llevan managed = False: Django las lee y escribe,
pero nunca las crea ni las modifica.
Los Id de Usuario, Tinaco, Medicion y Ubicacion son la fecha y hora
(con microsegundos) en que se creó el registro.

El modelo Usuario es además el modelo de usuario del sistema de autenticación
de Django (AUTH_USER_MODEL en settings.py): con él funcionan login(), logout(),
@login_required, @permission_required y el panel Django Admin.
"""

# AbstractBaseUser es la base que Django ofrece para crear un modelo de usuario propio.
# BaseUserManager trae utilidades para crear cuentas (por ejemplo, normalizar el correo).
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager

# ValidationError es el error que se lanza cuando un dato no cumple una regla.
from django.core.exceptions import ValidationError

# Validadores que revisan que un número no sea menor o mayor que un límite.
from django.core.validators import MaxValueValidator, MinValueValidator

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
# Nombre exacto del rol de solo lectura (el otro registro de la tabla rol).
ROL_USUARIO = "Usuario"

# Permisos de Django que tiene el rol Usuario. El Administrador los tiene todos.
# Django crea cuatro permisos por modelo: add_, change_, delete_ y view_ (solo ver).
# Se escriben "aplicación.permiso_modelo", por ejemplo "Agua.view_tinaco".
PERMISOS_ROL_USUARIO = {
    "Agua.view_tinaco",
    "Agua.view_medicion",
    "Agua.view_ubicacion",
}


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
    rol = models.CharField("rol", max_length=30, db_column="Rol")

    class Meta:
        # Django no administra esta tabla: ya existe en la base.
        managed = False
        # Nombre real de la tabla en MariaDB.
        db_table = "rol"
        # Nombres que muestra Django Admin, en singular y plural.
        verbose_name = "rol"
        verbose_name_plural = "roles"

    def __str__(self):
        # Texto que representa al rol cuando se muestra en pantalla.
        return self.rol


class UsuarioManager(BaseUserManager):
    """
    Crea cuentas con la contraseña cifrada.

    Lo usa "python manage.py createsuperuser" y queda disponible como Usuario.objects.
    """

    def create_user(self, nombre_usuario, email_usuario, password=None, rol=None):
        """Crea una cuenta; si no se indica rol, queda como Usuario (solo lectura)."""
        # Sin nombre no se podría iniciar sesión.
        if not nombre_usuario:
            raise ValueError("La cuenta necesita un nombre de usuario.")
        # Si no dijeron qué rol, se usa el de solo lectura.
        if rol is None:
            rol = Rol.objects.get(rol=ROL_USUARIO)
        # self.model es la clase Usuario; se arma la cuenta en memoria.
        usuario = self.model(
            nombre_usuario=nombre_usuario,
            # normalize_email deja el dominio del correo en minúsculas.
            email_usuario=self.normalize_email(email_usuario),
            rol=rol,
        )
        # set_password guarda el hash de la contraseña, nunca el texto plano.
        usuario.set_password(password)
        # Recién aquí se escribe la fila en la base.
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, nombre_usuario, email_usuario, password=None):
        """La llama "manage.py createsuperuser": crea la cuenta con rol Administrador."""
        rol = Rol.objects.get(rol=ROL_ADMINISTRADOR)
        return self.create_user(nombre_usuario, email_usuario, password, rol=rol)


class Usuario(AbstractBaseUser):
    """
    Tabla usuario: las cuentas que pueden iniciar sesión en el sistema.

    Al heredar de AbstractBaseUser obtiene set_password, check_password,
    is_authenticated y todo lo que necesita el sistema de autenticación de Django.
    """

    # Clave primaria: la fecha y hora exacta en que se creó la cuenta.
    # editable=False: se genera sola, ningún formulario la pide.
    id_usuario = models.DateTimeField(
        "registrado",
        primary_key=True,
        default=timezone.now,
        editable=False,
        db_column="Id_usuario",
    )
    # Nombre con el que la persona inicia sesión.
    # unique=True: no puede haber dos cuentas con el mismo nombre (Django lo exige
    # para el campo de inicio de sesión, y la tabla tiene la restricción Usuario_nombre_UK).
    nombre_usuario = models.CharField("nombre de usuario", max_length=20, unique=True)
    # Correo de la cuenta; unique=True impide que se repita en la tabla.
    email_usuario = models.CharField("correo electrónico", max_length=30, unique=True)
    # AbstractBaseUser ya trae un campo "password"; se redefine para que use la
    # columna password_usuario de la tabla y admita hashes de hasta 255 caracteres.
    password = models.CharField("contraseña", max_length=255, db_column="password_usuario")
    # Relación con la tabla rol: cada usuario tiene un rol.
    # RESTRICT impide borrar un rol que todavía tenga usuarios.
    rol = models.ForeignKey(Rol, on_delete=models.RESTRICT, db_column="Rol_Id_rol", verbose_name="rol")

    # AbstractBaseUser también trae el campo last_login (último ingreso).
    # La tabla no tiene esa columna, así que se quita asignándole None.
    last_login = None

    # Campo con el que se inicia sesión: lo usan authenticate() y Django Admin.
    USERNAME_FIELD = "nombre_usuario"
    # Campo que Django debe tratar como el correo de la cuenta.
    EMAIL_FIELD = "email_usuario"
    # Datos extra que pide "manage.py createsuperuser" además del nombre y la contraseña.
    REQUIRED_FIELDS = ["email_usuario"]

    # Usuario.objects usará el manager de arriba, que sabe crear cuentas.
    objects = UsuarioManager()

    class Meta:
        managed = False
        db_table = "usuario"
        # Los usuarios se listan ordenados por fecha de creación.
        ordering = ["id_usuario"]
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    def __str__(self):
        # Al mostrar un usuario se ve su nombre.
        return self.nombre_usuario

    def es_admin(self):
        """Devuelve True si la cuenta tiene el rol Administrador."""
        return self.rol.rol == ROL_ADMINISTRADOR

    @property
    def is_staff(self):
        """Django Admin solo deja entrar si is_staff es True: aquí, al rol Administrador."""
        return self.es_admin()

    def has_perm(self, perm, obj=None):
        """
        Responde si la cuenta tiene un permiso, por ejemplo "Agua.add_tinaco".

        Lo consultan @permission_required en las vistas, {{ perms }} en los
        templates y Django Admin. Los permisos salen del rol de la cuenta.
        """
        # Una cuenta desactivada no tiene ningún permiso.
        if not self.is_active:
            return False
        # El Administrador puede hacer todo.
        if self.es_admin():
            return True
        # El rol Usuario solo tiene los permisos de lectura de la lista de arriba.
        return perm in PERMISOS_ROL_USUARIO

    def has_perms(self, perm_list, obj=None):
        """Igual que has_perm, pero exige tener todos los permisos de una lista."""
        return all(self.has_perm(perm, obj) for perm in perm_list)

    def has_module_perms(self, app_label):
        """Django pregunta esto para saber si la cuenta tiene algún permiso en una aplicación."""
        if not self.is_active:
            return False
        if self.es_admin():
            return True
        # Basta con que alguno de sus permisos empiece con el nombre de la aplicación.
        return any(perm.startswith(app_label + ".") for perm in PERMISOS_ROL_USUARIO)


class Tinaco(models.Model):
    """Tabla tinaco: cada estanque de agua que se monitorea."""

    # Clave primaria: fecha y hora en que se registró el tinaco.
    id_tinaco = models.DateTimeField(
        "registrado",
        primary_key=True,
        default=timezone.now,
        editable=False,
        db_column="Id_Tinaco",
    )
    # Nombre del tinaco. En la base acepta vacío, por eso blank y null.
    nombre_tinaco = models.CharField("nombre", max_length=15, blank=True, null=True)
    # Cuántos litros almacena el tinaco; el validador impide 0 o negativos.
    capacidad_tinaco = models.IntegerField(
        "capacidad (litros)",
        validators=[MinValueValidator(1, "La capacidad debe ser mayor que cero.")],
    )
    # Relación con usuario: quién es el responsable del tinaco.
    usuario = models.ForeignKey(
        Usuario,
        # No se puede borrar un usuario que tenga tinacos a su cargo.
        on_delete=models.RESTRICT,
        # Nombre real de la columna en MariaDB.
        db_column="Usuario_Id_usuario",
        # Permite escribir usuario.tinacos para obtener sus tinacos.
        related_name="tinacos",
        verbose_name="usuario responsable",
    )

    class Meta:
        managed = False
        db_table = "tinaco"
        # Se listan del más antiguo al más nuevo.
        ordering = ["id_tinaco"]
        verbose_name = "tinaco"
        verbose_name_plural = "tinacos"

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
    id_medicion = models.DateTimeField(
        "registrada",
        primary_key=True,
        default=timezone.now,
        editable=False,
        db_column="Id_medicion",
    )
    # Valor de pH medido, con dos decimales (por ejemplo 7.20). La escala va de 0 a 14.
    ph_medicion = models.DecimalField(
        "pH",
        max_digits=4,
        decimal_places=2,
        validators=[
            MinValueValidator(0, "El pH debe estar entre 0 y 14."),
            MaxValueValidator(14, "El pH debe estar entre 0 y 14."),
        ],
    )
    # Litros de agua que tenía el tinaco en ese momento; no pueden ser negativos.
    agua_medicion = models.DecimalField(
        "agua (litros)",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0, "El agua medida no puede ser negativa.")],
    )
    # Momento en que se tomó la medición.
    fecha_medicion = models.DateTimeField("fecha de medición", default=timezone.now)
    # Relación con tinaco: a qué tinaco pertenece esta medición.
    tinaco = models.ForeignKey(
        Tinaco,
        # Si se borra el tinaco, sus mediciones se borran con él.
        on_delete=models.CASCADE,
        db_column="Tinaco_Id_Tinaco",
        # Permite escribir tinaco.mediciones.
        related_name="mediciones",
        verbose_name="tinaco",
    )

    class Meta:
        managed = False
        db_table = "medicion"
        # El signo menos ordena de la más reciente a la más antigua.
        ordering = ["-fecha_medicion"]
        verbose_name = "medición"
        verbose_name_plural = "mediciones"

    def __str__(self):
        # Texto corto que identifica la medición.
        return f"{self.tinaco} - pH {self.ph_medicion}"

    def clean(self):
        """
        Regla que involucra dos tablas: no puede haber más agua que la capacidad del tinaco.

        Django la ejecuta al validar cualquier formulario de este modelo,
        incluidos los de Django Admin.
        """
        super().clean()
        # Solo se puede comparar si ya se sabe el tinaco y se escribió el agua.
        if self.tinaco_id is not None and self.agua_medicion is not None:
            capacidad = self.tinaco.capacidad_tinaco
            if self.agua_medicion > capacidad:
                # El diccionario asocia el error al campo agua_medicion.
                raise ValidationError(
                    {"agua_medicion": f"El tinaco solo almacena {capacidad} litros."}
                )

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
    id_ubicacion = models.DateTimeField(
        "registrada",
        primary_key=True,
        default=timezone.now,
        editable=False,
        db_column="Id_ubicacion",
    )
    # Región donde está el tinaco.
    region = models.CharField("región", max_length=42, db_column="Region")
    # Ciudad de la dirección.
    ciudad = models.CharField("ciudad", max_length=20, db_column="Ciudad")
    # Comuna de la dirección.
    comuna = models.CharField("comuna", max_length=20, db_column="Comuna")
    # Nombre de la calle.
    calle = models.CharField("calle", max_length=50, db_column="Calle")
    # Número de la dirección; debe ser positivo.
    numero = models.IntegerField(
        "número",
        db_column="Numero",
        validators=[MinValueValidator(1, "El número de la dirección debe ser mayor que cero.")],
    )
    # Relación con tinaco: de qué tinaco es esta dirección.
    tinaco = models.ForeignKey(
        Tinaco,
        # Si se borra el tinaco, su dirección se borra con él.
        on_delete=models.CASCADE,
        db_column="Tinaco_Id_Tinaco",
        # Permite escribir tinaco.ubicaciones.
        related_name="ubicaciones",
        verbose_name="tinaco",
    )

    class Meta:
        managed = False
        db_table = "ubicacion"
        verbose_name = "ubicación"
        verbose_name_plural = "ubicaciones"

    def __str__(self):
        # Dirección resumida, por ejemplo "Av. Los Leones 1250, Providencia".
        return f"{self.calle} {self.numero}, {self.comuna}"
