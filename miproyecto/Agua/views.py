"""
Vistas de la aplicación: la lógica que responde a cada dirección del sitio.

Cada vista recibe una petición (request) del navegador, consulta o modifica la
base de datos y devuelve una página HTML o una redirección.

La seguridad usa las herramientas nativas de Django:
- login() / logout() y la sesión para saber quién está conectado.
- @login_required para exigir sesión iniciada.
- @permission_required para exigir un permiso (los permisos salen del rol, ver models.py).
"""

# datetime se usa para leer la fecha del ingreso anterior guardada en la sesión.
from datetime import datetime

# settings da acceso a la configuración (por ejemplo LOGIN_REDIRECT_URL).
from django.conf import settings

# messages muestra avisos de "guardado", "eliminado" o errores en la página siguiente.
from django.contrib import messages

# Funciones del sistema de autenticación de Django. Se renombran con "auth_"
# para que no choquen con las vistas login y logout de este archivo.
# update_session_auth_hash evita que se cierre la sesión al cambiar la propia contraseña.
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import update_session_auth_hash

# Decoradores nativos que protegen las vistas.
from django.contrib.auth.decorators import login_required, permission_required

# get_object_or_404 busca un registro y muestra error 404 si no existe.
# redirect manda al navegador a otra dirección; render arma una página con un template.
from django.shortcuts import get_object_or_404, redirect, render

# timezone.now entrega la fecha y hora actual, para la cookie de último ingreso.
from django.utils import timezone

# Revisa que una dirección de redirección sea de este mismo sitio (evita redirecciones abiertas).
from django.utils.http import url_has_allowed_host_and_scheme

# require_POST rechaza (error 405) cualquier petición que no sea POST.
from django.views.decorators.http import require_POST

