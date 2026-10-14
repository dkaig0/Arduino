"""
Formularios de la aplicación.

Un formulario de Django recibe lo que la persona escribe en el navegador,
revisa que los datos sean válidos y recién ahí los guarda en la base de datos.
"""

# forms contiene los tipos de campo (texto, número, contraseña) y las validaciones.
from django import forms

# make_password convierte una contraseña en un hash, para no guardarla en texto plano.
from django.contrib.auth.hashers import make_password

# Los modelos sobre los que trabajan estos formularios.
from .models import Medicion, Tinaco, Ubicacion, Usuario


class UsuarioForm(forms.ModelForm):
    """Formulario para crear y editar cuentas de usuario."""

    # Campo extra que no existe en el modelo: la contraseña sin cifrar que escribe el admin.
    password = forms.CharField(
        # Texto que se muestra sobre el campo.
        label="Contraseña",
        # PasswordInput muestra puntos en vez de letras; render_value=False la deja vacía al recargar.
        widget=forms.PasswordInput(render_value=False),
        # No es obligatoria porque al editar se puede dejar en blanco.
        required=False,
        # Explicación que aparece bajo el campo.
        help_text="Al editar, déjala vacía para mantener la contraseña actual.",
    )

    class Meta:
        # Modelo que este formulario crea o edita.
        model = Usuario
        # Campos del modelo que se muestran en el formulario.
        fields = ["nombre_usuario", "email_usuario", "rol"]
        # Nombres en español para esos campos.
        labels = {
            "nombre_usuario": "Nombre de usuario",
            "email_usuario": "Correo electrónico",
            "rol": "Rol",
        }

    def __init__(self, *args, **kwargs):
        # Se arma el formulario normal de Django.
        super().__init__(*args, **kwargs)
        # instance.pk es None cuando el usuario todavía no existe, o sea al crearlo.
        if self.instance.pk is None:
            # Al crear, la contraseña sí es obligatoria.
            self.fields["password"].required = True
            # Y se borra la ayuda, porque hablaba del caso de editar.
            self.fields["password"].help_text = ""

    def clean_password(self):
        """Django llama sola a este método para revisar el campo password."""
        # Se toma el valor ya limpio que escribió la persona.
        clave = self.cleaned_data["password"]
        # Si escribió algo y es muy corto, se rechaza.
        if clave and len(clave) < 6:
            raise forms.ValidationError("La contraseña debe tener al menos 6 caracteres.")
        # Si pasó la revisión, se devuelve tal cual.
        return clave

    def save(self, commit=True):
        """Guarda el usuario, cifrando la contraseña solo si escribieron una nueva."""
        # commit=False arma el objeto en memoria, sin escribir todavía en la base.
        usuario = super().save(commit=False)
        # Se recupera la contraseña escrita en el formulario.
        clave = self.cleaned_data["password"]
        # Solo si escribieron una nueva se reemplaza la guardada.
        if clave:
            usuario.password_usuario = make_password(clave)
        # Ahora sí se escribe la fila en la base de datos.
        if commit:
            usuario.save()
        # Se devuelve el usuario guardado para que la vista lo pueda usar.
        return usuario


class TinacoForm(forms.ModelForm):
    """Formulario para crear y editar tinacos."""

    # Se redefine el campo para poder exigir que la capacidad sea positiva.
    capacidad_tinaco = forms.IntegerField(
        label="Capacidad (litros)",
        # Mínimo 1 litro: así no se pueden guardar capacidades de 0 ni negativas.
        min_value=1,
        # Tope razonable para evitar números absurdos.
        max_value=1000000,
        # Mensaje en español cuando el número es menor al mínimo.
        error_messages={"min_value": "La capacidad debe ser mayor que cero."},
    )

    class Meta:
        model = Tinaco
        # Campos que se piden: nombre, capacidad y a qué usuario pertenece.
        fields = ["nombre_tinaco", "capacidad_tinaco", "usuario"]
        labels = {
            "nombre_tinaco": "Nombre del tinaco",
            "usuario": "Usuario responsable",
        }

    def clean_nombre_tinaco(self):
        """Revisa que el nombre no quede vacío ni con puros espacios."""
        # strip() quita los espacios de los extremos; el "or" cubre el caso de valor nulo.
        nombre = (self.cleaned_data["nombre_tinaco"] or "").strip()
        # Si después de limpiarlo no queda nada, se rechaza.
        if not nombre:
            raise forms.ValidationError("Escribe un nombre para el tinaco.")
        # Se devuelve el nombre ya sin espacios sobrantes.
        return nombre


