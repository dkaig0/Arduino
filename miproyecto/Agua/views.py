"""
Vistas de la aplicación: la lógica que responde a cada dirección del sitio.

Cada vista recibe una petición (request) del navegador, consulta o modifica la
base de datos y devuelve una página HTML o una redirección.
"""

# datetime se usa para reconstruir el Id del usuario guardado en la sesión.
from datetime import datetime

# wraps conserva el nombre de la vista original al envolverla en un decorador.
from functools import wraps

# messages muestra avisos de "guardado", "eliminado" o errores en la página siguiente.
from django.contrib import messages

# check_password compara la contraseña escrita con el hash guardado en la base.
from django.contrib.auth.hashers import check_password

# Q permite buscar por una condición O por otra (nombre O correo).
from django.db.models import Q

# get_object_or_404 busca un registro y muestra error 404 si no existe.
# redirect manda al navegador a otra dirección; render arma una página con un template.
from django.shortcuts import get_object_or_404, redirect, render

# Formularios que usan estas vistas.
from .forms import (
    AsignarTinacosForm,
    MedicionForm,
    TinacoForm,
    UbicacionForm,
    UsuarioForm,
)

# Modelos y constantes del rango bebible.
from .models import (
    PH_MAXIMO_BEBIBLE,
    PH_MINIMO_BEBIBLE,
    Medicion,
    Tinaco,
    Ubicacion,
    Usuario,
)


# ---------------------------------------------------------------
# Sesión y permisos
# ---------------------------------------------------------------


def usuario_actual(request):
    """Devuelve el usuario que inició sesión, o None si no hay sesión válida."""
    # En la sesión solo se guarda el Id de la cuenta, no la cuenta completa.
    id_usuario = request.session.get("id_usuario")
    # Si no hay nada guardado, nadie ha iniciado sesión.
    if id_usuario is None:
        return None
    # En la sesión (JSON) el Id se guarda como texto; se convierte de vuelta a fecha.
    try:
        fecha_id = datetime.fromisoformat(id_usuario)
    # Si el texto no es una fecha (por ejemplo, una sesión vieja), se pide entrar de nuevo.
    except (TypeError, ValueError):
        return None
    # select_related trae el rol en la misma consulta, para no hacer dos viajes a la base.
    return Usuario.objects.select_related("rol").filter(pk=fecha_id).first()


def requiere_sesion(vista):
    """Deja pasar solo a quien inició sesión y guarda el usuario en request.usuario."""

    # wraps hace que la función envuelta conserve su nombre original.
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        # Se busca quién está conectado.
        usuario = usuario_actual(request)
        # Si no hay nadie, se manda al formulario de ingreso.
        if usuario is None:
            return redirect("login")
        # Se deja el usuario disponible para la vista, sin tener que buscarlo de nuevo.
        request.usuario = usuario
        # Recién aquí se ejecuta la vista original.
        return vista(request, *args, **kwargs)

    return envoltura


def requiere_admin(vista):
    """Crear, editar y eliminar solo lo puede hacer el rol Administrador."""

    @wraps(vista)
    # Primero exige sesión iniciada; después revisa el rol.
    @requiere_sesion
    def envoltura(request, *args, **kwargs):
        # Si la cuenta no es administradora, no se ejecuta la vista.
        if not request.usuario.es_admin():
            # Se deja un aviso que se verá en la página siguiente.
            messages.error(request, "Tu cuenta es de solo lectura.")
            # Y se devuelve al dashboard.
            return redirect("dashboard")
        return vista(request, *args, **kwargs)

    return envoltura


def tinacos_visibles(usuario):
    """El administrador ve todos los tinacos; el resto solo los suyos."""
    # El administrador tiene acceso completo.
    if usuario.es_admin():
        return Tinaco.objects.select_related("usuario").all()
    # Una cuenta normal solo ve los tinacos donde figura como responsable.
    return usuario.tinacos.select_related("usuario").all()


