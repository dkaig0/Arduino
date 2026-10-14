"""
Configuración del proyecto miproyecto.

Aquí se define cómo se conecta a la base de datos, qué aplicaciones se usan,
dónde están los templates y el idioma del sitio.
Archivo generado por 'django-admin startproject' con Django 6.1 y luego ajustado.
Documentación: https://docs.djangoproject.com/en/6.1/ref/settings/
"""

# Path permite trabajar con rutas de carpetas sin preocuparse del sistema operativo.
from pathlib import Path

# Carpeta raíz del proyecto (donde está manage.py). Sirve para armar otras rutas.
BASE_DIR = Path(__file__).resolve().parent.parent


# Clave que Django usa para firmar las cookies de sesión.
# En un sistema real debe mantenerse en secreto; aquí es un proyecto de clase.
SECRET_KEY = 'django-insecure-zu%w)bc#0**6^^9%^qfp64xlv9kvp5s-yr*_a!lzr0-x#+s)zf'

# True muestra las páginas de error detalladas. En un sistema real va en False.
DEBUG = True

# Direcciones desde las que se puede entrar. Vacío significa solo este computador.
ALLOWED_HOSTS = []


# Aplicaciones activas en el proyecto.
INSTALLED_APPS = [
    # Sistema de avisos ("Usuario creado", "Medición eliminada").
    'django.contrib.messages',
    # Permite servir los archivos estáticos, como la hoja de estilos.
    'django.contrib.staticfiles',
    # La aplicación propia de este proyecto.
    'Agua',
]

# Capas por las que pasa cada visita antes y después de llegar a la vista.
MIDDLEWARE = [
    # Agrega protecciones básicas de seguridad a las respuestas.
    'django.middleware.security.SecurityMiddleware',
    # Lee y escribe la cookie de sesión (quién inició sesión).
    'django.contrib.sessions.middleware.SessionMiddleware',
    # Tareas comunes, como normalizar las direcciones.
    'django.middleware.common.CommonMiddleware',
    # Protege los formularios contra envíos desde otros sitios (token CSRF).
    'django.middleware.csrf.CsrfViewMiddleware',
    # Lleva los avisos de una página a la siguiente.
    'django.contrib.messages.middleware.MessageMiddleware',
    # Impide que el sitio se muestre dentro de un marco de otra página.
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# La sesión se guarda como JSON firmado en la cookie del navegador,
# no en base de datos ni en memoria del servidor.
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'

# Archivo donde Django empieza a buscar las rutas del sitio.
ROOT_URLCONF = 'miproyecto.urls'

# Configuración del sistema de plantillas HTML.
TEMPLATES = [
    {
        # Motor de plantillas propio de Django.
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Carpetas extra de templates; vacío porque están dentro de la aplicación.
        'DIRS': [],
        # True hace que Django busque en la carpeta templates de cada aplicación.
        'APP_DIRS': True,
        'OPTIONS': {
            # Datos que quedan disponibles en todas las plantillas.
            'context_processors': [
                # Deja disponible el objeto request.
                'django.template.context_processors.request',
                # Deja disponibles los avisos para mostrarlos en base.html.
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Punto de entrada que usaría un servidor real para ejecutar el sitio.
WSGI_APPLICATION = 'miproyecto.wsgi.application'


# Base de datos
# MariaDB de XAMPP (base "bd", creada con el script SQL del modelo).
# Se usa un backend propio porque Django 6.1 no acepta MariaDB 10.4.
# El inicio de sesión no usa tablas: vive en la cookie de sesión.

DATABASES = {
    # "default" es la conexión que se usa si no se indica otra.
    'default': {
        # Backend propio, definido en miproyecto/mariadb_xampp/base.py.
        'ENGINE': 'miproyecto.mariadb_xampp',
        # Nombre de la base en phpMyAdmin.
        'NAME': 'bd',
        # Usuario de MariaDB; en XAMPP viene root sin contraseña.
        'USER': 'root',
        'PASSWORD': '',
        # El servidor corre en este mismo computador.
        'HOST': '127.0.0.1',
        # Puerto por defecto de MariaDB y MySQL.
        'PORT': '3306',
        'OPTIONS': {
            # Codificación que admite tildes y la letra ñ.
            'charset': 'utf8mb4',
            # Modo estricto: MariaDB avisa en vez de recortar datos en silencio.
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}


# Idioma y zona horaria
# https://docs.djangoproject.com/en/6.1/topics/i18n/

# Español de Chile: los mensajes de Django salen en español.
LANGUAGE_CODE = 'es-cl'

# Zona horaria usada para mostrar y guardar las fechas.
TIME_ZONE = 'America/Santiago'

# Activa el sistema de traducciones.
USE_I18N = True

# Fechas en hora local, igual que las muestra phpMyAdmin.
USE_TZ = False


# Archivos estáticos (CSS, JavaScript, imágenes)
# https://docs.djangoproject.com/en/6.1/howto/static-files/

# Dirección desde la que se sirven; por ejemplo /static/Agua/estilos.css.
STATIC_URL = 'static/'


# Correo
# https://docs.djangoproject.com/en/6.1/topics/email/#topic-email-configuration

MAILERS = {
    'default': {
        # Los correos se escriben en la consola en vez de enviarse de verdad.
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}
