"""
Configuración del panel Django Admin (dirección /admin/).

Cada clase ModelAdmin define cómo se ve y se administra una tabla:
- list_display: columnas de la lista.
- search_fields: campos donde busca la caja de búsqueda.
- list_filter: filtros de la barra lateral derecha.
- inlines: tablas relacionadas que se editan dentro del mismo formulario.

Solo entran las cuentas con is_staff = True, es decir, las de rol Administrador
(ver Usuario.is_staff en models.py).
"""

# admin trae el panel y las clases para configurarlo.
from django.contrib import admin

# UserAdmin es la configuración que Django usa para administrar usuarios:
# agrega la página para cambiar contraseñas y los formularios que las cifran.
from django.contrib.auth.admin import UserAdmin

# Formularios de Django para crear usuarios (con contraseña y confirmación)
# y para editarlos (muestra el hash, nunca la contraseña).
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

# Group es el modelo de grupos de Django; aquí no se usa (los roles están en la tabla rol).
from django.contrib.auth.models import Group

# Count cuenta registros relacionados (por ejemplo, cuántos tinacos tiene un usuario).
from django.db.models import Count

# Login del panel con los mensajes del bloqueo por intentos fallidos.
from .forms import IngresoAdminForm

# Los modelos del proyecto y los límites del rango bebible.
from .models import (
    PH_MAXIMO_BEBIBLE,
    PH_MINIMO_BEBIBLE,
    Medicion,
    Rol,
    Tinaco,
    Ubicacion,
    Usuario,
)

# ---------------------------------------------------------------
# Textos del panel
# ---------------------------------------------------------------

# Título grande de la parte superior.
admin.site.site_header = "AquaVida · Administración"
# Texto de la pestaña del navegador.
admin.site.site_title = "AquaVida Admin"
# Título de la página de inicio del panel.
admin.site.index_title = "Gestión del monitoreo de agua (ODS 6)"
# Formulario de ingreso del panel: avisa del bloqueo por intentos fallidos.
admin.site.login_form = IngresoAdminForm

# Los permisos de este sistema salen del rol de cada cuenta (tabla rol),
# no de los grupos de Django, así que se quita "Grupos" del panel para no confundir.
admin.site.unregister(Group)


# ---------------------------------------------------------------
# Roles
# ---------------------------------------------------------------


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    """Tabla rol: Administrador y Usuario."""

    # Columnas de la lista: el nombre y cuántas cuentas lo tienen.
    list_display = ("rol", "cantidad_usuarios")
    # La caja de búsqueda busca por nombre del rol.
    search_fields = ("rol",)

    def get_queryset(self, request):
        """Agrega a cada rol la cantidad de usuarios, contada por la base en una sola consulta."""
        return super().get_queryset(request).annotate(total_usuarios=Count("usuario"))

    # description es el título de la columna; ordering permite ordenar haciendo clic.
    @admin.display(description="usuarios", ordering="total_usuarios")
    def cantidad_usuarios(self, rol):
        return rol.total_usuarios


# ---------------------------------------------------------------
# Usuarios
# ---------------------------------------------------------------


class UsuarioCreacionAdminForm(UserCreationForm):
    """Formulario de Django para crear usuarios, adaptado al modelo Usuario."""

    class Meta(UserCreationForm.Meta):
        model = Usuario
        # Además de estos campos, el formulario pide la contraseña dos veces
        # y la revisa con las reglas de AUTH_PASSWORD_VALIDATORS.
        fields = ("nombre_usuario", "email_usuario", "rol")


class UsuarioCambioAdminForm(UserChangeForm):
    """Formulario de Django para editar usuarios, adaptado al modelo Usuario."""

    class Meta(UserChangeForm.Meta):
        model = Usuario
        # El campo password se muestra como hash de solo lectura,
        # con un botón que lleva a la página para cambiarla.
        fields = ("nombre_usuario", "email_usuario", "password", "rol")


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """Gestión de cuentas: crear, editar, cambiar contraseña y eliminar."""

    # Formulario para editar y formulario para crear.
    form = UsuarioCambioAdminForm
    add_form = UsuarioCreacionAdminForm

    # Columnas de la lista de usuarios.
    list_display = ("nombre_usuario", "email_usuario", "rol", "cantidad_tinacos", "id_usuario")
    # Filtro lateral por rol (Administrador / Usuario).
    list_filter = ("rol",)
    # Búsqueda por nombre o por correo.
    search_fields = ("nombre_usuario", "email_usuario")
    # Orden alfabético por nombre.
    ordering = ("nombre_usuario",)
    # UserAdmin usa esto para grupos y permisos de Django; este modelo no los tiene.
    filter_horizontal = ()
    # La fecha de registro se muestra pero no se puede cambiar.
    readonly_fields = ("id_usuario",)

    # Secciones del formulario al editar un usuario.
    fieldsets = (
        (None, {"fields": ("nombre_usuario", "password")}),
        ("Datos de contacto", {"fields": ("email_usuario",)}),
        (
            "Permisos",
            {
                "fields": ("rol",),
                "description": (
                    "Administrador: acceso total y a este panel. "
                    "Usuario: solo puede ver sus propios tinacos."
                ),
            },
        ),
        ("Fechas", {"fields": ("id_usuario",)}),
    )
    # Secciones del formulario al crear un usuario (incluye las dos contraseñas).
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("nombre_usuario", "email_usuario", "rol", "password1", "password2"),
            },
        ),
    )

    def get_queryset(self, request):
        """Trae el rol y la cantidad de tinacos de cada usuario en la misma consulta."""
        return (
            super()
            .get_queryset(request)
            .select_related("rol")
            .annotate(total_tinacos=Count("tinacos"))
        )

    @admin.display(description="tinacos", ordering="total_tinacos")
    def cantidad_tinacos(self, usuario):
        return usuario.total_tinacos


