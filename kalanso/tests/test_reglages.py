"""Réglages de production : clé obligatoire, deux modes (école en HTTP, cloud en HTTPS)."""

import importlib
import sys

import pytest
from django.core.exceptions import ImproperlyConfigured

CLE = "x" * 60
VARIABLES = ("DJANGO_SECRET_KEY", "KALANSO_ALLOWED_HOSTS", "KALANSO_HTTPS")


@pytest.fixture
def charger_prod(monkeypatch):
    """Importe kalanso.settings.prod avec l'environnement donné, puis nettoie sys.modules."""

    def _charger(**env):
        for nom in VARIABLES:
            monkeypatch.delenv(nom, raising=False)
        for nom, valeur in env.items():
            monkeypatch.setenv(nom, valeur)
        sys.modules.pop("kalanso.settings.prod", None)
        return importlib.import_module("kalanso.settings.prod")

    yield _charger
    sys.modules.pop("kalanso.settings.prod", None)


def test_prod_refuse_de_demarrer_sans_cle_secrete(charger_prod):
    with pytest.raises(ImproperlyConfigured):
        charger_prod(KALANSO_ALLOWED_HOSTS="localhost")


def test_prod_refuse_une_cle_trop_courte(charger_prod):
    with pytest.raises(ImproperlyConfigured):
        charger_prod(DJANGO_SECRET_KEY="courte", KALANSO_ALLOWED_HOSTS="localhost")


def test_prod_refuse_de_demarrer_sans_hotes(charger_prod):
    with pytest.raises(ImproperlyConfigured):
        charger_prod(DJANGO_SECRET_KEY=CLE)


@pytest.mark.parametrize(
    "hotes", ["192.168.1.20:8000", "localhost,192.168.1.20:8000", "[::1]:8000"]
)
def test_prod_refuse_un_hote_avec_port_et_explique(hotes, charger_prod):
    with pytest.raises(ImproperlyConfigured, match="sans le port"):
        charger_prod(DJANGO_SECRET_KEY=CLE, KALANSO_ALLOWED_HOSTS=hotes)


def test_prod_accepte_une_adresse_ipv6_entre_crochets(charger_prod):
    prod = charger_prod(DJANGO_SECRET_KEY=CLE, KALANSO_ALLOWED_HOSTS="[::1],localhost")
    assert prod.ALLOWED_HOSTS == ["[::1]", "localhost"]


def test_prod_mode_ecole_reste_en_http(charger_prod):
    """À l'école, les postes se connectent en http://<ip>:8000 : pas de redirection HTTPS."""
    prod = charger_prod(DJANGO_SECRET_KEY=CLE, KALANSO_ALLOWED_HOSTS="localhost, 192.168.1.20")
    assert prod.DEBUG is False
    assert prod.ALLOWED_HOSTS == ["localhost", "192.168.1.20"]
    assert prod.SECURE_SSL_REDIRECT is False
    assert prod.SESSION_COOKIE_SECURE is False
    assert prod.SECURE_HSTS_SECONDS == 0
    assert "http://192.168.1.20:8000" in prod.CSRF_TRUSTED_ORIGINS
    assert "http://localhost" in prod.CSRF_TRUSTED_ORIGINS


def test_prod_mode_cloud_impose_https(charger_prod):
    prod = charger_prod(
        DJANGO_SECRET_KEY=CLE, KALANSO_ALLOWED_HOSTS="app.exemple.ml", KALANSO_HTTPS="1"
    )
    assert prod.SECURE_SSL_REDIRECT is True
    assert prod.SESSION_COOKIE_SECURE is True
    assert prod.CSRF_COOKIE_SECURE is True
    assert prod.SECURE_HSTS_SECONDS >= 31536000
    assert prod.SECURE_PROXY_SSL_HEADER == ("HTTP_X_FORWARDED_PROTO", "https")
    assert prod.CSRF_TRUSTED_ORIGINS == ["https://app.exemple.ml"]


def test_prod_mode_cloud_laisse_la_sonde_de_sante_en_http(charger_prod):
    prod = charger_prod(
        DJANGO_SECRET_KEY=CLE, KALANSO_ALLOWED_HOSTS="app.exemple.ml", KALANSO_HTTPS="1"
    )
    assert prod.SECURE_REDIRECT_EXEMPT == [r"^sante/$"]


@pytest.mark.parametrize("valeur", ["1", "true", "TRUE", "yes", "on", "oui"])
def test_kalanso_https_accepte_les_valeurs_vraies_courantes(valeur, charger_prod):
    prod = charger_prod(
        DJANGO_SECRET_KEY=CLE, KALANSO_ALLOWED_HOSTS="app.exemple.ml", KALANSO_HTTPS=valeur
    )
    assert prod.HTTPS_MODE is True


@pytest.mark.parametrize("valeur", ["0", "false", "no", "off", "non", ""])
def test_kalanso_https_accepte_les_valeurs_fausses_courantes(valeur, charger_prod):
    prod = charger_prod(
        DJANGO_SECRET_KEY=CLE, KALANSO_ALLOWED_HOSTS="localhost", KALANSO_HTTPS=valeur
    )
    assert prod.HTTPS_MODE is False


def test_kalanso_https_refuse_une_valeur_inconnue(charger_prod):
    with pytest.raises(ImproperlyConfigured, match="KALANSO_HTTPS"):
        charger_prod(
            DJANGO_SECRET_KEY=CLE, KALANSO_ALLOWED_HOSTS="localhost", KALANSO_HTTPS="peut-etre"
        )


def test_les_reglages_communs_ne_dependent_pas_d_internet():
    from kalanso import settings as communs

    assert communs.STATIC_URL == "/static/"
    assert communs.STATICFILES_DIRS == [communs.BASE_DIR / "static"]


def test_sqlite_est_regle_pour_plusieurs_postes():
    """Plusieurs postes écriront en même temps : attente de verrou et transactions immédiates."""
    from kalanso import settings as communs

    options = communs.DATABASES["default"]["OPTIONS"]
    assert options["timeout"] >= 10
    assert options["transaction_mode"] == "IMMEDIATE"
    assert "journal_mode=WAL" in options["init_command"]
