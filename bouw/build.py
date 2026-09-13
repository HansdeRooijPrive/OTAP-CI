#!/usr/bin/env python3
"""
Dunne ingang naar de centrale bouwstap van het OTAP-platform.

Dit bestand hoort in de root van elke app en verandert zelden: de echte
bouwlogica staat in OTAP-CI (bouw/otap_build.py), in de versie die app.json
noemt ("platform": "v2"). Lokaal wordt die versie eenmalig opgehaald in .otap/
(staat in .gitignore); in CI zet de workflow OTAP_CI_DIR.

    python build.py                 -> productie-build naar index.html
    python build.py --env=test      -> testvariant
    python build.py --check         -> afspraken + index.html controleren
"""
import importlib.util
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = "https://github.com/HansdeRooijPrive/OTAP-CI.git"


def _versie():
    with open(os.path.join(ROOT, "app.json"), encoding="utf-8") as f:
        return json.load(f).get("platform", "v2")


def _centrale_map():
    if os.environ.get("OTAP_CI_DIR"):
        return os.environ["OTAP_CI_DIR"]
    doel = os.path.join(ROOT, ".otap")
    versie = _versie()
    merk = os.path.join(doel, ".platformversie")
    huidig = open(merk).read().strip() if os.path.exists(merk) else None
    if huidig != versie:
        if not os.path.isdir(os.path.join(doel, ".git")):
            subprocess.run(["git", "clone", "-q", "--depth", "1", "--branch", versie, REPO, doel],
                           check=True)
        else:
            subprocess.run(["git", "-C", doel, "fetch", "-q", "--depth", "1", "origin", versie],
                           check=True)
            subprocess.run(["git", "-C", doel, "checkout", "-q", "FETCH_HEAD"], check=True)
        with open(merk, "w") as f:
            f.write(versie)
    return doel


_pad = os.path.join(_centrale_map(), "bouw", "otap_build.py")
_spec = importlib.util.spec_from_file_location("otap_build", _pad)
_otap = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_otap)


def _config():
    return _otap.config(ROOT)


def build(env="prod"):
    return _otap.build(env, ROOT)


if __name__ == "__main__":
    sys.exit(_otap.main(sys.argv[1:], ROOT))
