# Schéma des données Torque — version 1

Contrat entre ce dépôt (données publiques des motos) et l'application **Torque**. L'application lit ces fichiers au lancement depuis
`https://raw.githubusercontent.com/PrincePatch/torque-data/main/` et en garde une copie embarquée (premier lancement, hors ligne).
**Ajouter une moto = ajouter un dossier dans `motos/` et une ligne dans `index.json`, sans nouvelle version de l'application.**

Validation : `python outils/verifier.py` (structure, champs obligatoires, identifiants référencés, textes FR présents). Lancé aussi par GitHub Actions à chaque push.

## 1. Conventions communes

### 1.1 Fichiers
- UTF-8, JSON strict (pas de commentaires, pas de virgule finale), indentation 2 espaces.
- Chaque fichier commence par `"version_schema": 1` et `"maj": "AAAA-MM-JJ"` (date de dernière modification du contenu).
- Arborescence :

```
index.json                       ← catalogue des motos
commun/
  prix-zones.json                ← taux horaires et coefficients par pays / zone
  regles-generales.json          ← règles contextuelles valables pour toute moto (météo, saison, immobilisation…)
  pictos/*.svg                   ← pictogrammes génériques (voyants, catégories)
motos/<id-moto>/
  moto.json                      ← identité, versions, caractéristiques, fluides, pneus, pressions, charge, électricité, suspensions
  entretien.json                 ← opérations d'entretien et leurs intervalles
  mesures.json                   ← relevés que l'utilisateur peut saisir (pression, tension de chaîne…) et leurs seuils
  pieces.json                    ← pièces et consommables : références, prix
  outils.json                    ← outillage
  couples.json                   ← couples de serrage
  procedures.json                ← procédures pas à pas
  carenages.json                 ← pièces de carénage, vis, ordre de dépose
  composants.json                ← emplacement de chaque composant sur les schémas
  voyants.json                   ← voyants du tableau de bord + brief pour la lecture d'image
  fiabilite.json                 ← rappels, problèmes connus, rodage, contrôles avant départ, achat d'occasion
  regles.json                    ← règles contextuelles propres à cette moto
  modifications.json             ← accessoires et modifications compatibles
  sources.json                   ← bibliographie (id → document, URL)
  credits.json                   ← images : auteur, licence, modifications
  schemas/*.svg                  ← schémas dessinés (profil gauche/droit, dessus, tableau de bord…)
  images/*                       ← photos sous licence libre (voir credits.json)
```

### 1.2 Identifiants
- `kebab-case` ASCII, uniques **dans leur fichier**, stables (ne jamais renommer un identifiant publié : l'historique des utilisateurs s'y rattache).
- Préfixes conseillés : opérations `op-…`, pièces `pc-…`, consommables `cs-…`, outils `ou-…`, couples `cp-…`, procédures `pr-…`, carénages `ca-…`, composants `co-…`, voyants `vo-…`, mesures `me-…`, règles `rg-…`, modifications `md-…`, sources `src-…`.

### 1.3 Types réutilisables

**Texte** — texte traduisible. `fr` obligatoire ; `en` dès que possible ; puis `es`, `pt`, `de`, `it`. Repli de l'appli : langue de l'appareil → `en` → `fr`.
```json
{ "fr": "Vidange huile moteur + filtre", "en": "Engine oil and filter change" }
```

**Fiabilité d'une valeur** — tout objet porteur d'une valeur technique peut avoir :
```json
"confiance": "ok" | "une_source" | "incertain",
"sources": ["src-manuel-proprietaire#p186", "src-revzilla"]
```
- `ok` = manuel officiel ou ≥ 2 sources concordantes (✅) ; `une_source` = une seule source (⚠️) ; `incertain` = contradictoire ou estimé (❓).
- Une source se cite par son id dans `sources.json`, suivi facultativement de `#p<page>` ou `#<ancre>`.
- L'appli affiche une pastille discrète pour `une_source` et `incertain`.

**Millésimes** — `"millesimes": [2021, 2022, 2023, 2024]` ; absent = toutes les années de la moto. **Versions** — `"versions": ["standard", "a2"]` ; absent = toutes.

