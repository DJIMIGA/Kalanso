"""Tests du socle : pages de base, absence totale de CDN, fichiers statiques, commande dev."""

import json
import re
from io import StringIO
from pathlib import Path
from unittest import mock

import pytest
from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client
from django.urls import reverse

# Fournisseurs externes interdits : les écoles n'ont pas toujours internet.
MOTIFS_CDN = ("cdn.", "unpkg.com", "jsdelivr", "cdnjs", "googleapis", "gstatic", "bootstrapcdn")


# --- Pages -----------------------------------------------------------------------------------


@pytest.mark.django_db
def test_accueil_repond_et_affiche_la_base_connectee(client):
    reponse = client.get(reverse("core:home"))
    assert reponse.status_code == 200
    html = reponse.content.decode()
    assert "Kalanso" in html
    assert "Connectée" in html


@pytest.mark.django_db
def test_accueil_ne_divulgue_pas_la_version_de_django(client):
    import django

    html = client.get(reverse("core:home")).content.decode()
    assert django.get_version() not in html


@pytest.mark.django_db
def test_accueil_ne_charge_que_des_fichiers_locaux(client):
    """Chaque <script src> et <link href> pointe vers /static/, jamais vers l'extérieur."""
    html = client.get(reverse("core:home")).content.decode()
    adresses = re.findall(r"""<(?:script|link)[^>]+?(?:src|href)=["']([^"']+)["']""", html)
    assert adresses, "la page doit charger au moins le CSS et les scripts"
    for adresse in adresses:
        assert adresse.startswith(settings.STATIC_URL), adresse


@pytest.mark.django_db
def test_sante_repond_ok_en_get_et_en_head(client):
    reponse = client.get(reverse("core:health"))
    assert reponse.status_code == 200
    assert reponse.json() == {"statut": "ok", "base": "ok"}
    assert client.head(reverse("core:health")).status_code == 200
    assert client.head(reverse("core:home")).status_code == 200


@pytest.mark.django_db
def test_sante_signale_une_base_injoignable(client):
    with mock.patch("core.views.connection") as connexion:
        connexion.cursor.side_effect = RuntimeError("base injoignable")
        reponse = client.get(reverse("core:health"))
    assert reponse.status_code == 503
    assert reponse.json() == {"statut": "degrade", "base": "erreur"}


@pytest.mark.django_db
def test_demo_heure_repond_a_htmx(client):
    reponse = client.get(reverse("core:demo_time"), headers={"HX-Request": "true"})
    assert reponse.status_code == 200
    assert "Heure du serveur" in reponse.content.decode()


@pytest.mark.django_db
def test_demo_heure_refuse_un_appel_direct(client):
    assert client.get(reverse("core:demo_time")).status_code == 400


@pytest.mark.django_db
def test_les_pages_refusent_post(client):
    for nom in ("core:home", "core:health", "core:demo_time"):
        assert client.post(reverse(nom)).status_code == 405, nom


@pytest.mark.django_db
def test_entetes_de_securite_presents(client):
    reponse = client.get(reverse("core:home"))
    assert reponse["X-Frame-Options"] == "DENY"
    assert reponse["X-Content-Type-Options"] == "nosniff"
    assert reponse["Referrer-Policy"] == "same-origin"


# --- Zéro CDN, fichiers statiques ------------------------------------------------------------


def _sources_html_et_css() -> list[Path]:
    base = settings.BASE_DIR
    dossiers = [
        base / "templates",
        base / "assets",
        base / "static" / "css",
        *base.glob("*/templates"),
    ]
    return [
        f
        for d in dossiers
        if d.exists()
        for f in d.rglob("*")
        if f.suffix in (".html", ".css") and f.is_file()
    ]


def test_aucune_source_html_ou_css_ne_cite_un_cdn():
    fichiers = _sources_html_et_css()
    assert fichiers
    for fichier in fichiers:
        contenu = fichier.read_text(encoding="utf-8").lower()
        for motif in MOTIFS_CDN:
            assert motif not in contenu, f"{fichier.name} fait appel à {motif}"
        if fichier.suffix == ".css":
            assert not re.search(r"""(@import\s+|url\()["']?https?://""", contenu), (
                f"{fichier.name} charge une ressource distante"
            )


@pytest.mark.parametrize(
    "chemin", ["css/app.css", "vendor/htmx.min.js", "vendor/alpine.min.js", "vendor/VERSIONS.json"]
)
def test_les_fichiers_statiques_sont_presents(chemin):
    trouve = finders.find(chemin)
    assert trouve, f"{chemin} manque : lancer `npm run build`"
    assert Path(trouve).stat().st_size > 0