# ---------------------------------------------------------------
# Tinacos, con sus mediciones y su ubicación dentro del mismo formulario
# ---------------------------------------------------------------


class UbicacionInline(admin.TabularInline):
    """Permite cargar la dirección del tinaco desde la página del tinaco."""

    model = Ubicacion
    # No se agregan filas vacías extra.
    extra = 0
    # Cada tinaco tiene una sola dirección.
    max_num = 1


class MedicionInline(admin.TabularInline):
    """Muestra y permite editar las mediciones desde la página del tinaco."""

    model = Medicion
    extra = 0
    # Columnas de cada fila; "estado_agua" se calcula, no se escribe.
    fields = ("fecha_medicion", "ph_medicion", "agua_medicion", "estado_agua")
    readonly_fields = ("estado_agua",)
    # Enlace para abrir la medición en su propia página.
    show_change_link = True

    @admin.display(description="estado")
    def estado_agua(self, medicion):
        # Una fila nueva todavía no tiene pH, así que no se puede clasificar.
        if medicion.ph_medicion is None:
            return "-"
        return medicion.estado()


@admin.register(Tinaco)
class TinacoAdmin(admin.ModelAdmin):
    """Gestión de tinacos."""

    # Columnas de la lista, incluidas dos calculadas a partir de la última medición.
    list_display = (
        "nombre_tinaco",
        "capacidad_tinaco",
        "usuario",
        "ph_actual",
        "agua_bebible",
        "id_tinaco",
    )
    # Filtro lateral por usuario responsable.
    list_filter = ("usuario",)
    # Búsqueda por nombre del tinaco, por responsable o por comuna.
    search_fields = ("nombre_tinaco", "usuario__nombre_usuario", "ubicaciones__comuna")
    # Trae al responsable en la misma consulta de la lista.
    list_select_related = ("usuario",)
    # Cuántos tinacos se muestran por página.
    list_per_page = 20
    # Ubicación y mediciones se editan dentro del formulario del tinaco.
    inlines = [UbicacionInline, MedicionInline]

    @admin.display(description="pH actual")
    def ph_actual(self, tinaco):
        medicion = tinaco.ultima_medicion()
        return medicion.ph_medicion if medicion else "-"

    # boolean=True hace que Django muestre un ícono verde o rojo en vez de True/False.
    @admin.display(description="¿bebible?", boolean=True)
    def agua_bebible(self, tinaco):
        medicion = tinaco.ultima_medicion()
        # None se muestra como un ícono gris de "desconocido".
        return medicion.es_bebible() if medicion else None


# ---------------------------------------------------------------
# Mediciones
# ---------------------------------------------------------------


class FiltroPotabilidad(admin.SimpleListFilter):
    """Filtro propio: separa las mediciones según si el agua es bebible o no."""

    # Título del filtro en la barra lateral.
    title = "estado del agua"
    # Nombre del parámetro en la dirección, por ejemplo ?estado=acida.
    parameter_name = "estado"

    def lookups(self, request, model_admin):
        """Opciones que aparecen en el filtro: (valor en la dirección, texto visible)."""
        return [
            ("bebible", "Bebible"),
            ("acida", "No bebible (ácida)"),
            ("alcalina", "No bebible (alcalina)"),
        ]

    def queryset(self, request, queryset):
        """Filtra las mediciones según la opción elegida, con los mismos límites de models.py."""
        if self.value() == "bebible":
            return queryset.filter(
                ph_medicion__gte=PH_MINIMO_BEBIBLE, ph_medicion__lte=PH_MAXIMO_BEBIBLE
            )
        if self.value() == "acida":
            return queryset.filter(ph_medicion__lt=PH_MINIMO_BEBIBLE)
        if self.value() == "alcalina":
            return queryset.filter(ph_medicion__gt=PH_MAXIMO_BEBIBLE)
        # Sin opción elegida ("Todo"), se muestran todas.
        return queryset


@admin.register(Medicion)
class MedicionAdmin(admin.ModelAdmin):
    """Gestión de las lecturas del sensor de pH."""

    list_display = ("tinaco", "fecha_medicion", "ph_medicion", "agua_medicion", "estado_agua")
    # Filtros: el propio de potabilidad, por tinaco y por fecha.
    list_filter = (FiltroPotabilidad, "tinaco", "fecha_medicion")
    # Búsqueda por nombre del tinaco.
    search_fields = ("tinaco__nombre_tinaco",)
    # Navegación por año, mes y día sobre la lista.
    date_hierarchy = "fecha_medicion"
    list_select_related = ("tinaco",)
    # De la más reciente a la más antigua.
    ordering = ("-fecha_medicion",)

    # Al ordenar esta columna se ordena por el pH, que es lo que decide el estado.
    @admin.display(description="estado", ordering="ph_medicion")
    def estado_agua(self, medicion):
        return medicion.estado()


# ---------------------------------------------------------------
# Ubicaciones
# ---------------------------------------------------------------


@admin.register(Ubicacion)
class UbicacionAdmin(admin.ModelAdmin):
    """Gestión de las direcciones de los tinacos."""

    list_display = ("tinaco", "calle", "numero", "comuna", "ciudad", "region")
    # Filtros por región, ciudad y comuna.
    list_filter = ("region", "ciudad", "comuna")
    # Búsqueda por cualquier parte de la dirección o por el tinaco.
    search_fields = ("calle", "comuna", "ciudad", "tinaco__nombre_tinaco")
    list_select_related = ("tinaco",)
