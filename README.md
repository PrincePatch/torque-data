# torque-data — données publiques de l'application Torque

Catalogue des motos lu par l'application Android **Torque** (carnet d'entretien et manuel d'atelier moto) : caractéristiques, plan d'entretien, pièces et références, outillage, couples de serrage, procédures, voyants du tableau de bord, règles contextuelles (météo, saison, charge), modifications compatibles, prix indicatifs, schémas.

L'application télécharge ces fichiers au lancement (`https://raw.githubusercontent.com/PrincePatch/torque-data/main/`) et en garde une copie embarquée : **ajouter ou corriger une moto ici ne demande pas de nouvelle version de l'application.**

| Moto | Millésimes | Statut |
|---|---|---|
| Aprilia RS 660 | 2021-2026 | en construction |

- Contrat des données : [`SCHEMA.md`](SCHEMA.md).
- Validation : `python outils/verifier.py` (lancée aussi par GitHub Actions).
- Chaque valeur technique porte sa **confiance** (`ok` = manuel officiel ou ≥ 2 sources ; `une_source` ; `incertain`) et ses **sources** (`sources.json` de chaque moto).

## Avertissements
- **Aide-mémoire, pas un manuel officiel.** Toujours vérifier dans le manuel d'atelier du constructeur avant une intervention ; en cas de doute, s'adresser à un professionnel.
- Projet **indépendant**, non affilié à Aprilia ni à Piaggio & C. S.p.A., ni approuvé par eux. Aprilia, RS 660 et Tuono sont des marques de leurs titulaires respectifs, citées uniquement pour désigner les motos concernées.
- Aucune image protégée ici : les vues éclatées officielles sont **liées** vers des catalogues tiers, jamais copiées.

## Licences
- Données (JSON) et schémas dessinés (SVG) : **CC BY 4.0** — voir [`LICENSE`](LICENSE).
- Photos tierces éventuelles : licence propre à chaque fichier, détaillée dans `motos/<moto>/credits.json`.

Une erreur ? Ouvrir une *issue* sur ce dépôt.