**Prix** — en euros TTC, France, sauf `devise`. `par` = quantité à laquelle le prix correspond (le litre, la pièce, le jeu, l'heure).
```json
{ "min": 12, "moy": 15, "max": 22, "devise": "EUR", "par": { "valeur": 1, "unite": "L" }, "date": "2026-10-16", "confiance": "une_source", "sources": ["src-motoblouz"] }
```
Coût d'une opération = Σ `prix.moy` × (quantité utilisée ÷ `par.valeur`), dans la même unité.

**Quantité** — `{ "valeur": 2.7, "unite": "L" }` ; unités : `L`, `mL`, `kg`, `g`, `piece`, `jeu`, `m`, `mm`, `bar`, `Nm`, `km`, `mois`, `h`, `min`.

## 2. `index.json`
`index.json` est **généré** par `python outils/generer_index.py` (ne pas l'éditer à la main) : il liste **tous** les fichiers (JSON, SVG, images) que l'application doit télécharger, et porte un numéro de `revision` incrémenté à chaque génération qui change le contenu — l'application ne retélécharge le catalogue que si `revision` a changé.
```json
{
  "version_schema": 1, "maj": "2026-10-16", "revision": 12,
  "commun": ["commun/prix-zones.json", "commun/regles-generales.json", "commun/pictos/huile.svg", "…"],
  "motos": [
    {
      "id": "aprilia-rs660",
      "marque": "Aprilia", "modele": "RS 660",
      "categorie": "sportive",
      "millesimes": [2021, 2022, 2023, 2024, 2025, 2026],
      "dossier": "motos/aprilia-rs660",
      "vignette": "motos/aprilia-rs660/schemas/profil-gauche.svg",
      "statut": "complet" | "partiel" | "brouillon",
      "fichiers": ["moto.json", "entretien.json", "..."]
    }
  ]
}
```

## 3. `moto.json`
```json
{
  "version_schema": 1, "maj": "…", "id": "aprilia-rs660",
  "identite": { "marque": "Aprilia", "modele": "RS 660", "constructeur": "Piaggio & C. S.p.A.", "categorie": "sportive" },
  "versions": [
    { "id": "standard", "nom": Texte, "millesimes": [2021, …], "puissance_kw": 73.5, "puissance_ch": 100, "couple_nm": 67, "note": Texte },
    { "id": "a2", "nom": Texte, "puissance_kw": 35, "permis": "A2", … ,
      "variantes": [ { "millesimes": [2025], "puissance_kw": 35, "puissance_ch": 47.5, "couple_nm": 62, "note": Texte, "confiance", "sources" } ] },
    { "id": "factory", … }, { "id": "extrema", … }, { "id": "limited-edition", … }
  ],
  "millesimes": [ { "annee": 2025, "changements": Texte, "sources": […] } ],
  // `variantes` d'une version : valeurs qui changent selon le millésime (puissance 2025+…) ; elles remplacent celles de la version pour ces années.
  "caracteristiques": [
    { "id": "cylindree", "groupe": "moteur", "libelle": Texte, "valeur": 659, "unite": "cm3", "texte": Texte?, "millesimes"?, "versions"?, "confiance", "sources" }
  ],
  "fluides": [
    { "id": "huile-moteur", "libelle": Texte, "norme": "SAE 10W-60 …", "capacite": Quantité, "capacite_note": Texte, "consommable": "cs-huile-moteur", "confiance", "sources" }
  ],
  "pneus": {
    "avant": { "dimension": "120/70 ZR17", "indice": "58W", "jante": "3.50 x 17", "monte_origine": Texte, "profondeur_mini_mm": 2 },
    "arriere": { … }
  },
  "pressions": [
    { "id": "solo", "libelle": Texte, "avant_bar": 2.3, "arriere_bar": 2.5, "a_froid": true, "condition": { "passager": false }, "confiance", "sources" },
    { "id": "duo", … , "condition": { "passager": true } },
    { "id": "piste", … , "a_froid": false, "condition": { "usage": "piste" } }
  ],
  "charge": { "poids_ordre_marche_kg": 183, "poids_sec_kg": 169, "ptac_kg": 0, "charge_utile_max_kg": 0, "bagages_max_kg": Texte?, "confiance", "sources" },
  "electricite": { "batterie": Texte, "batterie_piece": "pc-batterie", "fusibles": [ { "calibre_a": 30, "role": Texte, "emplacement": "co-boite-fusibles" } ], "alternateur_w": 0, "eclairage": Texte },
  "suspensions": {
    "fourche": { "type": Texte, "reglages": [ { "id": "precharge", "libelle": Texte, "plage": Texte, "origine": Texte, "outil": "ou-…" } ] },
    "amortisseur": { … }
  },
  "plausibilite": { "km_par_jour_max": 1000, "km_max_compteur": 999999 },
  "avertissement": Texte
}
```

## 4. `entretien.json` — le cœur du moteur de recommandations
```json
{
  "version_schema": 1, "maj": "…",
  "operations": [
    {
      "id": "op-vidange-huile-filtre",
      "titre": Texte,
      "categorie": "moteur",
      "type": "remplacer",
      "intervalle": {
        "km": 10000,
        "mois": 12,
        "premiere_km": 1000,
        "premiere_mois": null,
        "severe": { "km": 5000, "mois": 6 },
        "piste": { "km": 2000 },
        "repetition": "les_deux_premier_atteint"
      },
      "gravite": 4,
      "resume": Texte,
      "pourquoi": Texte,
      "symptomes": Texte,
      "si_neglige": Texte,
      "pieces": [ { "id": "pc-filtre-huile", "quantite": 1 } ],
      "consommables": [ { "id": "cs-huile-moteur", "quantite": { "valeur": 2.7, "unite": "L" } } ],
      "outils": ["ou-cle-filtre-huile", "ou-douille-…"],
      "procedure": "pr-vidange-huile-filtre",
      "composants": ["co-filtre-huile", "co-bouchon-vidange"],
      "mesure": "me-…",
      "duree_diy_min": 60,
      "temps_atelier_h": 0.8,
      "difficulte": 2,
      "faisable_soi_meme": true,
      "outillage_special": false,
      "garantie": Texte,
      "groupe_revision": ["revision-1000", "revision-10000"],
      "millesimes"?, "versions"?, "confiance", "sources"
    }
  ],
  "revisions": [
    { "id": "revision-10000", "titre": Texte, "km": 10000, "mois": 12, "operations": ["op-…"], "temps_atelier_h": 2.5 }
  ]
}
```
- `categorie` ∈ `moteur`, `admission`, `allumage`, `refroidissement`, `transmission`, `freins`, `pneus`, `roues`, `suspensions`, `direction`, `electricite`, `eclairage`, `carrosserie`, `controle`, `nettoyage`, `stockage`.
- `type` ∈ `remplacer`, `controler`, `regler`, `lubrifier`, `nettoyer`, `diagnostic`, `purger`.
- `intervalle` : champs tous facultatifs. `km` / `mois` = périodicité ; `premiere_km` / `premiere_mois` = première échéance ponctuelle (rodage : vidange à 1 000 km, puis la grille reprend à 10 000, 20 000…) ; `decalage_km` = décalage de la grille constructeur quand elle ne part pas de zéro (contrôle du filtre à air à 10 000 puis 30 000 km → `km: 20000, decalage_km: 10000`) ; `severe` = usage sévère (ville, courts trajets, pluie, poussière) ; `piste` = usage piste ; `a_chaque_sortie: true` = contrôle avant chaque départ ; `repetition` : `les_deux_premier_atteint` (défaut : la première des deux échéances km/mois déclenche), `km_seulement`, `mois_seulement`, `une_fois` (ex. révision des 1 000 km).
- `gravite` (1-5) = conséquence d'un oubli : 1 confort, 2 usure prématurée, 3 panne probable, 4 casse moteur / coût élevé, 5 **sécurité** (freins, pneus, direction).
- L'**urgence** (0-100) n'est pas stockée : l'appli la calcule (échéance restante en km et en jours, km/jour moyen de l'utilisateur, gravité, contexte).

## 5. `mesures.json`
```json
{ "mesures": [
  { "id": "me-pression-avant", "libelle": Texte, "unite": "bar", "pas": 0.05,
    "cible": "pressions", "roue": "avant",
    "seuils": { "alerte_ecart": 0.2, "danger_ecart": 0.4 },
    "operation": "op-controle-pression-pneus", "aide": Texte, "confiance", "sources" },
  { "id": "me-fleche-chaine", "libelle": Texte, "unite": "mm", "min": 0, "max": 0, "seuils": { "alerte_bas": 0, "alerte_haut": 0 }, "operation": "op-tension-chaine", "aide": Texte, "schema": "schemas/chaine-fleche.svg" },
  { "id": "me-etat", "libelle": Texte, "type": "choix", "choix": [ { "id": "bon", "libelle": Texte, "gravite": 0 }, { "id": "use", "libelle": Texte, "gravite": 3 } ] }
] }
```
`type` ∈ `nombre` (défaut), `choix`, `booleen`, `photo`. `cible: "pressions"` = la valeur de référence est calculée depuis `moto.json → pressions` selon la charge du jour.

## 6. `pieces.json`
```json
{
  "pieces": [
    {
      "id": "pc-filtre-huile",
      "nom": Texte,
      "categorie": "moteur",
      "type": "piece" | "consommable",
      "quantite_par_moto": { "valeur": 1, "unite": "piece" },
      "references": [
        { "marque": "Aprilia", "ref": "…", "origine": true, "note": Texte, "confiance", "sources" },
        { "marque": "HifloFiltro", "ref": "HF…", "origine": false, "confiance", "sources" }
      ],
      "specification": Texte,
      "prix": Prix,
      "lien_eclate": "https://… (page du catalogue tiers, ouverte dans le navigateur)",
      "composant": "co-filtre-huile",
      "millesimes"?, "versions"?
    }
  ]
}
```
Les consommables (huile, liquide de frein, lubrifiant chaîne…) sont aussi dans `pieces.json`, avec `"type": "consommable"` et un id en `cs-…`, plus une liste de produits compatibles dans `references` (`origine: false`).

## 7. `outils.json`
```json
{ "outils": [
  { "id": "ou-douille-17", "nom": Texte, "taille": "17 mm", "categorie": "douille",
    "niveau": "courant" | "complet" | "special",
    "ref_aprilia": "…", "prix": Prix, "operations": ["op-…"], "note": Texte, "confiance", "sources" }
] }
```
`niveau` : `courant` = entretien de base (huile, chaîne, pressions, plaquettes) ; `complet` = tout l'entretien programmé et le démontage ; `special` = outil spécifique Aprilia ou rare.

## 8. `couples.json`
```json
{ "couples": [
  { "id": "cp-bouchon-vidange", "element": Texte, "valeur_nm": 20, "plage_nm": [18, 22], "filetage": "M14x1.5",
    "freinfilet": "aucun" | "faible" | "moyen" | "fort", "graisse": Texte?, "note": Texte, "composant": "co-…", "confiance", "sources" }
] }
```

## 9. `procedures.json`
```json
{ "procedures": [
  {
    "id": "pr-vidange-huile-filtre",
    "titre": Texte, "operations": ["op-vidange-huile-filtre"],
    "difficulte": 2, "duree_min": 60,
    "prealables": ["pr-depose-sabot"],
    "outils": ["ou-…"], "pieces": ["pc-…", "cs-…"], "couples": ["cp-…"],
    "securite": Texte,
    "etapes": [
      { "n": 1, "texte": Texte, "attention": Texte?, "astuce": Texte?, "couple": "cp-…"?, "outil": "ou-…"?,
        "schema": { "fichier": "schemas/profil-droit.svg", "composants": ["co-bouchon-vidange"] }? }
    ],
    "pieges": [Texte],
    "verification": Texte,
    "videos": [ { "titre": "…", "url": "https://www.youtube.com/…", "langue": "en" } ],
    "confiance", "sources"
  }
] }
```

## 10. `carenages.json`
```json
{ "carenages": [
  { "id": "ca-flanc-gauche", "nom": Texte, "cote": "gauche" | "droit" | "centre",
    "fixations": [ { "nombre": 4, "type": "vis", "empreinte": "Torx T25" | "Allen 4 mm" | "agrafe" | "clip", "note": Texte } ],
    "prealables": ["ca-…"], "procedure": "pr-…", "pieges": [Texte], "composant": "co-…", "confiance", "sources" }
] }
```

## 11. `composants.json` — repères sur les schémas
```json
{ "vues": [
    { "id": "profil-gauche", "fichier": "schemas/profil-gauche.svg", "libelle": Texte, "largeur": 1600, "hauteur": 1000 }
  ],
  "composants": [
    { "id": "co-filtre-huile", "nom": Texte, "groupe": "moteur", "emplacement": Texte,
      "reperes": [ { "vue": "profil-droit", "x": 0.52, "y": 0.71 } ],
      "acces": Texte, "carenages_a_deposer": ["ca-…"], "operations": ["op-…"], "confiance", "sources" }
] }
```
`x`, `y` = **fractions (0-1)** de la largeur et de la hauteur de la vue, jamais des pixels.

## 12. `voyants.json`
```json
{
  "voyants": [
    { "id": "vo-pression-huile", "nom": Texte, "couleur": "rouge" | "orange" | "vert" | "bleu" | "blanc",
      "picto": "commun/pictos/huile.svg", "description_picto": Texte, "position": Texte,
      "comportement_normal": Texte, "signification": Texte,
      "gravite": 5, "action": Texte, "arret_immediat": true, "operations": ["op-…"], "confiance", "sources" }
  ],
  "tableau_de_bord": { "type": Texte, "zones": Texte, "odometre": Texte, "pieges_lecture": Texte, "millesimes"? },
  "brief_ia": { "en": "…", "fr": "…" }
}
```

## 13. `fiabilite.json`
```json
{
  "rappels": [ { "id": "rap-…", "numero": "21V-502", "organisme": "NHTSA", "date": "2021-…", "millesimes": [2021], "titre": Texte, "description": Texte, "symptomes": Texte, "action": Texte, "comment_verifier": Texte, "sources" } ],
  "problemes_connus": [ { "id": "pb-…", "titre": Texte, "description": Texte, "frequence": "rare" | "occasionnel" | "frequent", "millesimes"?, "solution": Texte, "gravite": 3, "confiance", "sources" } ],
  "mises_a_jour": [ … ],
  "rodage": { "km": 1000, "etapes": [ { "jusqu_km": 1000, "regime_max_tr_min": 0, "texte": Texte } ], "sources" },
  "controles_avant_sortie": [ { "id": "avs-…", "texte": Texte, "operation": "op-…"? } ],
  "occasion": { "checklist": [ { "id": "occ-…", "texte": Texte, "gravite": 3 } ], "apres_achat": [ { "operation": "op-…", "pourquoi": Texte } ] },
  "garantie": Texte
}
```

## 14. `regles.json` et `commun/regles-generales.json` — règles contextuelles
```json
{ "regles": [
  {
    "id": "rg-froid-pression",
    "titre": Texte,
    "condition": { "tous": [ { "variable": "meteo.temp_min_24h", "op": "<", "valeur": 5 } ] },
    "message": Texte, "conseil": Texte,
    "gravite": 2, "urgence": 60,
    "operations": ["op-controle-pression-pneus"],
    "mesures": ["me-pression-avant"],
    "duree_validite_h": 24,
    "confiance", "sources"
  }
] }
```
**Condition** = arbre de `{ "tous": [...] }`, `{ "un_de": [...] }`, `{ "non": {...} }` et de feuilles `{ "variable", "op", "valeur" }` (`op` ∈ `<`, `<=`, `>`, `>=`, `==`, `!=`, `dans` — la variable est dans la liste `valeur`, ou, pour une variable liste comme `voyants.allumes`, au moins un élément commun —, `contient` — la variable liste contient `valeur`).

**Variables disponibles** (calculées par l'appli ; une règle dont une variable est inconnue ne se déclenche pas) :

| Variable | Type | Sens |
|---|---|---|
| `date.mois` | 1-12 | mois courant |
| `date.saison` | `printemps` `ete` `automne` `hiver` | saison astronomique de l'hémisphère de l'utilisateur |
| `date.heure` | 0-23 | heure locale |
| `meteo.temp_actuelle` | °C | température actuelle |
| `meteo.temp_min_24h` / `meteo.temp_max_24h` | °C | prévisions 24 h |
| `meteo.temp_min_72h` | °C | prévisions 3 jours |
| `meteo.pluie_24h_mm` / `meteo.pluie_passee_24h_mm` | mm | pluie prévue / tombée |
| `meteo.vent_max_24h_kmh` / `meteo.rafales_max_24h_kmh` | km/h | |
| `meteo.humidite_moy_24h` | % | |
| `meteo.gel_72h` | booléen | température ≤ 0 °C prévue dans les 72 h |
| `meteo.neige_24h_cm` | cm | |
| `moto.km` | km | kilométrage actuel estimé |
| `moto.km_par_jour` | km | moyenne sur 30 jours |
| `moto.jours_sans_releve` | jours | depuis le dernier relevé |
| `moto.jours_immobilisee` | jours | estimation (relevés identiques) |
| `moto.age_mois` | mois | depuis la 1re mise en circulation |
| `moto.millesime` | année | |
| `moto.version` | id | |
| `moto.usage` | `route` `ville` `piste` `mixte` | |
| `moto.occasion_historique_inconnu` | booléen | |
| `moto.hivernage` | booléen | l'utilisateur remise sa moto l'hiver |
| `charge.pilote_kg` / `charge.passager_kg` / `charge.bagages_kg` / `charge.total_kg` | kg | |
| `charge.passager` | booléen | |
| `charge.depasse_ptac` | booléen | |
| `voyants.allumes` | liste d'ids | lus sur la dernière photo |
| `mesure.<id-mesure>` | nombre | dernière valeur saisie |
| `mesure.<id-mesure>.age_jours` | jours | âge de la dernière valeur |
| `operation.<id-op>.km_depuis` / `operation.<id-op>.jours_depuis` | | depuis la dernière réalisation |

`urgence` (0-100) = urgence propre de la règle quand elle est vraie ; l'appli la combine avec celles des opérations.

## 15. `modifications.json`
```json
{ "categories": [ { "id": "echappement", "nom": Texte } ],
  "modifications": [
  { "id": "md-akrapovic-slip-on", "categorie": "echappement", "marque": "Akrapovič", "modele": "Slip-On Line (Titanium)",
    "references": [ { "ref": "S-A6SO…", "note": Texte } ], "millesimes": [ … ],
    "homologation": "route" | "route_avec_conditions" | "piste" | "inconnue", "legal_fr": Texte,
    "gain": Texte, "poids": Texte, "cartographie_requise": "non" | "conseillee" | "obligatoire",
    "difficulte": 2, "outils": ["ou-…"], "prix": Prix, "lien": "https://…", "note": Texte, "confiance", "sources" }
] }
```

## 16. `commun/prix-zones.json`
```json
{ "pays": [ { "code": "FR", "devise": "EUR", "taux_horaire": { "concession": Prix, "independant": Prix }, "coef_pieces": 1.0,
    "zones": [ { "id": "paris-idf", "libelle": Texte, "coef_main_oeuvre": 1.25, "detection": { "codes_postaux": ["75", "77", "78", "91", "92", "93", "94", "95"] } },
               { "id": "grande-ville", … , "detection": { "population_min": 200000 } },
               { "id": "ville-moyenne", … }, { "id": "rural", … } ] } ],
  "methode": Texte, "sources": […] }
```

## 17. `sources.json` et `credits.json`
```json
{ "sources": [ { "id": "src-manuel-proprietaire", "titre": "Manuel du propriétaire RS 660 (2Q000420, éd. 11/2020)", "type": "officiel" | "fabricant" | "revendeur" | "presse" | "forum" | "video" | "autre", "url": "https://…", "consulte": "2026-10-15" } ] }
```
```json
{ "images": [ { "fichier": "images/profil-gauche-r1.jpg", "titre": "…", "auteur": "…", "licence": "CC BY-SA 4.0", "url_licence": "https://…", "url_source": "https://commons.wikimedia.org/…", "modifications": Texte } ],
  "schemas": { "auteur": "Torque", "licence": "CC BY 4.0" } }
```

## 18. Règles de contenu
- **Ne jamais inventer** une valeur, une référence, un couple ou un prix : une donnée introuvable est **absente** (champ omis) ou marquée `"confiance": "incertain"` avec une note.
- Pas de logo ni d'image protégée (manuels, éclatés, photos de presse) dans ce dépôt : les éclatés sont **liés** (`lien_eclate`).
- « Aprilia », « RS 660 » : mentions textuelles nominatives seulement. L'application affiche l'avertissement de non-affiliation.
