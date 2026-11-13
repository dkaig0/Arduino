# Migración escrita a mano (Django 6.1).
#
# Acompaña el cambio de Usuario a modelo de usuario de Django (AUTH_USER_MODEL).
# Como todos los modelos tienen managed = False, NO cambia ninguna tabla:
# solo actualiza lo que Django sabe de los modelos.
# - El campo password_usuario pasa a llamarse password en Python (lo exige
#   AbstractBaseUser), pero sigue usando la misma columna password_usuario.
# - Se agregan los nombres en español que muestra Django Admin.
#
# Las tablas de Django (auth, admin, sesiones) las crean las migraciones de
# esas aplicaciones al ejecutar "python manage.py migrate".

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Agua', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='usuario',
            old_name='password_usuario',
            new_name='password',
        ),
        migrations.AlterField(
            model_name='usuario',
            name='password',
            field=models.CharField(db_column='password_usuario', max_length=255, verbose_name='contraseña'),
        ),
        migrations.AlterModelOptions(
            name='medicion',
            options={'managed': False, 'ordering': ['-fecha_medicion'], 'verbose_name': 'medición', 'verbose_name_plural': 'mediciones'},
        ),
        migrations.AlterModelOptions(
            name='rol',
            options={'managed': False, 'verbose_name': 'rol', 'verbose_name_plural': 'roles'},
        ),
        migrations.AlterModelOptions(
            name='tinaco',
            options={'managed': False, 'ordering': ['id_tinaco'], 'verbose_name': 'tinaco', 'verbose_name_plural': 'tinacos'},
        ),
        migrations.AlterModelOptions(
            name='ubicacion',
            options={'managed': False, 'verbose_name': 'ubicación', 'verbose_name_plural': 'ubicaciones'},
        ),
        migrations.AlterModelOptions(
            name='usuario',
            options={'managed': False, 'ordering': ['id_usuario'], 'verbose_name': 'usuario', 'verbose_name_plural': 'usuarios'},
        ),
    ]
