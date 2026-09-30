from datetime import datetime

from django.contrib.auth.hashers import check_password
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .models import PH_MAXIMO_BEBIBLE, PH_MINIMO_BEBIBLE, Tinaco, Usuario


def usuario_actual(request):
    id_usuario = request.session.get("id_usuario")
    if id_usuario is None:
        return None
    # En la sesión (JSON) el Id se guarda como texto; se convierte de vuelta a fecha.
    try:
        fecha_id = datetime.fromisoformat(id_usuario)
    except (TypeError, ValueError):
        return None
    return Usuario.objects.select_related("rol").filter(pk=fecha_id).first()


def tinacos_con_medicion(usuario):
    tinacos = []
    for tinaco in usuario.tinacos.all():
        tinaco.medicion = tinaco.ultima_medicion()
        tinaco.lugar = tinaco.ubicacion()
        tinacos.append(tinaco)
    return tinacos


def login(request):
    error = ""

    if request.method == "POST":
        identificador = request.POST.get("username", "")
        clave = request.POST.get("password", "")

        usuario = Usuario.objects.filter(
            Q(nombre_usuario=identificador) | Q(email_usuario=identificador)
        ).first()

        if usuario is not None and check_password(clave, usuario.password_usuario):
            request.session["id_usuario"] = usuario.id_usuario.isoformat()
            return redirect("dashboard")
        else:
            error = "Usuario o contraseña incorrectos."

    return render(request, "Agua/login.html", {"error": error})


def logout(request):
    request.session.flush()
    return redirect("login")


def dashboard(request):
    usuario = usuario_actual(request)
    if usuario is None:
        return redirect("login")

    tinacos = tinacos_con_medicion(usuario)

    bebibles = 0
    for tinaco in tinacos:
        if tinaco.medicion is not None and tinaco.medicion.es_bebible():
            bebibles = bebibles + 1

    contexto = {
        "tinacos": tinacos,
        "tinacos_menu": tinacos,
        "usuario": usuario,
        "seccion": "dashboard",
        "total": len(tinacos),
        "bebibles": bebibles,
        "no_bebibles": len(tinacos) - bebibles,
        "ph_minimo": PH_MINIMO_BEBIBLE,
        "ph_maximo": PH_MAXIMO_BEBIBLE,
    }
    return render(request, "Agua/dashboard.html", contexto)


def detalle_tinaco(request, tinaco_id):
    usuario = usuario_actual(request)
    if usuario is None:
        return redirect("login")

    tinaco = get_object_or_404(Tinaco, pk=tinaco_id, usuario=usuario)
    medicion = tinaco.ultima_medicion()

    if medicion is None:
        mensaje = "Este tinaco todavía no tiene mediciones registradas."
    elif medicion.ph_medicion < PH_MINIMO_BEBIBLE:
        mensaje = "El agua está demasiado ácida. No es apta para consumo humano."
    elif medicion.ph_medicion > PH_MAXIMO_BEBIBLE:
        mensaje = "El agua está demasiado alcalina. No es apta para consumo humano."
    else:
        mensaje = "El agua está dentro del rango permitido. Es apta para consumo humano."

    contexto = {
        "tinaco": tinaco,
        "medicion": medicion,
        "lugar": tinaco.ubicacion(),
        "mediciones": tinaco.mediciones.all()[:4],
        "tinacos_menu": tinacos_con_medicion(usuario),
        "usuario": usuario,
        "mensaje": mensaje,
        "ph_minimo": PH_MINIMO_BEBIBLE,
        "ph_maximo": PH_MAXIMO_BEBIBLE,
        "rango_inicio": int(PH_MINIMO_BEBIBLE / 14 * 100),
        "rango_ancho": int((PH_MAXIMO_BEBIBLE - PH_MINIMO_BEBIBLE) / 14 * 100),
    }
    return render(request, "Agua/detalle.html", contexto)
