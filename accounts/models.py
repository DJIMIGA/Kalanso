"""Compte utilisateur de Kalanso.

Créé dès le socle parce que Django ne permet pas de remplacer le modèle de compte après la
première migration. Les champs métier (école de rattachement, rôle) arrivent dans la PR
« écoles et rôles ».
"""

import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        verbose_name = "utilisateur"
        verbose_name_plural = "utilisateurs"

    def __str__(self) -> str:
        return self.get_full_name() or self.username
