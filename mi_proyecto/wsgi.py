# -*- coding: utf-8 -*-
import os
import sys

# Añade la ruta de tu proyecto Django
sys.path.append('/var/www/mi_proyecto')
sys.path.append('/var/www/mi_proyecto/mi_proyecto')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()