# otap-ci — generieke CI/CD-straat voor kleine web-apps

Herbruikbare GitHub Actions-workflows voor een OTAP-straat op GitHub Pages.
Elke app is een eigen repo (gemaakt uit een template), volgt dezelfde conventie
en verwijst hierheen voor de build/deploy/test-logica. Geen Node nodig — alles
draait op Python.

## OTAP-model (per app-repo)

| Laag | Branch | Waar | Wie |
|------|--------|------|-----|
| **O**ntwikkel | `development` + lokaal | lokaal (`python build.py`) | ontwikkelaar |
| **T**est | `development` | automatische poort: `verify` + `tests` moeten groen | CI |
| **A**cceptatie | `acceptatie` | `…github.io/<repo>/acceptatie/` | acceptant |
| **P**roductie | `main` | `…github.io/<repo>/` (root) | na akkoord |

Eén Pages-site per app; de omgevingen zijn paden. `build.py --env=<prod|acc|test>`
zet per omgeving de thema-kleur en de **opslagsleutels** (localStorage/IndexedDB),
zodat T/A/P elkaars data niet raken. Verschillende apps zijn aparte repo's =
aparte origins = automatisch geïsoleerd.

## Herbruikbare workflows

| Workflow | Doel |
|----------|------|
| `deploy.yml` | Bouwt main/acceptatie/development en publiceert P/A/T naar Pages |
| `verify.yml` | `build.py --check` — index.html moet overeenkomen met src/ |
| `tests.yml`  | Playwright + pytest (indien de app een `tests/`-map heeft) |

Een app roept ze aan met bijv. `uses: HansdeRooijPrive/otap-ci/.github/workflows/deploy.yml@v1`.

## Conventie waaraan een app voldoet

```
app.json                 naam, short_name, storage_key, theme per omgeving
build.py                 env-bewuste build (uit de template)
src/index.template.html  romp met {{APP_NAME}}, {{ENV_LABEL}}, {{STYLES}}, {{SCRIPT}}
src/styles.css           met {{MERK}} / {{MERK_DONKER}} / {{MERK_LICHT}}
src/app/NN-*.js          app-code als IIFE-fragmenten; {{STORAGE_KEY}}, {{ENV}} …
src/vendor/*.js          optionele libraries
tests/                   optionele Playwright/pytest-tests
index.html               ingecheckte productie-build (build.py --env=prod)
.github/workflows/       dunne callers naar deze repo
```

## Nieuwe app (beheerd via Claude)

Nieuwe app = nieuwe repo uit de juiste template + branches + Pages + omgevingen.
Naamconventie onder het persoonlijke account:
`prive-<app>` en `ventus-<app>`.

## Versionering

Callers pinnen een tag (`@v1`). Een verbetering hier komt beschikbaar voor alle
apps door de tag te verplaatsen of te verhogen.
