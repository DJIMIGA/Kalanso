#!/usr/bin/env python
"""Point d'entrée des commandes Django (migrations, tests, serveur de développement)."""

import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kalanso.settings.dev")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
