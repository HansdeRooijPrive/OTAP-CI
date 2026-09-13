#!/usr/bin/env python3
"""
OTAP-CI — centrale bouwstap (v2).

Voegt de src/ van een app samen tot één self-contained index.html per omgeving
(prod/acc/test) en bewaakt de platformafspraken. Apps roepen dit aan via hun
dunne build.py; lokaal en in CI draait dus exact dezelfde code.

Platformafspraken (hard, de build faalt anders):
  - naam per omgeving: productie kaal, acceptatie " acc", test " test"
    (zichtbaar onder het icoon op je beginscherm)
  - opslagsleutel per omgeving: kaal / .acc / .test
  - drie app-iconen, src/icons/icon.<prod|acc|test>.png, die onderling verschillen

Wat de app zelf bepaalt: kleuren (app.json "theme"), vormgeving en de iconen zelf.
Bij voorkeur verschillen de iconen in kleur; dat is een aanbeveling, geen eis.
"""
import argparse
import base64
import glob
import json
import os
import sys
import urllib.parse

ENVS = ("prod", "acc", "test")
SUFFIX = {"prod": "", "acc": ".acc", "test": ".test"}
LABEL = {"prod": "", "acc": "ACCEPTATIE", "test": "TEST"}
NAAM_SUFFIX = {"prod": "", "acc": " acc", "test": " test"}
PNG_HANDTEKENING = b"\x89PNG\r\n\x1a\n"


class PlatformFout(SystemExit):
    """Een platformafspraak is geschonden; de build stopt met een uitleg."""

    def __init__(self, melding):
        super().__init__("PLATFORMFOUT: " + melding)


def _lees(app, rel):
    with open(os.path.join(app, rel), encoding="utf-8") as f:
        return f.read()


def config(app):
    cfg = json.loads(_lees(app, "app.json"))
    for veld in ("name", "storage_key"):
        if not cfg.get(veld):
            raise PlatformFout("app.json mist het verplichte veld %r" % veld)
    return cfg


def _theme(cfg, env):
    t = cfg.get("theme", {})
    kleur = dict(t.get("prod", {}))
    kleur.update(t.get(env, {}))
    return kleur


def iconen(app):
    """Leest de drie iconen en controleert de afspraak: aanwezig, PNG, verschillend."""
    gelezen = {}
    for env in ENVS:
        pad = os.path.join(app, "src", "icons", "icon.%s.png" % env)
        if not os.path.exists(pad):
            raise PlatformFout(
                "icoon ontbreekt: src/icons/icon.%s.png. Elke omgeving heeft een eigen "
                "icoon nodig, zodat je ze op je beginscherm uit elkaar houdt." % env)
        with open(pad, "rb") as f:
            data = f.read()
        if not data.startswith(PNG_HANDTEKENING):
            raise PlatformFout("src/icons/icon.%s.png is geen PNG-bestand" % env)
        gelezen[env] = data
    for i, a in enumerate(ENVS):
        for b in ENVS[i + 1:]:
            if gelezen[a] == gelezen[b]:
                raise PlatformFout(
                    "de iconen van %s en %s zijn identiek. Ze moeten verschillen, bij "
                    "voorkeur in kleur; welke kleur bepaalt de app zelf." % (a, b))
    return {env: base64.b64encode(data).decode("ascii") for env, data in gelezen.items()}


def _apply(text, repl):
    for k, v in repl.items():
        text = text.replace(k, v)
    return text


def build(env, app):
    if env not in ENVS:
        raise SystemExit("onbekende omgeving: %s (kies uit %s)" % (env, ", ".join(ENVS)))
    cfg = config(app)
    th = _theme(cfg, env)
    naam = cfg["name"]
    kort = cfg.get("short_name", naam)
    naam_env = naam + NAAM_SUFFIX[env]
    kort_env = kort + NAAM_SUFFIX[env]
    repl = {
        "{{APP_NAME}}": naam,
        "{{APP_NAME_URL}}": urllib.parse.quote(naam),
        "{{APP_SHORT}}": kort,
        "{{APP_NAME_ENV}}": naam_env,
        "{{APP_NAME_ENV_URL}}": urllib.parse.quote(naam_env),
        "{{APP_SHORT_ENV}}": kort_env,
        "{{APP_SHORT_ENV_URL}}": urllib.parse.quote(kort_env),
        "{{ICOON}}": iconen(app)[env],
        "{{STORAGE_KEY}}": cfg["storage_key"] + SUFFIX[env],
        "{{ENV}}": env,
        "{{ENV_LABEL}}": LABEL[env],
        "{{MERK}}": th.get("merk", "#333333"),
        "{{MERK_DONKER}}": th.get("merk_donker", "#111111"),
        "{{MERK_LICHT}}": th.get("merk_licht", "#555555"),
    }
    stukken = lambda map_: "".join(  # noqa: E731
        _lees(app, os.path.relpath(p, app))
        for p in sorted(glob.glob(os.path.join(app, "src", map_, "*.js"))))
    script = _apply(stukken("vendor") + stukken("app"), repl)
    styles = _apply(_lees(app, "src/styles.css"), repl)
    html = _apply(_lees(app, "src/index.template.html"), repl)
    html = html.replace("{{STYLES}}", styles).replace("{{SCRIPT}}", script)

    # Afspraak: de naam met omgeving moet ook echt in de pagina belanden.
    if env != "prod" and naam_env not in html and urllib.parse.quote(naam_env) not in html:
        raise PlatformFout(
            "de naam per omgeving (%r) komt niet in de pagina terecht. Gebruik "
            "{{APP_SHORT_ENV}} in apple-mobile-web-app-title en {{APP_SHORT_ENV_URL}} "
            "in het manifest." % naam_env)
    return html


def main(argv, app):
    ap = argparse.ArgumentParser(description="OTAP-CI centrale bouwstap (v2)")
    ap.add_argument("--env", default="prod", choices=ENVS)
    ap.add_argument("--out", default=None, help="uitvoerpad (standaard index.html in de app)")
    ap.add_argument("--check", action="store_true",
                    help="alle omgevingen bouwen (afspraken controleren) en index.html vergelijken")
    args = ap.parse_args(argv)

    if args.check:
        for env in ENVS:
            build(env, app)                     # faalt bij een geschonden afspraak
        pad = os.path.join(app, "index.html")
        current = _lees(app, "index.html") if os.path.exists(pad) else ""
        if current == build("prod", app):
            print("OK: afspraken nageleefd en index.html komt overeen met src/")
            return 0
        print("FOUT: index.html is verouderd — draai `python build.py` en commit het resultaat.",
              file=sys.stderr)
        return 1

    html = build(args.env, app)
    out = args.out or os.path.join(app, "index.html")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    print("gebouwd (%s): %s (%d bytes)" % (args.env, out, len(html)))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--app", default=os.getcwd())
    bekend, rest = ap.parse_known_args()
    sys.exit(main(rest, os.path.abspath(bekend.app)))