def contexto_base(request, seccion=""):
    """Arma los datos que necesitan todas las páginas: usuario, rol y menú lateral."""
    # Lista de tinacos que se muestra en la barra lateral.
    menu = []
    # Se recorre cada tinaco que esta cuenta tiene permitido ver.
    for tinaco in tinacos_visibles(request.usuario):
        # Se le agrega su última medición, para pintar el punto verde o rojo.
        tinaco.medicion = tinaco.ultima_medicion()
        # Y su dirección, para mostrarla en las tarjetas.
        tinaco.lugar = tinaco.ubicacion()
        menu.append(tinaco)
    # El diccionario que se entrega al template.
    return {
        "usuario": request.usuario,
        # Con esto los templates deciden si muestran los botones de edición.
        "es_admin": request.usuario.es_admin(),
        "tinacos_menu": menu,
        # Sirve para resaltar la opción activa del menú.
        "seccion": seccion,
    }


# ---------------------------------------------------------------
# Entrar y salir
# ---------------------------------------------------------------


def login(request):
    """Muestra el formulario de ingreso y valida usuario y contraseña."""
    # Mensaje de error; parte vacío porque al abrir la página aún no hay error.
    error = ""

    # POST significa que la persona envió el formulario.
    if request.method == "POST":
        # Lo escrito en el campo de usuario (puede ser el nombre o el correo).
        identificador = request.POST.get("username", "")
        # La contraseña escrita.
        clave = request.POST.get("password", "")

        # Se busca una cuenta cuyo nombre O cuyo correo coincida.
        usuario = Usuario.objects.filter(
            Q(nombre_usuario=identificador) | Q(email_usuario=identificador)
        ).first()

        # Debe existir la cuenta y la contraseña debe coincidir con el hash guardado.
        if usuario is not None and check_password(clave, usuario.password_usuario):
            # Se guarda el Id en la sesión como texto, porque la sesión viaja en formato JSON.
            request.session["id_usuario"] = usuario.id_usuario.isoformat()
            # Ingreso correcto: al dashboard.
            return redirect("dashboard")
        else:
            # Datos incorrectos: se vuelve a mostrar el formulario con el aviso.
            error = "Usuario o contraseña incorrectos."

    # Tanto al abrir la página como al fallar el ingreso se muestra el formulario.
    return render(request, "Agua/login.html", {"error": error})


def logout(request):
    """Cierra la sesión y vuelve al formulario de ingreso."""
    # flush borra todos los datos guardados en la sesión.
    request.session.flush()
    return redirect("login")


# ---------------------------------------------------------------
# Lectura: dashboard y detalle (los dos roles)
# ---------------------------------------------------------------


@requiere_sesion
def dashboard(request):
    """Pantalla principal: resumen y tarjetas de todos los tinacos visibles."""
    # Datos comunes (usuario, menú) marcando "dashboard" como sección activa.
    contexto = contexto_base(request, seccion="dashboard")
    # Los tinacos ya vienen con su última medición cargada.
    tinacos = contexto["tinacos_menu"]

    # Contador de tinacos con agua bebible; parte en cero.
    bebibles = 0
    # Se revisa tinaco por tinaco.
    for tinaco in tinacos:
        # Solo cuentan los que tienen medición y están dentro del rango permitido.
        if tinaco.medicion is not None and tinaco.medicion.es_bebible():
            bebibles = bebibles + 1

    # Se agregan al contexto los datos propios de esta pantalla.
    contexto.update(
        {
            "tinacos": tinacos,
            # Total de tinacos que ve esta cuenta.
            "total": len(tinacos),
            "bebibles": bebibles,
            # Los que no son bebibles son el resto.
            "no_bebibles": len(tinacos) - bebibles,
            # Los límites se muestran en pantalla para explicar la regla.
            "ph_minimo": PH_MINIMO_BEBIBLE,
            "ph_maximo": PH_MAXIMO_BEBIBLE,
        }
    )
    # Se arma la página con el template del dashboard.
    return render(request, "Agua/dashboard.html", contexto)