# Formularios que usan estas vistas.
from .forms import (
    AsignarTinacosForm,
    IngresoForm,
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

# Nombre de la cookie opcional que recuerda el último ingreso en este navegador.
COOKIE_ULTIMO_INGRESO = "ultimo_ingreso"
# Cuánto duran las cookies propias en el navegador: 365 días, expresado en segundos.
DURACION_COOKIE = 60 * 60 * 24 * 365

# Cookie que guarda la decisión de la persona sobre las cookies opcionales.
COOKIE_CONSENTIMIENTO = "consentimiento_cookies"
# Los dos valores que puede tener esa decisión.
COOKIES_ACEPTADAS = "aceptadas"
COOKIES_RECHAZADAS = "rechazadas"
DECISIONES_COOKIES = {COOKIES_ACEPTADAS, COOKIES_RECHAZADAS}


# ---------------------------------------------------------------
# Sesión y permisos
# ---------------------------------------------------------------


def requiere_permiso(permiso):
    """
    Junta los dos decoradores nativos de Django en uno solo:

    1. login_required: si no hay sesión iniciada, manda al formulario de ingreso
       (LOGIN_URL en settings.py) y recuerda a dónde se quería ir (?next=...).
    2. permission_required: si hay sesión pero la cuenta no tiene el permiso,
       responde "403 Prohibido" con el template 403.html.
    """

    def decorador(vista):
        # Primero se aplica permission_required y por fuera login_required,
        # así que login_required es lo primero que se revisa al entrar.
        return login_required(permission_required(permiso, raise_exception=True)(vista))

    return decorador


def tinacos_visibles(usuario):
    """El administrador ve todos los tinacos; el resto solo los suyos."""
    # El administrador tiene acceso completo.
    if usuario.es_admin():
        return Tinaco.objects.select_related("usuario").all()
    # Una cuenta normal solo ve los tinacos donde figura como responsable.
    return usuario.tinacos.select_related("usuario").all()


def contexto_base(request, seccion=""):
    """Arma los datos que necesitan todas las páginas: rol y menú lateral."""
    # request.user es la cuenta conectada; la carga AuthenticationMiddleware desde la sesión.
    # (Los templates también la reciben como {{ user }}, junto con {{ perms }}).
    usuario = request.user
    # Lista de tinacos que se muestra en la barra lateral.
    menu = []
    # Se recorre cada tinaco que esta cuenta tiene permitido ver.
    for tinaco in tinacos_visibles(usuario):
        # Se le agrega su última medición, para pintar el punto verde o rojo.
        tinaco.medicion = tinaco.ultima_medicion()
        # Y su dirección, para mostrarla en las tarjetas.
        tinaco.lugar = tinaco.ubicacion()
        menu.append(tinaco)
    # El diccionario que se entrega al template.
    return {
        # Con esto los templates ajustan textos según el rol.
        "es_admin": usuario.es_admin(),
        "tinacos_menu": menu,
        # Sirve para resaltar la opción activa del menú.
        "seccion": seccion,
    }


def sal_cookie(usuario):
    """
    "Sal" con la que se firma la cookie de último ingreso.

    Al incluir el Id de la cuenta, una cookie firmada para un usuario no sirve
    para otro: si dos personas usan el mismo navegador, cada una solo ve su fecha.
    """
    return f"{COOKIE_ULTIMO_INGRESO}:{usuario.pk}"


# ---------------------------------------------------------------
# Entrar y salir
# ---------------------------------------------------------------


def login(request):
    """Muestra el formulario de ingreso e inicia la sesión con el sistema de Django."""
    # Quien ya inició sesión no necesita volver a ingresar.
    if request.user.is_authenticated:
        return redirect("dashboard")

    # IngresoForm hereda de AuthenticationForm: al validarse llama a authenticate(),
    # que revisa usuario y contraseña con el backend de backends.py.
    # Si la petición no es POST, data es None y el formulario va vacío.
    formulario = IngresoForm(request, data=request.POST or None)

    # is_valid() es True solo si los datos son correctos y la cuenta está activa.
    if request.method == "POST" and formulario.is_valid():
        # La cuenta que validó el formulario.
        usuario = formulario.get_user()
        # login() guarda el Id de la cuenta en la sesión (tabla django_session)
        # y cambia el identificador de la sesión para evitar la fijación de sesión.
        auth_login(request, usuario)

        # --- Sesión: "Mantener sesión iniciada" ---
        if not formulario.cleaned_data["recordarme"]:
            # 0 significa que la sesión termina al cerrar el navegador.
            request.session.set_expiry(0)
        # Si la marcó, la sesión dura SESSION_COOKIE_AGE (una semana, ver settings.py).

        # La cookie "ultimo_ingreso" es opcional: solo se usa si la persona
        # aceptó las cookies en la ventana de consentimiento.
        acepta_cookies = request.COOKIES.get(COOKIE_CONSENTIMIENTO) == COOKIES_ACEPTADAS

        # --- Cookie: lectura ---
        # Se lee la cookie firmada del ingreso anterior. Si no existe, si es de
        # otra cuenta o si alguien la alteró, la firma no calza y se obtiene None.
        anterior = None
        if acepta_cookies:
            anterior = request.get_signed_cookie(
                COOKIE_ULTIMO_INGRESO, default=None, salt=sal_cookie(usuario)
            )
        # Se guarda en la sesión para mostrarla en el dashboard mientras dure la sesión.
        request.session["ingreso_anterior"] = anterior

        # A dónde ir después: ?next=... solo si apunta a este mismo sitio;
        # si no, al dashboard. Así nadie puede usar el login para redirigir a otro sitio.
        destino = request.GET.get("next")
        if not url_has_allowed_host_and_scheme(
            destino, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        ):
            destino = settings.LOGIN_REDIRECT_URL
        respuesta = redirect(destino)

        # --- Cookie: creación (solo con consentimiento) ---
        # Se guarda la fecha y hora de este ingreso, firmada para que no se pueda alterar.
        if acepta_cookies:
            respuesta.set_signed_cookie(
                COOKIE_ULTIMO_INGRESO,
                timezone.now().isoformat(),
                salt=sal_cookie(usuario),
                # Tiempo de vida de la cookie en el navegador.
                max_age=DURACION_COOKIE,
                # httponly: JavaScript no puede leerla, solo el servidor.
                httponly=True,
                # samesite Lax: no se envía en peticiones que vienen de otros sitios.
                samesite="Lax",
            )
        return respuesta

    # Tanto al abrir la página como al fallar el ingreso se muestra el formulario.
    return render(request, "Agua/login.html", {"formulario": formulario})


@require_POST
def guardar_cookies(request):
    """
    Guarda la decisión de la ventana de cookies: aceptar, rechazar o volver a preguntar.

    No exige sesión, porque la ventana también aparece en la página de ingreso.
    Solo acepta POST con token CSRF.
    """
    # Lo que eligió la persona: "aceptadas", "rechazadas" o "cambiar".
    decision = request.POST.get("decision")

    # Se vuelve a la página donde estaba, solo si es una dirección de este sitio.
    volver = request.POST.get("volver")
    if not url_has_allowed_host_and_scheme(
        volver, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        volver = settings.LOGIN_REDIRECT_URL
    respuesta = redirect(volver)

    if decision in DECISIONES_COOKIES:
        # --- Cookie de consentimiento: creación ---
        # Recuerda la decisión por un año, para no preguntar en cada visita.
        respuesta.set_cookie(
            COOKIE_CONSENTIMIENTO,
            decision,
            max_age=DURACION_COOKIE,
            httponly=True,
            samesite="Lax",
        )
        if decision == COOKIES_RECHAZADAS:
            # Al rechazar se borra la cookie opcional, si ya existía,
            # y se deja de mostrar el dato que se había leído de ella.
            respuesta.delete_cookie(COOKIE_ULTIMO_INGRESO, samesite="Lax")
            request.session.pop("ingreso_anterior", None)
            messages.success(request, "Rechazaste las cookies opcionales.")
        else:
            messages.success(request, "Aceptaste las cookies.")
    elif decision == "cambiar":
        # Se borra la decisión: la ventana vuelve a aparecer en la siguiente página.
        respuesta.delete_cookie(COOKIE_CONSENTIMIENTO, samesite="Lax")
    # Cualquier otro valor se ignora: no se crea ninguna cookie.

    return respuesta


@require_POST
def logout(request):
    """Cierra la sesión y vuelve al formulario de ingreso. Solo acepta POST (con token CSRF)."""
    # logout() de Django borra la sesión de la base y de la cookie del navegador.
    auth_logout(request)
    messages.success(request, "Cerraste sesión correctamente.")
    return redirect("login")


# ---------------------------------------------------------------
# Lectura: dashboard y detalle (los dos roles)
# ---------------------------------------------------------------


@requiere_permiso("Agua.view_tinaco")
def dashboard(request):
    """Pantalla principal: resumen y tarjetas de todos los tinacos visibles."""
    # Datos comunes (rol, menú) marcando "dashboard" como sección activa.
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

    # El ingreso anterior se leyó de la cookie al iniciar sesión y quedó en la sesión.
    texto_anterior = request.session.get("ingreso_anterior")
    # En la sesión está como texto; se convierte a fecha para darle formato en el template.
    ingreso_anterior = datetime.fromisoformat(texto_anterior) if texto_anterior else None

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
            # Datos de la sesión y de la cookie, para el recuadro "Tu sesión".
            "ingreso_anterior": ingreso_anterior,
            # True si la sesión termina al cerrar el navegador (no marcó "Mantener sesión").
            "sesion_temporal": request.session.get_expire_at_browser_close(),
            # Fecha en que vence la sesión, si se pidió mantenerla.
            "sesion_vence": request.session.get_expiry_date(),
        }
    )
    # Se arma la página con el template del dashboard.
    return render(request, "Agua/dashboard.html", contexto)


