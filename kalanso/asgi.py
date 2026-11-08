"""Point d'entrée ASGI (non utilisé en V1, conservé pour la forme standard Django)."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kalanso.settings.prod")

application = get_asgi_application()
