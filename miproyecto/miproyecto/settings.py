"""
Configuración del proyecto miproyecto.

Aquí se define cómo se conecta a la base de datos, qué aplicaciones se usan,
dónde están los templates y el idioma del sitio.
Archivo generado por 'django-admin startproject' con Django 6.1 y luego ajustado.
Documentación: https://docs.djangoproject.com/en/6.1/ref/settings/
"""

# os permite leer variables de entorno (valores que se definen fuera del código).
import os

# Path permite trabajar con rutas de carpetas sin preocuparse del sistema operativo.
from pathlib import Path

# Carpeta raíz del proyecto (donde está manage.py). Sirve para armar otras rutas.
BASE_DIR = Path(__file__).resolve().parent.parent


# Clave que Django usa para firmar la sesión, las cookies firmadas y los tokens CSRF.
# Se lee de la variable de entorno DJANGO_SECRET_KEY; si no existe se usa la de
# desarrollo. En un sistema real debe definirse la variable y mantenerse en secreto.
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-zu%w)bc#0**6^^9%^qfp64xlv9kvp5s-yr*_a!lzr0-x#+s)zf',
)

# True muestra las páginas de error detalladas. En un sistema real va en False
# (se cambia con la variable de entorno DJANGO_DEBUG=False).
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

# Direcciones desde las que se puede entrar: solo este computador.
ALLOWED_HOSTS = ['localhost', '127.0.0.1']


# Aplicaciones activas en el proyecto.
INSTALLED_APPS = [
    # Panel de administración (/admin/).
    'django.contrib.admin',
    # Sistema de autenticación: login, logout, permisos y cifrado de contraseñas.
    'django.contrib.auth',
    # Registro de los modelos del proyecto; lo necesitan los permisos y el admin.
    'django.contrib.contenttypes',
    # Sesiones guardadas en la base de datos (tabla django_session).
    'django.contrib.sessions',
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
    # Lee y escribe la cookie de sesión (sessionid) y carga la sesión desde la base.
    'django.contrib.sessions.middleware.SessionMiddleware',
    # Tareas comunes, como normalizar las direcciones.
    'django.middleware.common.CommonMiddleware',
    # Protege los formularios contra envíos desde otros sitios (token CSRF).
    'django.middleware.csrf.CsrfViewMiddleware',
    # Deja en request.user la cuenta conectada, a partir de la sesión.
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # Lleva los avisos de una página a la siguiente.
    'django.contrib.messages.middleware.MessageMiddleware',
    # Impide que el sitio se muestre dentro de un marco de otra página.
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# Autenticación
# https://docs.djangoproject.com/en/6.1/topics/auth/customizing/

# El modelo de usuario de Django es Usuario (tabla usuario), no el que trae Django.
AUTH_USER_MODEL = 'Agua.Usuario'

# Backend que revisa usuario y contraseña: acepta el nombre o el correo (Agua/backends.py).
AUTHENTICATION_BACKENDS = ['Agua.backends.NombreOCorreoBackend']

# A dónde manda @login_required a quien no ha iniciado sesión (nombre de la ruta).
LOGIN_URL = 'login'
# A dónde se va después de iniciar sesión, si no se pidió otra página.
LOGIN_REDIRECT_URL = 'dashboard'

# Reglas que debe cumplir toda contraseña nueva (formularios de la app y de Django Admin).
AUTH_PASSWORD_VALIDATORS = [
    {
        # No puede parecerse al nombre de usuario ni al correo.
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        'OPTIONS': {'user_attributes': ('nombre_usuario', 'email_usuario')},
    },
    # Mínimo 8 caracteres.
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    # No puede ser una contraseña de la lista de las más usadas.
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    # No puede ser solo números.
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Caché
# Guarda en la memoria del servidor los intentos fallidos de inicio de sesión
# y los bloqueos temporales de cuentas (ver Agua/bloqueo.py).
# Cada dato se borra solo al vencer su tiempo; al reiniciar el servidor se pierden.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}


# Sesiones
# https://docs.djangoproject.com/en/6.1/topics/http/sessions/

# Los datos de la sesión se guardan en la tabla django_session de MariaDB;
# el navegador solo guarda la cookie "sessionid" con un identificador aleatorio.
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
# Duración de la sesión si se marca "Mantener sesión iniciada": 7 días, en segundos.
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7
# JavaScript no puede leer la cookie de sesión (protege contra robo por XSS).
SESSION_COOKIE_HTTPONLY = True
# La cookie de sesión no viaja en peticiones iniciadas desde otros sitios.
SESSION_COOKIE_SAMESITE = 'Lax'
# Con HTTPS (en producción) estas dos deben ir en True para que las cookies
# solo viajen cifradas. En desarrollo se usa http://127.0.0.1, por eso van en False.
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

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
                # Deja disponibles {{ user }} (la cuenta conectada) y {{ perms }} (sus permisos).
                'django.contrib.auth.context_processors.auth',
                # Deja disponibles los avisos para mostrarlos en base.html.
                'django.contrib.messages.context_processors.messages',
                # Indica si hay que mostrar la ventana de cookies (Agua/context_processors.py).
                'Agua.context_processors.aviso_cookies',
                # Versión de estilos.css, para que el navegador no use una copia vieja.
                'Agua.context_processors.version_css',
            ],
        },
    },
]

# Punto de entrada que usaría un servidor real para ejecutar el sitio.
WSGI_APPLICATION = 'miproyecto.wsgi.application'


# Base de datos
# MariaDB de XAMPP (base "bd"). Las tablas del negocio se crean con bd_tinacos.sql;
# las de Django (auth, admin, sesiones) las crea "python manage.py migrate".
# Se usa un backend propio porque Django 6.1 no acepta MariaDB 10.4.

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
