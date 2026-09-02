from django.shortcuts import get_object_or_404, redirect, render

from .models import PH_MAXIMO_BEBIBLE, PH_MINIMO_BEBIBLE, Tinaco #Modelo 

USUARIO_DEMO = "demo" #Usuario
CLAVE_DEMO = "demo1234" # Comntraseña


def hay_sesion(request): #Si hay sesión activa, devuelve True. Si no, devuelve False.
    return request.session.get("usuario") is not None


def login(request): #Funcion Login pidiendo una request
    error = "" #error vacio

    if request.method == "POST": #Si el usuario hace un POST, se obtiene el usuario y la contraseña del formulario
        usuario = request.POST.get("username", "") #Usuario se obtiene del formulario
        clave = request.POST.get("password", "")# Contraseña se obtiene del formulario 

        if usuario == USUARIO_DEMO and clave == CLAVE_DEMO: #Si el usuario ingresado y la clave ingresada son correctos, se guarda la sesión y se redirige al dashboard. Si no, se muestra un mensaje de error.
            request.session["usuario"] = usuario #se onbteniene el usuario y se guarda en la sesión
            return redirect("dashboard")#se redirige a dashboard
        else:
            error = "Usuario o contraseña incorrectos."

    return render(request, "Agua/login.html", {"error": error}) #Se renderiza la plantilla login.html con el mensaje de error (si lo hay)


def logout(request):#Con .flush la sesion se borra y se redirige al login
    request.session.flush()
    return redirect("login")


def dashboard(request):#Funcion de dashboard
    if not hay_sesion(request): #Si no hay sesión activa, se redirige al login
        return redirect("login")

    tinacos = Tinaco.objects.all()#Los tinacos se obtienen de la base de datos y se guardan en la variable tinacos

    bebibles = 0 #iniciamos un contador de tinacos bebibles en 0
    for tinaco in tinacos:#se recorre la lista de tinacos 
        if tinaco.es_bebible():
            bebibles = bebibles + 1


    #El contexto es un diccionario que contiene los datos que se van a pasar a la plantilla dashboard.html. Se pasan los tinacos, el usuario, la sección, el total de tinacos, el total de tinacos bebibles y no bebibles, y los valores de pH mínimo y máximo para que se puedan mostrar en la plantilla.
    contexto = {
        "tinacos": tinacos,
        "tinacos_menu": tinacos,
        "usuario": request.session["usuario"],
        "seccion": "dashboard",
        "total": tinacos.count(),
        "bebibles": bebibles,
        "no_bebibles": tinacos.count() - bebibles,
        "ph_minimo": PH_MINIMO_BEBIBLE,
        "ph_maximo": PH_MAXIMO_BEBIBLE,
    }
    return render(request, "Agua/dashboard.html", contexto)
    #muestra la template dashboard.html con el contexto que contiene los datos de los tinacos y el usuario

def detalle_tinaco(request, tinaco_id):#Función para mostrar los detalles de un tinaco
    if not hay_sesion(request):#si no hay sesión activa, se redirige al login
        return redirect("login")

    tinaco = get_object_or_404(Tinaco, pk=tinaco_id) #Se obtiene el tinaco con el ID proporcionado o se devuelve un error 404

    if tinaco.ph_actual < PH_MINIMO_BEBIBLE:#Si el pH del tinaco es menor que el mínimo permitido, se muestra un mensaje de que el agua está demasiado ácida y no es apta para consumo humano. Si el pH es mayor que el máximo permitido, se muestra un mensaje de que el agua está demasiado alcalina y no es apta para consumo humano. Si el pH está dentro del rango permitido, se muestra un mensaje de que el agua es apta para consumo humano.
        mensaje = "El agua está demasiado ácida. No es apta para consumo humano."#se muestra mensaje
    elif tinaco.ph_actual > PH_MAXIMO_BEBIBLE:#SI el pH del tinaco es mayor que el máximo permitido, se muestra un mensaje de que el agua está demasiado alcalina y no es apta para consumo humano.
        mensaje = "El agua está demasiado alcalina. No es apta para consumo humano."
    else:#si el pH del tinaco está dentro del rango permitido, se muestra un mensaje de que el agua es apta para consumo humano.
        mensaje = "El agua está dentro del rango permitido. Es apta para consumo humano."

    contexto = {
        "tinaco": tinaco,
        "tinacos_menu": Tinaco.objects.all(),
        "usuario": request.session["usuario"],
        "mensaje": mensaje,
        "ph_minimo": PH_MINIMO_BEBIBLE,
        "ph_maximo": PH_MAXIMO_BEBIBLE,
        "rango_inicio": int(PH_MINIMO_BEBIBLE / 14 * 100),
        "rango_ancho": int((PH_MAXIMO_BEBIBLE - PH_MINIMO_BEBIBLE) / 14 * 100),
    }
    #Se crea un diccionario llamado contexto que contiene el tinaco, la lista de tinacos, el usuario, el mensaje, los valores de pH mínimo y máximo, y los valores de inicio y ancho del rango de pH para mostrar en la plantilla detalle.html.
    #se renderiza la template detalle.html con el contexto que contiene los datos del tinaco y el usuario
    return render(request, "Agua/detalle.html", contexto)
