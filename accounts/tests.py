"""Tests du modèle de compte : clé UUID, mot de passe jamais en clair."""

import uuid

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


def test_le_modele_de_compte_est_celui_de_kalanso():
    assert settings.AUTH_USER_MODEL == "accounts.User"
    assert User.__module__ == "accounts.models"


@pytest.mark.django_db
def test_la_cle_du_compte_est_un_uuid():
    compte = User.objects.create_user(username="awa", password="un-mot-de-passe-long-2026")
    assert isinstance(compte.pk, uuid.UUID)


@pytest.mark.django_db
def test_le_mot_de_passe_est_hache_et_verifiable():
    compte = User.objects.create_user(username="moussa", password="un-mot-de-passe-long-2026")
    compte.refresh_from_db()
    assert "un-mot-de-passe-long-2026" not in compte.password
    assert compte.check_password("un-mot-de-passe-long-2026")
    assert not compte.check_password("autre")


@pytest.mark.django_db
def test_l_admin_django_exige_une_connexion(client):
    reponse = client.get("/admin/")
    assert reponse.status_code == 302
    assert reponse["Location"].startswith("/admin/login/")
