"""Vérifie les données de torque-data contre le contrat de SCHEMA.md.

Contrôles bloquants (erreurs) :
- chaque fichier JSON se lit, porte `version_schema: 1` ;
- identifiants présents et uniques dans leur fichier ;
- chaque identifiant référencé existe (pièces, outils, opérations, procédures,
  couples, composants, carénages, mesures, vues, sources, fichiers SVG) ;
- les conditions des règles n'utilisent que les variables autorisées ;
- les textes traduisibles ont une valeur `fr`.

Avertissements (non bloquants) : traduction anglaise manquante sur un titre,
élément sans source, intervalle sans `km` ni `mois`…

Usage : `python outils/verifier.py [--strict]` depuis la racine du dépôt.
`--strict` transforme les avertissements en erreurs. Code de sortie 1 en cas
d'erreur.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Console Windows (cp1252) : forcer l'UTF-8 pour les accents et les flèches.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RACINE = Path(__file__).resolve().parent.parent

# Variables du langage de règles (SCHEMA.md § 14). Les variables
# paramétrées (mesure.<id>, operation.<id>.…) sont vérifiées par motif.
VARIABLES_FIXES = {
    "date.mois", "date.saison", "date.heure",
    "meteo.temp_actuelle", "meteo.temp_min_24h", "meteo.temp_max_24h", "meteo.temp_min_72h",
    "meteo.pluie_24h_mm", "meteo.pluie_passee_24h_mm", "meteo.vent_max_24h_kmh",
    "meteo.rafales_max_24h_kmh", "meteo.humidite_moy_24h", "meteo.gel_72h", "meteo.neige_24h_cm",
    "moto.km", "moto.km_par_jour", "moto.jours_sans_releve", "moto.jours_immobilisee",
    "moto.age_mois", "moto.millesime", "moto.version", "moto.usage",
    "moto.occasion_historique_inconnu", "moto.hivernage",
    "charge.pilote_kg", "charge.passager_kg", "charge.bagages_kg", "charge.total_kg",
    "charge.passager", "charge.depasse_ptac",
    "voyants.allumes",
}
MOTIF_MESURE = re.compile(r"^mesure\.(me-[a-z0-9-]+)(\.age_jours)?$")
MOTIF_OPERATION = re.compile(r"^operation\.(op-[a-z0-9-]+)\.(km_depuis|jours_depuis)$")
OPERATEURS = {"<", "<=", ">", ">=", "==", "!=", "dans", "contient"}
CHAMPS_TEXTE_COURT = {"titre", "nom", "libelle", "element"}


class Rapport:
    """Accumule erreurs et avertissements, avec le fichier concerné."""

    def __init__(self) -> None:
        self.erreurs: list[str] = []
        self.avertissements: list[str] = []

    def erreur(self, fichier: str, message: str) -> None:
        self.erreurs.append(f"{fichier} : {message}")

    def avertir(self, fichier: str, message: str) -> None:
        self.avertissements.append(f"{fichier} : {message}")


def lire_json(chemin: Path, rapport: Rapport) -> dict | None:
    """Lit un fichier JSON ; signale l'erreur et rend None s'il est illisible."""
    try:
        contenu = json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        rapport.erreur(chemin.relative_to(RACINE).as_posix(), f"JSON illisible ({exc})")
        return None
    if not isinstance(contenu, dict):
        rapport.erreur(chemin.relative_to(RACINE).as_posix(), "la racine doit être un objet")
        return None
    if contenu.get("version_schema") != 1 and chemin.name != "index.json":
        rapport.erreur(chemin.relative_to(RACINE).as_posix(), "version_schema absent ou différent de 1")
    return contenu


def verifier_textes(objet, fichier: str, rapport: Rapport, chemin: str = "") -> None:
    """Parcourt récursivement un objet : tout Texte {fr, en…} doit avoir `fr`."""
    if isinstance(objet, dict):
        cles = set(objet)
        if cles and cles <= {"fr", "en", "es", "pt", "de", "it"} and all(isinstance(v, str) for v in objet.values()):
            if "fr" not in objet:
                rapport.erreur(fichier, f"texte sans « fr » ({chemin})")
            return
        for cle, valeur in objet.items():
            if cle in CHAMPS_TEXTE_COURT and isinstance(valeur, dict) and "fr" in valeur and "en" not in valeur:
                rapport.avertir(fichier, f"« {cle} » sans traduction anglaise ({chemin}.{cle})")
            verifier_textes(valeur, fichier, rapport, f"{chemin}.{cle}" if chemin else cle)
    elif isinstance(objet, list):
        for index, element in enumerate(objet):
            verifier_textes(element, fichier, rapport, f"{chemin}[{index}]")


def ids_de(liste, fichier: str, rapport: Rapport, nom_liste: str) -> set[str]:
    """Identifiants d'une liste d'objets ; signale les absents et les doublons."""
    vus: set[str] = set()
    if not isinstance(liste, list):
        return vus
    for index, element in enumerate(liste):
        if not isinstance(element, dict):
            rapport.erreur(fichier, f"{nom_liste}[{index}] n'est pas un objet")
            continue
        identifiant = element.get("id")
        if not isinstance(identifiant, str) or not identifiant:
            rapport.erreur(fichier, f"{nom_liste}[{index}] sans id")
            continue
        if identifiant in vus:
            rapport.erreur(fichier, f"id en double : {identifiant}")
        vus.add(identifiant)
    return vus


def collecter_sources(objet, trouvees: set[str]) -> None:
    """Rassemble tous les identifiants cités dans des champs `sources`."""
    if isinstance(objet, dict):
        for cle, valeur in objet.items():
            if cle == "sources" and isinstance(valeur, list):
                for source in valeur:
                    if isinstance(source, str):
                        trouvees.add(source.split("#")[0])
            else:
                collecter_sources(valeur, trouvees)
    elif isinstance(objet, list):
        for element in objet:
            collecter_sources(element, trouvees)


def variables_condition(condition, fichier: str, rapport: Rapport, contexte: str) -> list[str]:
    """Valide la forme d'un arbre de conditions et rend ses variables."""
    if not isinstance(condition, dict):
        rapport.erreur(fichier, f"{contexte} : condition qui n'est pas un objet")
        return []
    if "tous" in condition or "un_de" in condition:
        enfants = condition.get("tous", condition.get("un_de"))
        if not isinstance(enfants, list) or not enfants:
            rapport.erreur(fichier, f"{contexte} : « tous » / « un_de » doit être une liste non vide")
            return []
        variables: list[str] = []
        for enfant in enfants:
            variables += variables_condition(enfant, fichier, rapport, contexte)
        return variables
    if "non" in condition:
        return variables_condition(condition["non"], fichier, rapport, contexte)
    variable, operateur = condition.get("variable"), condition.get("op")
    if not isinstance(variable, str) or operateur not in OPERATEURS or "valeur" not in condition:
        rapport.erreur(fichier, f"{contexte} : feuille mal formée {condition}")
        return []
    return [variable]


