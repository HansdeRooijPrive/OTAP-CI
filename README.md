# OTAP-CI — generieke CI/CD-straat voor kleine web-apps

Herbruikbare GitHub Actions-workflows én de centrale bouwstap voor een
OTAP-straat op GitHub Pages. Elke app is een eigen repo (gemaakt uit een
template), volgt dezelfde conventie en verwijst hierheen. Geen Node nodig —
alles draait op Python.

**Taakverdeling.** Deze repo bepaalt *hoe* er gebouwd, gecontroleerd en
gepubliceerd wordt, en welke afspraken elke app naleeft. De app bepaalt *wat*
er gebouwd wordt: functionaliteit, vormgeving, kleuren en iconen.

## OTAP-model (per app-repo)

| Laag | Branch | Waar | Wie |
|------|--------|------|-----|
| **O**ntwikkel | `development` + lokaal | lokaal (`python build.py`) | ontwikkelaar |
| **T**est | `development` | `…github.io/<repo>/test/`; `verify` + `tests` moeten groen | CI |
| **A**cceptatie | `acceptatie` | `…github.io/<repo>/acceptatie/` | acceptant |
| **P**roductie | `main` | `…github.io/<repo>/` (root) | na expliciet akkoord |

Eén Pages-site per app; de omgevingen zijn paden. Verschillende apps zijn aparte
repo's = aparte origins = automatisch geïsoleerd.

## Platformafspraken

De centrale bouwstap dwingt deze af; een app die ze schendt, bouwt niet.

| Afspraak | Productie | Acceptatie | Test |
|----------|-----------|------------|------|
| Naam (ook onder het icoon op je beginscherm) | `App` | `App acc` | `App test` |
| Opslagsleutel (localStorage/IndexedDB) | `sleutel` | `sleutel.acc` | `sleutel.test` |
| App-icoon `src/icons/icon.<env>.png` | eigen icoon | eigen icoon | eigen icoon |

- De drie iconen **moeten van elkaar verschillen**, bij voorkeur in kleur.
  Welke kleur en welke vormgeving bepaalt de app zelf.
- De kleuren in de app (`app.json` → `theme`) kiest de app ook zelf.

## Centrale bouwstap (v2)

`bouw/otap_build.py` voegt `src/` samen tot één self-contained `index.html` per
omgeving en controleert de afspraken. Een app heeft alleen een dunne ingang:

- `bouw/build.py` — kopieer dit eenmalig naar de root van de app. Het haalt de
  centrale bouwstap op in de versie uit `app.json` (`"platform": "v2"`), lokaal in
  `.otap/` (zet dat in `.gitignore`); in CI zet de workflow `OTAP_CI_DIR`.
- Lokaal en in CI draait daardoor exact dezelfde code.
- Tests van de app kunnen gewoon `import build` gebruiken (`build.build(env)`,
  `build._config()`).

```bash
python build.py                 # productie-build naar index.html
python build.py --env=test      # testvariant
python build.py --check         # afspraken + index.html == build van src/
```

Placeholders die de bouwstap invult:
`{{APP_NAME}}`, `{{APP_NAME_URL}}`, `{{APP_SHORT}}`,
`{{APP_NAME_ENV}}`, `{{APP_NAME_ENV_URL}}`, `{{APP_SHORT_ENV}}`, `{{APP_SHORT_ENV_URL}}`,
`{{ICOON}}`, `{{STORAGE_KEY}}`, `{{ENV}}`, `{{ENV_LABEL}}`,
`{{MERK}}`, `{{MERK_DONKER}}`, `{{MERK_LICHT}}`, en in de romp `{{STYLES}}`, `{{SCRIPT}}`.

## Herbruikbare workflows

| Workflow | Doel |
|----------|------|
| `deploy.yml` | Bouwt main/acceptatie/development en publiceert P/A/T naar Pages |
| `verify.yml` | `build.py --check` — afspraken + index.html moet overeenkomen met src/ |
| `tests.yml`  | Playwright + pytest (indien de app een `tests/`-map heeft) |

Een app roept ze aan met bijv. `uses: HansdeRooijPrive/OTAP-CI/.github/workflows/deploy.yml@v2`.

## Conventie waaraan een app voldoet

```
app.json                 platform, name, short_name, storage_key, theme per omgeving
build.py                 dunne ingang naar de centrale bouwstap (kopie van bouw/build.py)
src/index.template.html  romp met de placeholders hierboven
src/styles.css           eigen stijl, mag {{MERK}} e.d. gebruiken
src/app/NN-*.js          app-code; {{STORAGE_KEY}}, {{ENV}} …
src/vendor/*.js          optionele libraries
src/icons/icon.<env>.png eigen icoon per omgeving (prod/acc/test), onderling verschillend
tests/                   optionele Playwright/pytest-tests
index.html               ingecheckte productie-build (build.py --env=prod)
.github/workflows/       dunne callers naar deze repo
.gitignore               met .otap/
.gitattributes           src/** text eol=lf, maar src/icons/*.png binary
```

Let op die laatste regel: zonder `binary` haalt Git regeleinden uit de PNG-iconen
en zijn ze na vastleggen beschadigd. De bouwstap herkent dat en zegt het erbij.

## Nieuwe app (beheerd via Claude, vanuit de platformsessie)

Nieuwe app = nieuwe repo uit de juiste template (`Prive-App-Template` of
`Ventus-App-Template`) + branches `development` en `acceptatie` + Pages +
branch-regels voor de `github-pages`-omgeving. Naamconventie onder het
persoonlijke account: `Prive-<App>` en `Ventus-<App>`. Daarna krijgt de app een
eigen sessie in de zijbalk, waarin de app verder ontwikkeld wordt.

## Versionering

Callers pinnen een tag (`@v2`); de dunne `build.py` volgt `"platform"` in
`app.json`. Een verbetering binnen een versie komt bij alle apps door de tag te
verplaatsen. Een wijziging die apps moeten overnemen, krijgt een nieuwe versie;
een app stapt over door in één commit de callers en `"platform"` op te hogen.

| Versie | Wat |
|--------|-----|
| `v1` | workflows centraal; bouwstap als kopie in elke app |
| `v2` | bouwstap centraal; afspraken voor naam en icoon per omgeving afgedwongen |
