# Kalanso

Gestion scolaire pour les groupes scolaires du Mali : inscriptions, frais et reçus, notes et
bulletins. Le même logiciel tourne sur un PC de l'école (sans internet, en réseau local) et dans
le cloud.

Ce dépôt en est au **socle technique** : pas encore de module métier. Le cahier des charges et
les décisions d'architecture sont dans le document « SaaS gestion scolaire : cahier des charges MVP ».

## Lancer en une commande

1. Installer [uv](https://docs.astral.sh/uv/) une seule fois.
   - Windows (PowerShell) : `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
   - macOS / Linux : `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. Dans le dossier du projet :

   ```
   uv run manage.py dev
   ```

   La **toute première fois**, il faut internet : uv télécharge Python (la version fixée par le
   fichier `.python-version`) et les bibliothèques, quelques dizaines de Mo. Ensuite l'application
   fonctionne entièrement hors ligne. La commande prépare la base de données puis démarre le
   serveur. Ouvrir <http://127.0.0.1:8000/>.

Aucune installation de Node n'est nécessaire pour lancer l'application : le CSS compilé et les
scripts (HTMX, Alpine) sont déjà dans `static/` et sont servis par l'application elle-même.

### Tester depuis un autre poste du réseau

```
uv run manage.py dev --reseau
```

Puis, sur l'autre poste (ou un téléphone sur le même wifi) : `http://<ip-du-pc>:8000/`.
Sous Windows, l'adresse du PC s'obtient avec `ipconfig` (ligne « Adresse IPv4 »), et il faut
accepter la fenêtre du pare-feu Windows au premier lancement (« Réseaux privés », « Autoriser »).
Ce mode affiche des pages d'erreur détaillées à tout le réseau : c'est un mode de test, pas un
mode pour des données réelles.

### Postes clients

Le style exige un navigateur récent : Microsoft Edge ou Chrome **111 ou plus** (mars 2023),
Firefox 128 ou plus. Les PC sous Windows 7 ou 8.1 (Edge bloqué en version 109) afficheront la
page sans mise en forme. Vérifier la version dans `edge://settings/help` avant la mise en service.

## Vérifier

```
uv run pytest            # tests automatiques
uv run ruff check .      # erreurs et style Python
uv run ruff format .     # mise en forme
```

La CI (GitHub Actions) rejoue tout cela sur chaque PR.

### À faire une fois sur GitHub

Un workflow ne bloque jamais une fusion par lui-même. Pour que GitHub refuse de fusionner une PR
dont la CI est rouge : Settings → Branches → Add branch ruleset (ou Add rule) sur `main` →
cocher « Require status checks to pass » et choisir le contrôle **CI**.

## Modifier le style ou les scripts

Seulement si l'on touche aux classes Tailwind des gabarits ou aux versions de HTMX / Alpine :

```
npm ci            # une fois
npm run build     # recopie static/vendor/ puis recompile static/css/app.css
```

Puis commiter `static/`. La CI vérifie que le résultat commité correspond bien aux sources
(`assets/tailwind/app.css` et `templates/`). `npm run watch:css` recompile en continu.

Toute modification des dépendances Python passe par `uv add` (ou `uv lock`) : la CI refuse un
`uv.lock` en retard sur `pyproject.toml`.

## Déployer (serveur de l'école ou cloud)

Les réglages de production se choisissent avec la variable `DJANGO_SETTINGS_MODULE` ; sans elle,
`manage.py` utilise les réglages de développement.

| Variable | Rôle |
| --- | --- |
| `DJANGO_SETTINGS_MODULE` | Obligatoire : `kalanso.settings.prod`. |
| `DJANGO_SECRET_KEY` | Obligatoire. Clé aléatoire d'au moins 50 caractères, propre à chaque installation. |
| `KALANSO_ALLOWED_HOSTS` | Obligatoire. Adresses acceptées, séparées par des virgules, **sans le port** (ex. `localhost,192.168.1.20`). |
| `KALANSO_HTTPS` | `1` en cloud derrière HTTPS (redirection, cookies sécurisés, HSTS). Absent ou `0` à l'école (HTTP sur le réseau local). |
| `KALANSO_DB_PATH` | Emplacement du fichier SQLite. |

Windows (PowerShell) :

```
$env:DJANGO_SETTINGS_MODULE = "kalanso.settings.prod"
$env:DJANGO_SECRET_KEY = "<clé longue et aléatoire>"
$env:KALANSO_ALLOWED_HOSTS = "localhost,192.168.1.20"
uv run manage.py migrate
uv run manage.py collectstatic --no-input
uv run manage.py check --deploy
```

macOS / Linux : mêmes commandes avec `export DJANGO_SETTINGS_MODULE=kalanso.settings.prod`, etc.

Le **démarrage du serveur en production** (service Windows, serveur WSGI, installeur) n'est pas
encore dans ce dépôt : c'est un chantier à part, prévu après les modules métier. `manage.py dev`
n'est pas fait pour cela.

## Organisation du code

| Dossier | Contenu |
| --- | --- |
| `kalanso/` | Réglages (`settings/`), routes de premier niveau, points d'entrée WSGI/ASGI |
| `core/` | Socle : page d'accueil, contrôle de santé `/sante/`, commande `dev` |
| `accounts/` | Compte utilisateur (clé UUID). Les rôles et l'école de rattachement arrivent par PR dédiée |
| `templates/` | Gabarits HTML (Django + HTMX + Alpine) |
| `assets/tailwind/` | Source Tailwind (non servie) ; `static/css/` et `static/vendor/` sont les fichiers compilés et servis |
| `.github/workflows/` | CI |

## Règles de travail

- Une fonctionnalité par PR, petite. Chaque PR explique en français ce qui change, donne un
  scénario de test manuel et le résultat des tests automatiques.
- Chaque règle métier a ses tests, écrits avec le code. La CI bloque si un test échoue.
- Aucune ressource chargée depuis internet (CDN) : les écoles sont souvent hors ligne.
- Rien hors du périmètre V1 sans décision.