def verifier_variable(variable: str, mesures: set[str], operations: set[str], fichier: str,
                      rapport: Rapport, contexte: str) -> None:
    """Une variable doit être fixe, ou désigner une mesure / opération existante."""
    if variable in VARIABLES_FIXES:
        return
    motif = MOTIF_MESURE.match(variable)
    if motif:
        if mesures and motif.group(1) not in mesures:
            rapport.erreur(fichier, f"{contexte} : mesure inconnue dans « {variable} »")
        return
    motif = MOTIF_OPERATION.match(variable)
    if motif:
        if operations and motif.group(1) not in operations:
            rapport.erreur(fichier, f"{contexte} : opération inconnue dans « {variable} »")
        return
    rapport.erreur(fichier, f"{contexte} : variable non autorisée « {variable} »")


def _references(valeurs, connus: set[str], fichier: str, rapport: Rapport, contexte: str, genre: str) -> None:
    """Chaque identifiant de `valeurs` (chaîne ou liste) doit être dans `connus`."""
    if valeurs is None:
        return
    for valeur in valeurs if isinstance(valeurs, list) else [valeurs]:
        if isinstance(valeur, str) and valeur and valeur not in connus:
            rapport.erreur(fichier, f"{contexte} : {genre} inconnu(e) « {valeur} »")


