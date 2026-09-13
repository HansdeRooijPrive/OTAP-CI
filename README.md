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

### Eigen waarden per omgeving: `waarden` in `app.json`

Moet een app naast de opslagsleutel nog andere namen per omgeving scheiden (een
IndexedDB-database, een bestandsnaam, een URL-gecodeerde kleur), dan kan dat met
eigen placeholders:

```json
"waarden": {
  "OMG_SUFFIX": { "prod": "",          "acc": "-acc",      "test": "-test" },
  "THEMA_URL":  { "prod": "%23cc0000", "acc": "%23b45309", "test": "%230f7a45" }
}
```

Daarmee wordt `{{OMG_SUFFIX}}` en `{{THEMA_URL}}` overal ingevuld waar de gewone
placeholders ook werken. De bouwstap stopt als een naam niet uit HOOFDLETTERS,
cijfers en `_` bestaat, botst met een ingebouwde placeholder, of niet voor alle drie
de omgevingen is opgegeven. Zo kan een bestaande app haar productienamen letterlijk
behouden (bijv. `kilometerdeclaratie{{OMG_SUFFIX}}` → `kilometerdeclaratie`).

### Losse bestanden: `public/`

Heeft een app bestanden die naast `index.html` moeten staan (routedata, een
service worker, een manifest), dan horen die in `public/`. De bouwstap kopieert
die map per omgeving mee naar de uitvoermap (alleen bij `--out` naar een andere
map dan de app zelf). In tekstbestanden (`.js`, `.json`, `.webmanifest`, `.html`,
`.css`, `.txt`, `.svg`, `.xml`) worden dezelfde placeholders ingevuld; andere
bestanden worden ongewijzigd gekopieerd.

Service workers: laat cachenamen beginnen met `{{STORAGE_KEY}}-` zodat omgevingen
geen caches delen (caches gelden voor het hele domein, niet per pad), en laat de
productie-worker verzoeken onder `acceptatie/` en `test/` negeren.

### Branches die nog niet op het platform staan

Heeft een branch geen `build.py` maar wel een `index.html` (bijvoorbeeld `main`
tijdens het onboarden van een bestaande app), dan publiceert `deploy.yml` die
branch ongewijzigd, zonder de verborgen bestanden en `README.md`. In het log staat
dan een melding. Zo blijft productie gewoon online terwijl `development` al op het
platform draait.

## Herbruikbare workflows

| Workflow | Doel |
|----------|------|
| `deploy.yml` | Bouwt main/acceptatie/development en publiceert P/A/T naar Pages |
| `verify.yml` | `build.py --check` — afspraken + index.html moet overeenkomen met src/ |
| `tests.yml`  | Playwright + pytest (indien de app een `tests/`-map heeft) |

Een app roept ze aan met bijv. `uses: HansdeRooijPrive/OTAP-CI/.github/workflows/deploy.yml@v2`.

**Rechten voor `deploy.yml`.** De aanroepende workflow van de app geeft:

```yaml
permissions:
  contents: write   # voor de losse publicatie-commit (zie hieronder)
  pages: write
  id-token: write
```

Waarom `contents: write`: GitHub Pages activeert geen publicatie van een commit
die al live staat vanaf een andere branch. Bij doorzetten (development →
acceptatie → main) is dat precies zo, en dan bleef acceptatie de oude versie
tonen. `deploy.yml` maakt daarom per publicatie een losse commit met exact
dezelfde inhoud en publiceert daarmee; er wordt geen branch verplaatst. Zonder
`contents: write` publiceert de workflow zoals vroeger, met een waarschuwing.

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