@requiere_sesion
def detalle_tinaco(request, tinaco_id):
    """Ficha de un tinaco: su pH actual, si es bebible y su historial."""
    # Se busca el tinaco solo entre los que esta cuenta puede ver (si no, error 404).
    tinaco = get_object_or_404(tinacos_visibles(request.usuario), pk=tinaco_id)
    # La medición más reciente es la que se muestra arriba.
    medicion = tinaco.ultima_medicion()

    # Según el pH se arma la explicación en palabras.
    if medicion is None:
        mensaje = "Este tinaco todavía no tiene mediciones registradas."
    elif medicion.ph_medicion < PH_MINIMO_BEBIBLE:
        mensaje = "El agua está demasiado ácida. No es apta para consumo humano."
    elif medicion.ph_medicion > PH_MAXIMO_BEBIBLE:
        mensaje = "El agua está demasiado alcalina. No es apta para consumo humano."
    else:
        mensaje = "El agua está dentro del rango permitido. Es apta para consumo humano."

    contexto = contexto_base(request)
    contexto.update(
        {
            "tinaco": tinaco,
            "medicion": medicion,
            # La dirección del tinaco, si tiene.
            "lugar": tinaco.ubicacion(),
            # Todas sus mediciones, para la tabla del final.
            "mediciones": tinaco.mediciones.all(),
            "mensaje": mensaje,
            "ph_minimo": PH_MINIMO_BEBIBLE,
            "ph_maximo": PH_MAXIMO_BEBIBLE,
            # Dónde empieza la franja verde de la escala, en porcentaje.
            "rango_inicio": int(PH_MINIMO_BEBIBLE / 14 * 100),
            # Y cuánto mide esa franja.
            "rango_ancho": int((PH_MAXIMO_BEBIBLE - PH_MINIMO_BEBIBLE) / 14 * 100),
        }
    )
    return render(request, "Agua/detalle.html", contexto)


# ---------------------------------------------------------------
# CRUD de usuarios (solo administrador)
# ---------------------------------------------------------------


@requiere_admin
def usuarios(request):
    """Lista todas las cuentas del sistema."""
    contexto = contexto_base(request, seccion="usuarios")
    # Se traen los usuarios junto con su rol en una sola consulta.
    contexto["usuarios"] = Usuario.objects.select_related("rol").all()
    return render(request, "Agua/usuarios.html", contexto)


@requiere_admin
def usuario_nuevo(request):
    """Crea una cuenta nueva con su contraseña."""
    # Si la petición es POST se llena con lo enviado; si no, el formulario va vacío.
    formulario = UsuarioForm(request.POST or None)

    # is_valid() ejecuta todas las validaciones del formulario.
    if request.method == "POST" and formulario.is_valid():
        # save() guarda la cuenta y cifra la contraseña.
        nuevo = formulario.save()
        # Aviso verde que se verá en la lista de usuarios.
        messages.success(request, f"Usuario {nuevo.nombre_usuario} creado.")
        return redirect("usuarios")

    contexto = contexto_base(request, seccion="usuarios")
    # Datos que necesita la plantilla genérica de formularios.
    contexto.update(
        {
            "titulo": "Nuevo usuario",
            "formulario": formulario,
            "texto_boton": "Crear usuario",
            # A dónde vuelve el botón Cancelar.
            "volver": "usuarios",
        }
    )
    return render(request, "Agua/formulario.html", contexto)


@requiere_admin
def usuario_editar(request, usuario_id):
    """Edita una cuenta existente."""
    # Se busca la cuenta a editar; si no existe, error 404.
    editado = get_object_or_404(Usuario, pk=usuario_id)
    # instance hace que el formulario aparezca con los datos actuales.
    formulario = UsuarioForm(request.POST or None, instance=editado)

    if request.method == "POST" and formulario.is_valid():
        # Si dejaron la contraseña vacía, se conserva la anterior.
        formulario.save()
        messages.success(request, f"Usuario {editado.nombre_usuario} actualizado.")
        return redirect("usuarios")

    contexto = contexto_base(request, seccion="usuarios")
    contexto.update(
        {
            "titulo": f"Editar usuario: {editado.nombre_usuario}",
            "formulario": formulario,
            "texto_boton": "Guardar cambios",
            "volver": "usuarios",
        }
    )
    return render(request, "Agua/formulario.html", contexto)