def verifier_moto(dossier: Path, communs: dict, rapport: Rapport) -> None:
    """Vérifie tous les fichiers d'une moto et leurs références croisées."""
    nom = dossier.relative_to(RACINE).as_posix()

    def references(valeurs, connus: set[str], fichier: str, contexte: str, genre: str) -> None:
        _references(valeurs, connus, fichier, rapport, contexte, genre)

    donnees: dict[str, dict] = {}
    for chemin in sorted(dossier.glob("*.json")):
        contenu = lire_json(chemin, rapport)
        if contenu is not None:
            donnees[chemin.name] = contenu
            verifier_textes(contenu, f"{nom}/{chemin.name}", rapport)
    if "moto.json" not in donnees:
        rapport.erreur(nom, "moto.json manquant")
        return

    def f(fichier: str) -> dict:
        return donnees.get(fichier, {})

    def liste(fichier: str, cle: str) -> list:
        valeur = f(fichier).get(cle, [])
        return valeur if isinstance(valeur, list) else []

    operations = ids_de(liste("entretien.json", "operations"), f"{nom}/entretien.json", rapport, "operations")
    revisions = ids_de(liste("entretien.json", "revisions"), f"{nom}/entretien.json", rapport, "revisions")
    mesures = ids_de(liste("mesures.json", "mesures"), f"{nom}/mesures.json", rapport, "mesures")
    pieces = ids_de(liste("pieces.json", "pieces"), f"{nom}/pieces.json", rapport, "pieces")
    outils = ids_de(liste("outils.json", "outils"), f"{nom}/outils.json", rapport, "outils")
    couples = ids_de(liste("couples.json", "couples"), f"{nom}/couples.json", rapport, "couples")
    procedures = ids_de(liste("procedures.json", "procedures"), f"{nom}/procedures.json", rapport, "procedures")
    carenages = ids_de(liste("carenages.json", "carenages"), f"{nom}/carenages.json", rapport, "carenages")
    vues = ids_de(liste("composants.json", "vues"), f"{nom}/composants.json", rapport, "vues")
    composants = ids_de(liste("composants.json", "composants"), f"{nom}/composants.json", rapport, "composants")
    ids_de(liste("voyants.json", "voyants"), f"{nom}/voyants.json", rapport, "voyants")
    ids_de(liste("regles.json", "regles"), f"{nom}/regles.json", rapport, "regles")
    ids_de(liste("modifications.json", "modifications"), f"{nom}/modifications.json", rapport, "modifications")
    sources = ids_de(liste("sources.json", "sources"), f"{nom}/sources.json", rapport, "sources")
    rappels = {r.get("id") for r in liste("fiabilite.json", "rappels") if isinstance(r, dict)}

    def fichier_existe(relatif, contexte: str, fichier: str) -> None:
        if not isinstance(relatif, str) or not relatif:
            return
        base = RACINE if relatif.startswith("commun/") else dossier
        if not (base / relatif).exists():
            rapport.erreur(fichier, f"{contexte} : fichier introuvable « {relatif} »")

    # entretien.json
    fe = f"{nom}/entretien.json"
    for op in liste("entretien.json", "operations"):
        if not isinstance(op, dict):
            continue
        ctx = op.get("id", "?")
        references([l.get("id") for l in op.get("pieces", []) if isinstance(l, dict)], pieces, fe, ctx, "pièce")
        references([l.get("id") for l in op.get("consommables", []) if isinstance(l, dict)], pieces, fe, ctx, "consommable")
        references(op.get("outils"), outils, fe, ctx, "outil")
        references(op.get("procedure"), procedures, fe, ctx, "procédure")
        references(op.get("composants"), composants, fe, ctx, "composant")
        references(op.get("mesure"), mesures, fe, ctx, "mesure")
        references(op.get("groupe_revision"), revisions, fe, ctx, "révision")
        gravite = op.get("gravite")
        if not isinstance(gravite, int) or not 1 <= gravite <= 5:
            rapport.erreur(fe, f"{ctx} : gravite doit être un entier 1-5")
        intervalle = op.get("intervalle", {})
        if isinstance(intervalle, dict) and not any(
            intervalle.get(c) for c in ("km", "mois", "premiere_km", "premiere_mois", "a_chaque_sortie", "severe")
        ):
            rapport.avertir(fe, f"{ctx} : pas d'intervalle (opération d'usure ou sur mesure)")
    for revision in liste("entretien.json", "revisions"):
        if isinstance(revision, dict):
            references(revision.get("operations"), operations, fe, revision.get("id", "?"), "opération")

    # mesures.json
    for mesure in liste("mesures.json", "mesures"):
        if isinstance(mesure, dict):
            references(mesure.get("operation"), operations, f"{nom}/mesures.json", mesure.get("id", "?"), "opération")
            fichier_existe(mesure.get("schema"), mesure.get("id", "?"), f"{nom}/mesures.json")

    # pieces, outils, couples
    for piece in liste("pieces.json", "pieces"):
        if isinstance(piece, dict):
            references(piece.get("composant"), composants, f"{nom}/pieces.json", piece.get("id", "?"), "composant")
    for outil in liste("outils.json", "outils"):
        if isinstance(outil, dict):
            references(outil.get("operations"), operations, f"{nom}/outils.json", outil.get("id", "?"), "opération")
    for couple in liste("couples.json", "couples"):
        if isinstance(couple, dict):
            references(couple.get("composant"), composants, f"{nom}/couples.json", couple.get("id", "?"), "composant")

    # procedures.json
    fp = f"{nom}/procedures.json"
    for proc in liste("procedures.json", "procedures"):
        if not isinstance(proc, dict):
            continue
        ctx = proc.get("id", "?")
        references(proc.get("operations"), operations, fp, ctx, "opération")
        references(proc.get("prealables"), procedures | carenages, fp, ctx, "préalable")
        references(proc.get("outils"), outils, fp, ctx, "outil")
        references(proc.get("pieces"), pieces, fp, ctx, "pièce")
        references(proc.get("couples"), couples, fp, ctx, "couple")
        for etape in proc.get("etapes", []):
            if not isinstance(etape, dict):
                continue
            references(etape.get("couple"), couples, fp, f"{ctx} étape {etape.get('n')}", "couple")
            references(etape.get("outil"), outils, fp, f"{ctx} étape {etape.get('n')}", "outil")
            schema = etape.get("schema")
            if isinstance(schema, dict):
                fichier_existe(schema.get("fichier"), f"{ctx} étape {etape.get('n')}", fp)
                references(schema.get("composants"), composants, fp, f"{ctx} étape {etape.get('n')}", "composant")

    # carenages.json
    for carenage in liste("carenages.json", "carenages"):
        if isinstance(carenage, dict):
            ctx = carenage.get("id", "?")
            references(carenage.get("prealables"), carenages, f"{nom}/carenages.json", ctx, "carénage")
            references(carenage.get("procedure"), procedures, f"{nom}/carenages.json", ctx, "procédure")
            references(carenage.get("composant"), composants, f"{nom}/carenages.json", ctx, "composant")

    # composants.json
    fc = f"{nom}/composants.json"
    for vue in liste("composants.json", "vues"):
        if isinstance(vue, dict):
            fichier_existe(vue.get("fichier"), vue.get("id", "?"), fc)
    for composant in liste("composants.json", "composants"):
        if not isinstance(composant, dict):
            continue
        ctx = composant.get("id", "?")
        for repere in composant.get("reperes", []):
            if not isinstance(repere, dict):
                continue
            references(repere.get("vue"), vues, fc, ctx, "vue")
            for axe in ("x", "y"):
                valeur = repere.get(axe)
                if not isinstance(valeur, (int, float)) or not 0 <= valeur <= 1:
                    rapport.erreur(fc, f"{ctx} : repère {axe} doit être une fraction 0-1")
        references(composant.get("carenages_a_deposer"), carenages, fc, ctx, "carénage")
        references(composant.get("operations"), operations, fc, ctx, "opération")

    # voyants.json
    for voyant in liste("voyants.json", "voyants"):
        if isinstance(voyant, dict):
            references(voyant.get("operations"), operations, f"{nom}/voyants.json", voyant.get("id", "?"), "opération")
            fichier_existe(voyant.get("picto"), voyant.get("id", "?"), f"{nom}/voyants.json")

    # fiabilite.json
    ff = f"{nom}/fiabilite.json"
    for point in f("fiabilite.json").get("controles_avant_sortie", []):
        if isinstance(point, dict):
            references(point.get("operation"), operations, ff, "controles_avant_sortie", "opération")
    occasion = f("fiabilite.json").get("occasion", {})
    if isinstance(occasion, dict):
        for action in occasion.get("apres_achat", []):
            if isinstance(action, dict):
                references(action.get("operation"), operations, ff, "occasion.apres_achat", "opération")

    # regles.json (+ communes, vérifiées ici avec les ids de cette moto)
    for nom_fichier, regles in (("regles.json", liste("regles.json", "regles")),
                                ("commun/regles-generales.json", communs.get("regles", []))):
        fichier = f"{nom}/{nom_fichier}" if not nom_fichier.startswith("commun/") else nom_fichier
        for regle in regles:
            if not isinstance(regle, dict):
                continue
            ctx = regle.get("id", "?")
            for variable in variables_condition(regle.get("condition"), fichier, rapport, ctx):
                verifier_variable(variable, mesures, operations, fichier, rapport, ctx)
            references(regle.get("operations"), operations | rappels, fichier, ctx, "opération")
            references(regle.get("mesures"), mesures, fichier, ctx, "mesure")

    # modifications.json
    for modification in liste("modifications.json", "modifications"):
        if isinstance(modification, dict):
            references(modification.get("outils"), outils, f"{nom}/modifications.json", modification.get("id", "?"), "outil")

    # sources citées
    citees: set[str] = set()
    for nom_fichier, contenu in donnees.items():
        if nom_fichier != "sources.json":
            collecter_sources(contenu, citees)
    if sources:
        for source in sorted(citees - sources):
            rapport.erreur(f"{nom}/sources.json", f"source citée mais absente : {source}")
    elif citees:
        rapport.erreur(nom, "sources.json manquant alors que des sources sont citées")


