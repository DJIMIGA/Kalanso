"""Pages du socle : accueil, contrôle de santé et une démonstration HTMX."""

from django.db import connection
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_safe


def _database_ok() -> bool:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            return cursor.fetchone() == (1,)
    except Exception:  # on veut un simple oui/non, quelle que soit l'erreur
        return False


@require_safe
def home(request):
    return render(request, "core/home.html", {"database_ok": _database_ok()})


@require_safe
def health(request):
    """Contrôle de santé lisible par une machine (GET ou HEAD) : base de données jointe ou non."""
    database_ok = _database_ok()
    return JsonResponse(
        {"statut": "ok" if database_ok else "degrade", "base": "ok" if database_ok else "erreur"},
        status=200 if database_ok else 503,
    )


@require_GET
def demo_time(request):
    """Fragment HTMX : renvoie l'heure du serveur. Refuse les appels qui ne viennent pas d'HTMX."""
    if request.headers.get("HX-Request") != "true":
        return HttpResponseBadRequest("Ce fragment est réservé aux appels HTMX.")
    return render(request, "core/partials/server_time.html", {"now": timezone.localtime()})
