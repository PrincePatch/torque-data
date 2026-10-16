"""Génère `index.json` : la liste des motos et de TOUS les fichiers que
l'application doit télécharger, plus un numéro de `revision`.

La révision n'augmente que si le contenu a changé (empreinte SHA-256 de tous
les fichiers listés) : l'application compare ce numéro et ne retélécharge
le catalogue que lorsqu'il bouge.

Usage : `python outils/generer_index.py` depuis la racine du dépôt.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

# Console Windows (cp1252) : forcer l'UTF-8 pour les accents et les flèches.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RACINE = Path(__file__).resolve().parent.parent
EXTENSIONS = {".json", ".svg", ".png", ".jpg", ".jpeg", ".webp"}


def fichiers_publies(dossier: Path) -> list[str]:
    """Fichiers utiles d'un dossier (récursif), chemins relatifs à lui, triés.

    Les dossiers de travail (`_fragments`, commençant par `_` ou `.`) sont
    exclus.
    """
    resultat = []
    for chemin in sorted(dossier.rglob("*")):
        relatif = chemin.relative_to(dossier)
        if not chemin.is_file() or chemin.suffix.lower() not in EXTENSIONS:
            continue
        if any(partie.startswith(("_", ".")) for partie in relatif.parts):
            continue
        resultat.append(relatif.as_posix())
    return resultat


def entree_moto(dossier: Path) -> dict:
    """Entrée d'index d'une moto, tirée de son `moto.json`."""
    moto = json.loads((dossier / "moto.json").read_text(encoding="utf-8"))
    identite = moto.get("identite", {})
    millesimes = sorted({
        annee
        for version in moto.get("versions", [])
        for annee in version.get("millesimes", [])
        if isinstance(annee, int)
    })
    fichiers = fichiers_publies(dossier)
    vignette = next((f for f in fichiers if f.endswith("profil-gauche.svg")), None)
    attendus = {"moto.json", "entretien.json", "pieces.json", "procedures.json", "voyants.json"}
    statut = "complet" if attendus <= set(fichiers) else "partiel"
    return {
        "id": moto["id"],
        "marque": identite.get("marque", ""),
        "modele": identite.get("modele", moto["id"]),
        "categorie": identite.get("categorie"),
        "millesimes": millesimes,
        "dossier": dossier.relative_to(RACINE).as_posix(),
        "vignette": f"{dossier.relative_to(RACINE).as_posix()}/{vignette}" if vignette else None,
        "statut": statut,
        "fichiers": fichiers,
    }


def empreinte(chemins: list[Path]) -> str:
    """SHA-256 du contenu de tous les fichiers (chemin + octets)."""
    h = hashlib.sha256()
    for chemin in chemins:
        h.update(chemin.relative_to(RACINE).as_posix().encode())
        # Fins de ligne normalisées : la même donnée sous Windows et sous
        # Linux (GitHub Actions) doit donner la même empreinte.
        h.update(chemin.read_bytes().replace(b"\r\n", b"\n"))
    return h.hexdigest()


def main() -> None:
    """Écrit `index.json` à la racine (révision incrémentée si changement)."""
    motos = [entree_moto(p.parent) for p in sorted((RACINE / "motos").glob("*/moto.json"))]
    commun = [f"commun/{f}" for f in fichiers_publies(RACINE / "commun")] if (RACINE / "commun").exists() else []
    tous = [RACINE / f for f in commun] + [
        RACINE / m["dossier"] / f for m in motos for f in m["fichiers"]
    ]
    nouvelle = empreinte(tous)

    chemin_index = RACINE / "index.json"
    ancien = json.loads(chemin_index.read_text(encoding="utf-8")) if chemin_index.exists() else {}
    revision = int(ancien.get("revision", 0))
    maj = ancien.get("maj")
    if ancien.get("empreinte") != nouvelle:
        revision += 1
        maj = dt.date.today().isoformat()

    index = {
        "version_schema": 1,
        "maj": maj,
        "revision": revision,
        "empreinte": nouvelle,
        "commun": commun,
        "motos": motos,
    }
    chemin_index.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    total = len(commun) + sum(len(m["fichiers"]) for m in motos)
    print(f"index.json : révision {revision}, {len(motos)} moto(s), {total} fichier(s).")


if __name__ == "__main__":
    main()