def main() -> int:
    """Vérifie tout le dépôt et affiche le rapport ; 1 si une erreur."""
    strict = "--strict" in sys.argv
    rapport = Rapport()
    communs: dict = {}
    for chemin in sorted((RACINE / "commun").glob("*.json")):
        contenu = lire_json(chemin, rapport)
        if contenu is not None:
            verifier_textes(contenu, chemin.relative_to(RACINE).as_posix(), rapport)
            if chemin.name == "regles-generales.json":
                communs = contenu
    motos = sorted(p.parent for p in (RACINE / "motos").glob("*/moto.json"))
    if not motos:
        rapport.erreur("motos/", "aucune moto (motos/<id>/moto.json)")
    for dossier in motos:
        verifier_moto(dossier, communs, rapport)
    index = RACINE / "index.json"
    if index.exists():
        lire_json(index, rapport)

    for message in rapport.avertissements:
        print(f"  avertissement  {message}")
    for message in rapport.erreurs:
        print(f"  ERREUR         {message}")
    nb_erreurs = len(rapport.erreurs) + (len(rapport.avertissements) if strict else 0)
    print(f"\n{len(motos)} moto(s), {len(rapport.erreurs)} erreur(s), {len(rapport.avertissements)} avertissement(s).")
    return 1 if nb_erreurs else 0


if __name__ == "__main__":
    sys.exit(main())
