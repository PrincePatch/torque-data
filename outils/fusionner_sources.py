"""Fusionne les fragments de sources (`_fragments/sources-*.json`) d'une moto
dans son `sources.json`, sans doublon.

Deux fragments peuvent citer la même source sous le même identifiant (les
manuels) : la première description est gardée. Un même identifiant avec deux
URL différentes est signalé, car il cache sans doute deux sources distinctes.

Usage : `python outils/fusionner_sources.py motos/aprilia-rs660`
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

# Console Windows (cp1252) : forcer l'UTF-8 pour les accents et les flèches.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def fusionner(dossier: Path) -> int:
    """Écrit `<dossier>/sources.json` ; rend le nombre de conflits d'URL."""
    cible = dossier / "sources.json"
    entrees: dict[str, dict] = {}
    morceaux = ([cible] if cible.exists() else []) + sorted((dossier / "_fragments").glob("sources-*.json"))
    conflits = 0
    for chemin in morceaux:
        contenu = json.loads(chemin.read_text(encoding="utf-8"))
        for source in contenu.get("sources", []):
            identifiant = source.get("id")
            if not identifiant:
                continue
            existante = entrees.get(identifiant)
            if existante is None:
                entrees[identifiant] = source
            elif existante.get("url") and source.get("url") and existante["url"] != source["url"]:
                conflits += 1
                print(f"  conflit : {identifiant} → {existante['url']} / {source['url']} ({chemin.name})")
    resultat = {
        "version_schema": 1,
        "maj": dt.date.today().isoformat(),
        "sources": sorted(entrees.values(), key=lambda s: s["id"]),
    }
    cible.write_text(json.dumps(resultat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{cible.as_posix()} : {len(entrees)} source(s), {conflits} conflit(s).")
    return conflits


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(1 if fusionner(Path(sys.argv[1])) else 0)
