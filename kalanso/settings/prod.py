"""Réglages du serveur de l'école (PC Windows, réseau local en HTTP) et du cloud (HTTPS).

À sélectionner avec ``DJANGO_SETTINGS_MODULE=kalanso.settings.prod`` (sans cela, ``manage.py``
utilise les réglages de développement).

Variables d'environnement :
- ``DJANGO_SECRET_KEY`` (obligatoire) : clé secrète longue et aléatoire, propre à chaque
  installation.
- ``KALANSO_ALLOWED_HOSTS`` (obligatoire) : noms ou adresses acceptés, séparés par des virgules,
  SANS le port (exemple ``localhost,192.168.1.20`` à l'école, ``app.kalanso.ml`` en cloud).
- ``KALANSO_HTTPS`` : ``1`` en cloud derrière HTTPS. Absent ou ``0`` sur le serveur local de
  l'école, joint en HTTP simple sur le réseau de l'école.
- ``KALANSO_DB_PATH`` : emplacement du fichier SQLite (voir réglages communs).
"""

import os

from django.core.exceptions import ImproperlyConfigured

from . import *  # noqa: F403

DEBUG = False

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if len(SECRET_KEY) < 50:
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY doit être définie (au moins 50 caractères aléatoires)."
    )


def _lire_booleen(nom: str) -> bool:
    valeur = os.environ.get(nom, "0").strip().lower()
    if valeur in {"1", "true", "yes", "on", "oui"}:
        return True
    if valeur in {"0", "false", "no", "off", "non", ""}:
        return False
    raise ImproperlyConfigured(f"{nom} doit valoir 1 ou 0 (valeur reçue : « {valeur} »).")


def _lire_hotes(nom: str) -> list[str]:
    hotes = [h.strip() for h in os.environ.get(nom, "").split(",") if h.strip()]
    if not hotes:
        raise ImproperlyConfigured(
            f"{nom} doit lister les adresses acceptées, séparées par des virgules."
        )
    for hote in hotes:
        # Django compare l'hôte sans son port : « 192.168.1.20:8000 » refuserait toute requête.
        reste = hote.rsplit("]", 1)[-1] if hote.startswith("[") else hote
        if ":" in reste:
            sans_port = hote.rsplit(":", 1)[0]
            raise ImproperlyConfigured(
                f"{nom} : indiquez « {sans_port} » sans le port (IPv6 entre crochets)."
            )
    return hotes


ALLOWED_HOSTS = _lire_hotes("KALANSO_ALLOWED_HOSTS")

# Mode cloud (HTTPS) : redirection, cookies sécurisés et HSTS. Mode école (HTTP local) : désactivé,
# sinon les postes ne pourraient plus se connecter au PC serveur.
HTTPS_MODE = _lire_booleen("KALANSO_HTTPS")

# Confiance CSRF : les mêmes adresses, avec leur schéma (et le port 8000 à l'école).
_scheme = "https" if HTTPS_MODE else "http"
_hotes_nommables = [h for h in ALLOWED_HOSTS if not h.startswith((".", "*"))]
CSRF_TRUSTED_ORIGINS = [f"{_scheme}://{h}" for h in _hotes_nommables]
if not HTTPS_MODE:
    CSRF_TRUSTED_ORIGINS += [f"http://{h}:8000" for h in _hotes_nommables]

SECURE_SSL_REDIRECT = HTTPS_MODE
SESSION_COOKIE_SECURE = HTTPS_MODE
CSRF_COOKIE_SECURE = HTTPS_MODE
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365 if HTTPS_MODE else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = HTTPS_MODE
SECURE_HSTS_PRELOAD = HTTPS_MODE
if HTTPS_MODE:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# La sonde de santé de l'hébergeur interroge souvent le serveur en HTTP direct : pas de redirection.
SECURE_REDIRECT_EXEMPT = [r"^sante/$"]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": os.environ.get("KALANSO_LOG_LEVEL", "INFO")},
}