@requiere_permiso("Agua.view_tinaco")
def detalle_tinaco(request, tinaco_id):
    """Ficha de un tinaco: su pH actual, si es bebible y su historial."""
    # Se busca el tinaco solo entre los que esta cuenta puede ver (si no, error 404).
    tinaco = get_object_or_404(tinacos_visibles(request.user), pk=tinaco_id)
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


@requiere_permiso("Agua.view_usuario")
def usuarios(request):
    """Lista todas las cuentas del sistema."""
    contexto = contexto_base(request, seccion="usuarios")
    # Se traen los usuarios junto con su rol en una sola consulta.
    contexto["usuarios"] = Usuario.objects.select_related("rol").all()
    return render(request, "Agua/usuarios.html", contexto)


@requiere_permiso("Agua.add_usuario")
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


@requiere_permiso("Agua.change_usuario")
def usuario_editar(request, usuario_id):
    """Edita una cuenta existente."""
    # Se busca la cuenta a editar; si no existe, error 404.
    editado = get_object_or_404(Usuario, pk=usuario_id)
    # instance hace que el formulario aparezca con los datos actuales.
    formulario = UsuarioForm(request.POST or None, instance=editado)

    if request.method == "POST" and formulario.is_valid():
        # Si dejaron la contraseña vacía, se conserva la anterior.
        formulario.save()
        # Cambiar la contraseña invalida las sesiones abiertas de esa cuenta (seguridad).
        # Si el administrador se editó a sí mismo, se actualiza su sesión para no sacarlo.
        if editado.pk == request.user.pk:
            update_session_auth_hash(request, editado)
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


@requiere_permiso("Agua.delete_usuario")
def usuario_eliminar(request, usuario_id):
    """Pide confirmación y elimina una cuenta, si se puede."""
    # Cuenta que se quiere eliminar.
    objetivo = get_object_or_404(Usuario, pk=usuario_id)

    # Primer caso que lo impide: eliminarse a uno mismo.
    if objetivo.pk == request.user.pk:
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


@requiere_permiso("Agua.change_tinaco")
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


@requiere_permiso("Agua.add_tinaco")
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


@requiere_permiso("Agua.change_tinaco")
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


@requiere_permiso("Agua.delete_tinaco")
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


@requiere_permiso("Agua.add_medicion")
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


@requiere_permiso("Agua.change_medicion")
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


@requiere_permiso("Agua.delete_medicion")
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


@requiere_permiso("Agua.add_ubicacion")
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


@requiere_permiso("Agua.change_ubicacion")
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


@requiere_permiso("Agua.delete_ubicacion")
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