@requiere_admin
def usuario_eliminar(request, usuario_id):
    """Pide confirmación y elimina una cuenta, si se puede."""
    # Cuenta que se quiere eliminar.
    objetivo = get_object_or_404(Usuario, pk=usuario_id)

    # Primer caso que lo impide: eliminarse a uno mismo.
    if objetivo.pk == request.usuario.pk:
        impedimento = "No puedes eliminar la cuenta con la que estás conectado."
    # Segundo caso: la cuenta tiene tinacos y la base no permite dejarlos sin responsable.
    elif objetivo.tinacos.exists():
        impedimento = (
            f"Este usuario tiene {objetivo.tinacos.count()} tinaco(s) a su cargo. "
            "Asígnalos a otro usuario antes de eliminarlo."
        )
    # Si no hay impedimento, la cadena queda vacía.
    else:
        impedimento = ""

    # Solo se borra cuando confirman (POST) y no hay impedimento.
    if request.method == "POST" and not impedimento:
        # Se guarda el nombre antes de borrar, para poder mostrarlo en el aviso.
        nombre = objetivo.nombre_usuario
        objetivo.delete()
        messages.success(request, f"Usuario {nombre} eliminado.")
        return redirect("usuarios")

    contexto = contexto_base(request, seccion="usuarios")
    # Datos para la página de confirmación.
    contexto.update(
        {
            "titulo": f"Eliminar usuario: {objetivo.nombre_usuario}",
            "mensaje": "Esta acción no se puede deshacer.",
            "impedimento": impedimento,
            "volver": "usuarios",
        }
    )
    return render(request, "Agua/confirmar.html", contexto)


@requiere_admin
def usuario_tinacos(request, usuario_id):
    """Asigna tinacos de otros usuarios al usuario elegido."""
    # Usuario que recibirá los tinacos.
    objetivo = get_object_or_404(Usuario, pk=usuario_id)
    # El formulario necesita saber de quién se trata para no ofrecerle los suyos.
    formulario = AsignarTinacosForm(request.POST or None, usuario=objetivo)

    if request.method == "POST" and formulario.is_valid():
        # Lista de tinacos que marcaron en las casillas.
        elegidos = formulario.cleaned_data["tinacos"]
        # Se cambia el responsable de cada uno y se guarda.
        for tinaco in elegidos:
            tinaco.usuario = objetivo
            tinaco.save()

        # Aviso distinto según si marcaron algo o no.
        if elegidos:
            messages.success(
                request,
                f"{len(elegidos)} tinaco(s) asignado(s) a {objetivo.nombre_usuario}.",
            )
        else:
            messages.error(request, "No seleccionaste ningún tinaco.")
        # Se recarga la misma página para ver el resultado.
        return redirect("usuario_tinacos", usuario_id=objetivo.pk)

    contexto = contexto_base(request, seccion="usuarios")
    contexto.update(
        {
            "objetivo": objetivo,
            # Los tinacos que ya tiene a su cargo.
            "asignados": objetivo.tinacos.all(),
            "formulario": formulario,
        }
    )
    return render(request, "Agua/asignar_tinacos.html", contexto)


# ---------------------------------------------------------------
# CRUD de tinacos (solo administrador)
# ---------------------------------------------------------------


@requiere_admin
def tinaco_nuevo(request):
    """Registra un tinaco nuevo y lo asigna a un usuario."""
    formulario = TinacoForm(request.POST or None)

    if request.method == "POST" and formulario.is_valid():
        nuevo = formulario.save()
        messages.success(request, f"Tinaco {nuevo} creado.")
        # Se abre directamente la ficha del tinaco recién creado.
        return redirect("detalle_tinaco", tinaco_id=nuevo.pk)

    contexto = contexto_base(request, seccion="dashboard")
    contexto.update(
        {
            "titulo": "Nuevo tinaco",
            "formulario": formulario,
            "texto_boton": "Crear tinaco",
            "volver": "dashboard",
        }
    )
    return render(request, "Agua/formulario.html", contexto)


