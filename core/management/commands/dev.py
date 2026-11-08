"""``manage.py dev`` : prépare la base puis lance le serveur de développement, en une commande."""

import os

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

ADRESSE_LOCALE = "127.0.0.1:8000"
ADRESSE_RESEAU = "0.0.0.0:8000"  # noqa: S104 - volontaire, derrière l'option --reseau et un avertissement
HOTES_LOCAUX = {"", "127.0.0.1", "localhost", "::1", "[::1]"}


class Command(BaseCommand):
    help = "Applique les migrations puis démarre le serveur de développement (DEBUG uniquement)."

    def add_arguments(self, parser):
        parser.add_argument(
            "adresse",
            nargs="?",
            default=None,
            help=f"Adresse d'écoute, par défaut {ADRESSE_LOCALE} (ce PC seulement).",
        )
        parser.add_argument(
            "--reseau",
            action="store_true",
            help="Écouter sur toutes les interfaces (test depuis un autre poste du réseau local).",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError(
                "La commande dev ne fonctionne qu'avec les réglages de développement "
                "(kalanso.settings.dev)."
            )
        adresse = options["adresse"] or (ADRESSE_RESEAU if options["reseau"] else ADRESSE_LOCALE)
        hote, _, port = adresse.rpartition(":")
        if not port:  # seul un port a été donné (ex. « 8080 ») : Django écoute alors en local
            hote, port = "", adresse

        # Le rechargeur relance ce processus avec RUN_MAIN=true : migration et messages une fois.
        if os.environ.get("RUN_MAIN") != "true":
            call_command("migrate", interactive=False, verbosity=1)
            self.stdout.write(self.style.SUCCESS("Base prête."))
            self.stdout.write(f"Ouvrez http://127.0.0.1:{port}/ dans votre navigateur.")
            if hote not in HOTES_LOCAUX:
                self.stdout.write(
                    self.style.WARNING(
                        "Mode développement ouvert au réseau : les pages d'erreur détaillées "
                        "sont visibles par tous les postes du réseau. Pas de données réelles ici."
                    )
                )
                self.stdout.write(
                    f"Depuis un autre poste : http://<ip-du-pc>:{port}/ (sous Windows, "
                    "« ipconfig » donne l'adresse IPv4 ; accepter la fenêtre du pare-feu)."
                )
        call_command("runserver", adresse)
