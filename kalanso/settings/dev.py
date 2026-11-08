"""Réglages du poste de développement et des tests automatiques. Ne jamais déployer avec."""

from . import *  # noqa: F403

DEBUG = True

# Clé volontairement fixe et publique : uniquement pour le développement local.
SECRET_KEY = "dev-only-insecure-key-ne-pas-utiliser-en-production"  # noqa: S105

# Autorise l'accès depuis d'autres postes du réseau local (http://<ip-du-pc>:8000).
ALLOWED_HOSTS = ["*"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Pas de collecte en développement : WhiteNoise sert static/ directement, même pendant les tests
# (pytest-django force DEBUG=False, d'où les deux réglages explicites).
STATIC_ROOT = None
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True