@requiere_admin
def tinaco_editar(request, tinaco_id):
    """Cambia el nombre, la capacidad o el responsable de un tinaco."""
    tinaco = get_object_or_404(Tinaco, pk=tinaco_id)
    formulario = TinacoForm(request.POST or None, instance=tinaco)

    if request.method == "POST" and formulario.is_valid():
        formulario.save()
        messages.success(request, f"Tinaco {tinaco} actualizado.")
        return redirect("detalle_tinaco", tinaco_id=tinaco.pk)

    contexto = contexto_base(request)
    contexto.update(
        {
            "titulo": f"Editar tinaco: {tinaco}",
            "formulario": formulario,
            "texto_boton": "Guardar cambios",
            "volver": "detalle_tinaco",
            # El botón Cancelar necesita el Id para volver a la ficha correcta.
            "volver_id": tinaco.pk,
        }
    )
    return render(request, "Agua/formulario.html", contexto)


@requiere_admin
def tinaco_eliminar(request, tinaco_id):
    """Pide confirmación y elimina un tinaco con todo lo que depende de él."""
    tinaco = get_object_or_404(Tinaco, pk=tinaco_id)

    if request.method == "POST":
        # Se guarda el nombre antes de borrarlo para el aviso.
        nombre = str(tinaco)
        # Al borrar el tinaco, la base borra en cascada sus mediciones y su ubicación.
        tinaco.delete()
        messages.success(request, f"Tinaco {nombre} eliminado con sus mediciones y ubicación.")
        return redirect("dashboard")

    contexto = contexto_base(request)
    contexto.update(
        {
            "titulo": f"Eliminar tinaco: {tinaco}",
            # Se avisa cuántas mediciones se perderán.
            "mensaje": (
                f"Se eliminarán también sus {tinaco.mediciones.count()} medición(es) "
                "y su ubicación. Esta acción no se puede deshacer."
            ),
            "impedimento": "",
            "volver": "detalle_tinaco",
            "volver_id": tinaco.pk,
        }
    )
    return render(request, "Agua/confirmar.html", contexto)


# ---------------------------------------------------------------
# CRUD de mediciones (solo administrador)
# ---------------------------------------------------------------


@requiere_admin
def medicion_nueva(request, tinaco_id):
    """Registra una medición de pH para un tinaco."""
    # Tinaco al que pertenecerá la medición.
    tinaco = get_object_or_404(Tinaco, pk=tinaco_id)
    # Se le pasa el tinaco al formulario para poder comparar el agua con su capacidad.
    formulario = MedicionForm(request.POST or None, tinaco=tinaco)

    if request.method == "POST" and formulario.is_valid():
        # commit=False arma la medición sin guardarla todavía.
        medicion = formulario.save(commit=False)
        # Se completa el dato que no venía en el formulario.
        medicion.tinaco = tinaco
        # Ahora sí se escribe en la base.
        medicion.save()
        messages.success(request, "Medición registrada.")
        return redirect("detalle_tinaco", tinaco_id=tinaco.pk)

    contexto = contexto_base(request)
    contexto.update(
        {
            "titulo": f"Nueva medición: {tinaco}",
            "formulario": formulario,
            "texto_boton": "Registrar medición",
            "volver": "detalle_tinaco",
            "volver_id": tinaco.pk,
        }
    )
    return render(request, "Agua/formulario.html", contexto)


@requiere_admin
def medicion_editar(request, medicion_id):
    """Corrige los datos de una medición ya registrada."""
    medicion = get_object_or_404(Medicion, pk=medicion_id)
    # El formulario saca el tinaco desde la propia medición.
    formulario = MedicionForm(request.POST or None, instance=medicion)

    if request.method == "POST" and formulario.is_valid():
        formulario.save()
        messages.success(request, "Medición actualizada.")
        # tinaco_id es la columna de la relación: evita consultar el tinaco completo.
        return redirect("detalle_tinaco", tinaco_id=medicion.tinaco_id)

    contexto = contexto_base(request)
    contexto.update(
        {
            "titulo": f"Editar medición: {medicion.tinaco}",
            "formulario": formulario,
            "texto_boton": "Guardar cambios",
            "volver": "detalle_tinaco",
            "volver_id": medicion.tinaco_id,
        }
    )
    return render(request, "Agua/formulario.html", contexto)