class TinacosDeOtrosField(forms.ModelMultipleChoiceField):
    """Lista de casillas de tinacos que además muestra de quién es cada uno."""

    def label_from_instance(self, tinaco):
        # Texto que acompaña a cada casilla en pantalla.
        return f"{tinaco} (hoy a cargo de {tinaco.usuario.nombre_usuario})"


class AsignarTinacosForm(forms.Form):
    """Permite al administrador pasar tinacos de otros usuarios a uno en concreto."""

    # Campo de casillas marcables con los tinacos disponibles.
    tinacos = TinacosDeOtrosField(
        # Parte vacío: la lista real se arma en __init__, porque depende del usuario.
        queryset=Tinaco.objects.none(),
        # Se dibuja como casillas de verificación, no como lista desplegable.
        widget=forms.CheckboxSelectMultiple,
        # No es obligatorio marcar alguna.
        required=False,
        label="Tinacos a cargo de otros usuarios",
    )

    def __init__(self, *args, usuario=None, **kwargs):
        # usuario es el dueño al que se le quieren asignar tinacos.
        super().__init__(*args, **kwargs)
        # Se ofrecen todos los tinacos MENOS los que ya son de ese usuario.
        self.fields["tinacos"].queryset = (
            # exclude descarta los suyos; select_related trae de una vez al dueño actual.
            Tinaco.objects.exclude(usuario=usuario).select_related("usuario")
        )


class MedicionForm(forms.ModelForm):
    """Formulario para registrar y editar mediciones de pH."""

    # El pH se redefine para limitarlo al rango real de la escala.
    ph_medicion = forms.DecimalField(
        label="pH medido",
        # La escala de pH va de 0 a 14.
        min_value=0,
        max_value=14,
        # Hasta 4 dígitos en total y 2 decimales, igual que la columna de la base.
        max_digits=4,
        decimal_places=2,
        error_messages={
            "min_value": "El pH debe estar entre 0 y 14.",
            "max_value": "El pH debe estar entre 0 y 14.",
        },
    )
    # El agua medida tampoco puede ser negativa.
    agua_medicion = forms.DecimalField(
        label="Agua en el tinaco (litros)",
        min_value=0,
        max_digits=10,
        decimal_places=2,
        error_messages={"min_value": "El agua medida no puede ser negativa."},
    )

    class Meta:
        model = Medicion
        # El tinaco no se pide aquí: lo pone la vista según la página donde se está.
        fields = ["ph_medicion", "agua_medicion", "fecha_medicion"]
        labels = {
            "fecha_medicion": "Fecha y hora de la medición",
        }
        widgets = {
            # type="datetime-local" hace que el navegador muestre un selector de fecha y hora.
            "fecha_medicion": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
        }

    def __init__(self, *args, tinaco=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Al editar, el tinaco viene en la medición; al crear, lo pasa la vista.
        self.tinaco = tinaco or (self.instance.tinaco if self.instance.tinaco_id else None)
        # Si se sabe de qué tinaco se trata, se avisa su capacidad bajo el campo.
        if self.tinaco is not None:
            self.fields["agua_medicion"].help_text = (
                f"El tinaco almacena hasta {self.tinaco.capacidad_tinaco} litros."
            )

    def clean_agua_medicion(self):
        """Impide registrar más agua de la que cabe en el tinaco."""
        agua = self.cleaned_data["agua_medicion"]
        # Solo se puede comparar si se conoce el tinaco.
        if self.tinaco is not None and agua > self.tinaco.capacidad_tinaco:
            raise forms.ValidationError(
                f"El tinaco solo almacena {self.tinaco.capacidad_tinaco} litros."
            )
        return agua


class UbicacionForm(forms.ModelForm):
    """Formulario para la dirección donde está instalado el tinaco."""

    # El número de la dirección debe ser positivo.
    numero = forms.IntegerField(
        label="Número",
        min_value=1,
        error_messages={"min_value": "El número de la dirección debe ser mayor que cero."},
    )

    class Meta:
        model = Ubicacion
        # El tinaco no se pide: lo asigna la vista.
        fields = ["region", "ciudad", "comuna", "calle", "numero"]
        labels = {
            "region": "Región",
            "ciudad": "Ciudad",
            "comuna": "Comuna",
            "calle": "Calle",
            "numero": "Número",
        }