def test_la_source_tailwind_n_est_pas_servie():
    assert finders.find("src/app.css") is None
    assert (settings.BASE_DIR / "assets" / "tailwind" / "app.css").exists()


def test_le_css_compile_contient_les_classes_des_gabarits():
    """Si le CSS n'a pas été recompilé après un changement de gabarit, ce test le signale."""
    css = Path(finders.find("css/app.css")).read_text(encoding="utf-8")
    for classe in ("min-h-full", "bg-slate-50", "text-emerald-700", "sm\\:grid-cols-2"):
        assert f".{classe}" in css, (
            f"classe {classe} absente du CSS compilé : lancer `npm run build`"
        )


def test_les_versions_des_scripts_sont_celles_du_package_json():
    """Le fichier VERSIONS.json (copié par `npm run vendor`) doit suivre package.json."""
    versions = json.loads(Path(finders.find("vendor/VERSIONS.json")).read_text(encoding="utf-8"))
    paquets = json.loads((settings.BASE_DIR / "package.json").read_text(encoding="utf-8"))
    attendu = paquets["devDependencies"]
    assert versions["htmx.min.js"] == attendu["htmx.org"]
    assert versions["alpine.min.js"] == attendu["alpinejs"]


def test_l_application_sert_elle_meme_les_fichiers_statiques_en_developpement(client):
    reponse = client.get(f"{settings.STATIC_URL}css/app.css")
    assert reponse.status_code == 200
    assert reponse["Content-Type"].startswith("text/css")


def test_l_application_sert_les_fichiers_collectes_comme_a_l_ecole(tmp_path, settings):
    """Chemin de production : collectstatic vers STATIC_ROOT puis WhiteNoise sans les finders."""
    settings.STATIC_ROOT = tmp_path
    settings.WHITENOISE_USE_FINDERS = False
    settings.WHITENOISE_AUTOREFRESH = False
    call_command("collectstatic", interactive=False, verbosity=0)
    assert (tmp_path / "css" / "app.css").exists()
    reponse = Client().get(f"{settings.STATIC_URL}css/app.css")  # client neuf : relit les réglages
    assert reponse.status_code == 200
    assert reponse["Content-Type"].startswith("text/css")


# --- Commande dev ----------------------------------------------------------------------------


@pytest.fixture
def commandes_appelees(monkeypatch):
    appels = []
    monkeypatch.setattr(
        "core.management.commands.dev.call_command",
        lambda nom, *args, **kwargs: appels.append((nom, args, kwargs)),
    )
    monkeypatch.delenv("RUN_MAIN", raising=False)
    return appels


def test_dev_refuse_hors_reglages_de_developpement(settings, commandes_appelees):
    settings.DEBUG = False
    with pytest.raises(CommandError):
        call_command("dev")
    assert commandes_appelees == []


def test_dev_migre_puis_lance_le_serveur_en_local(settings, commandes_appelees):
    settings.DEBUG = True
    sortie = StringIO()
    call_command("dev", stdout=sortie)
    assert [appel[0] for appel in commandes_appelees] == ["migrate", "runserver"]
    assert commandes_appelees[1][1] == ("127.0.0.1:8000",)
    assert "http://127.0.0.1:8000/" in sortie.getvalue()
    assert "visibles par tous les postes" not in sortie.getvalue()


def test_dev_reseau_ecoute_partout_et_avertit(settings, commandes_appelees):
    settings.DEBUG = True
    sortie = StringIO()
    call_command("dev", "--reseau", stdout=sortie)
    assert commandes_appelees[1][1] == ("0.0.0.0:8000",)  # noqa: S104
    assert "visibles par tous les postes" in sortie.getvalue()
    assert "http://<ip-du-pc>:8000/" in sortie.getvalue()


def test_dev_affiche_le_port_reellement_choisi(settings, commandes_appelees):
    settings.DEBUG = True
    sortie = StringIO()
    call_command("dev", "127.0.0.1:8765", stdout=sortie)
    assert commandes_appelees[1][1] == ("127.0.0.1:8765",)
    assert "http://127.0.0.1:8765/" in sortie.getvalue()


def test_dev_ne_migre_pas_dans_le_processus_du_rechargeur(
    settings, commandes_appelees, monkeypatch
):
    settings.DEBUG = True
    monkeypatch.setenv("RUN_MAIN", "true")
    call_command("dev", stdout=StringIO())
    assert [appel[0] for appel in commandes_appelees] == ["runserver"]