@requiere_admin
def medicion_eliminar(request, medicion_id):
    """Pide confirmación y elimina una medición."""
    medicion = get_object_or_404(Medicion, pk=medicion_id)
    # Se guarda a qué tinaco pertenecía, para volver a su ficha después de borrarla.
    tinaco_id = medicion.tinaco_id

    if request.method == "POST":
        medicion.delete()
        messages.success(request, "Medición eliminada.")
        return redirect("detalle_tinaco", tinaco_id=tinaco_id)

    contexto = contexto_base(request)
    contexto.update(
        {
            "titulo": "Eliminar medición",
            # Se describe la medición para que se sepa cuál se va a borrar.
            "mensaje": (
                f"Medición del {medicion.fecha_medicion:%d-%m-%Y %H:%M} "
                f"con pH {medicion.ph_medicion}. Esta acción no se puede deshacer."
            ),
            "impedimento": "",
            "volver": "detalle_tinaco",
            "volver_id": tinaco_id,
        }
    )
    return render(request, "Agua/confirmar.html", contexto)


# ---------------------------------------------------------------
# CRUD de ubicaciones (solo administrador)
# ---------------------------------------------------------------


@requiere_admin
def ubicacion_nueva(request, tinaco_id):
    """Agrega la dirección donde está instalado un tinaco."""
    tinaco = get_object_or_404(Tinaco, pk=tinaco_id)
    formulario = UbicacionForm(request.POST or None)

    if request.method == "POST" and formulario.is_valid():
        # Se arma la ubicación sin guardarla, para poder completar el tinaco.
        ubicacion = formulario.save(commit=False)
        ubicacion.tinaco = tinaco
        ubicacion.save()
        messages.success(request, "Ubicación guardada.")
        return redirect("detalle_tinaco", tinaco_id=tinaco.pk)

    contexto = contexto_base(request)
    contexto.update(
        {
            "titulo": f"Nueva ubicación: {tinaco}",
            "formulario": formulario,
            "texto_boton": "Guardar ubicación",
            "volver": "detalle_tinaco",
            "volver_id": tinaco.pk,
        }
    )
    return render(request, "Agua/formulario.html", contexto)


@requiere_admin
def ubicacion_editar(request, ubicacion_id):
    """Corrige la dirección de un tinaco."""
    ubicacion = get_object_or_404(Ubicacion, pk=ubicacion_id)
    formulario = UbicacionForm(request.POST or None, instance=ubicacion)

    if request.method == "POST" and formulario.is_valid():
        formulario.save()
        messages.success(request, "Ubicación actualizada.")
        return redirect("detalle_tinaco", tinaco_id=ubicacion.tinaco_id)

    contexto = contexto_base(request)
    contexto.update(
        {
            "titulo": f"Editar ubicación: {ubicacion.tinaco}",
            "formulario": formulario,
            "texto_boton": "Guardar cambios",
            "volver": "detalle_tinaco",
            "volver_id": ubicacion.tinaco_id,
        }
    )
    return render(request, "Agua/formulario.html", contexto)


@requiere_admin
def ubicacion_eliminar(request, ubicacion_id):
    """Pide confirmación y elimina la dirección de un tinaco."""
    ubicacion = get_object_or_404(Ubicacion, pk=ubicacion_id)
    # Se recuerda el tinaco para volver a su ficha después.
    tinaco_id = ubicacion.tinaco_id

    if request.method == "POST":
        ubicacion.delete()
        messages.success(request, "Ubicación eliminada.")
        return redirect("detalle_tinaco", tinaco_id=tinaco_id)

    contexto = contexto_base(request)
    contexto.update(
        {
            "titulo": "Eliminar ubicación",
            "mensaje": f"{ubicacion}. Esta acción no se puede deshacer.",
            "impedimento": "",
            "volver": "detalle_tinaco",
            "volver_id": tinaco_id,
        }
    )
    return render(request, "Agua/confirmar.html", contexto)
