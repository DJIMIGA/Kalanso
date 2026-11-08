# Kalanso — consignes pour le code

Produit : gestion scolaire (Mali), même code Django sur le PC de l'école (SQLite, réseau local
en HTTP, souvent sans internet) et dans le cloud (HTTPS ; SQLite pour l'instant, PostgreSQL à
ajouter dans une PR dédiée). Cahier des charges et décisions : document « SaaS gestion
scolaire : cahier des charges MVP ».

## Règles non négociables
- Une fonctionnalité par PR, petite. Pas de dump massif de code.
- Chaque règle métier a ses tests (pytest), écrits avec le code. CI verte obligatoire.
- Chaque PR : explication en français sans jargon, scénario de test manuel pas à pas, résultat
  des tests, ce qui n'est pas testé, et la commande pour lancer (`uv run manage.py dev`).
- Rien hors du périmètre V1 sans décision du propriétaire du projet.
- Aucune ressource externe (CDN, polices Google, scripts distants). Tout vient de `static/`.
- Permissions vérifiées côté serveur, jamais seulement masquées dans l'interface.
- Isolation par école : toute requête filtrée par école côté serveur, testée.

## Conventions
- Identifiants de code en anglais (modèles, fonctions, vues, noms de routes, blocs de gabarit,
  variables de contexte, apps) ; chemins d'URL, textes d'interface, messages, commentaires et
  docstrings en français. Les noms de fonctions de test peuvent être en français (ils se lisent
  comme une spécification).
- Clé primaire UUID sur toutes les tables métier, plus `created_at` / `updated_at`.
  Montants en entiers FCFA. Numéros lisibles (matricule, reçu) via un compteur par école.
- Rien ne se rattache à l'élève directement : tout passe par l'inscription (élève + classe + année).
- Pas de suppression de données ayant un historique : statut « sorti » ou annulation tracée.
- Stack : Django 5.2 LTS, templates + HTMX + Alpine, Tailwind v4 compilé depuis
  `assets/tailwind/app.css` (`npm run build`, résultat commité dans `static/`).
  Python fixé par `.python-version` ; dépendances gérées par `uv` (`uv add`, `uv.lock` commité).

## Commandes
- Lancer : `uv run manage.py dev` (`--reseau` pour tester depuis un autre poste)
- Tests : `uv run pytest` · Lint : `uv run ruff check . && uv run ruff format --check .`
- Assets : `npm ci && npm run build` puis commiter `static/`
- Réglages prod : `DJANGO_SETTINGS_MODULE=kalanso.settings.prod` (variables dans le README).
