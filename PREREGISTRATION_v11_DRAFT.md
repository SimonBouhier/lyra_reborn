# Pre-Registration v11 — BROUILLON, NON GELÉ

> **Ce document n'est pas une préinscription tant que Simon Bouhier ne l'a pas
> gelé.** Tant qu'il porte ce bandeau et le nom `_DRAFT`, il n'engage rien et
> aucun run ne peut s'y référer. Le gel consiste à : trancher les quatre points
> marqués **[DÉCISION]**, neutraliser la mise à jour automatique d'Ollama,
> constater la version réellement servie, renommer le fichier en
> `PREREGISTRATION_v11.md`, committer, puis estampiller le commit de gel.

**Frozen on**: TO_BE_FROZEN
**Frozen by**: Simon Bouhier
**Git commit at freeze**: TO_BE_FROZEN

## Hypothesis

H11 : conditionnellement à un premier tour strictement commun, la politique
adaptative existante de Lyra produit, sur les deux tours suivants, un avantage
de qualité éditoriale robuste et pratiquement utile face à la meilleure
politique statique simple observée en calibration, sur 60 contenus publics
réels et tenus, à modèle, gabarits et enveloppe de calcul comparables.

H11 est évaluée séparément sur trois modèles producteurs locaux et soutenue
globalement seulement si au moins deux modèles sur trois franchissent toutes
les portes gelées.

L'hypothèse est **mot pour mot** celle de H8/H9/H10. Ni l'instrument de
jugement, ni les données, ni les seuils ne changent. Seul le **runtime**
change, et c'est la seule raison d'être de cette préinscription.

## Pourquoi V11 et non la poursuite de V10

V10 a franchi Q0 le 2026-08-29 (`Q0_PASSED`, 18/18, run
`p7_v10_q0_20260829T211254.467768Z`) sur Ollama **0.32.15**, la version que sa
préinscription épinglait. Le 2026-08-30 à 00 h 24, Ollama s'est mis à jour
automatiquement vers **0.33.2**.

Q0 est la « qualification du juge en condition de campagne ». Mesurer H10 sur
un moteur différent de celui qui a qualifié le juge aurait laissé, dans la
note de résultats, une discontinuité irréparable — la re-qualification étant
interdite par le gel V10. V10 a donc été arrêtée : `V10_ARRETEE_APRES_Q0`,
`H10 UNTESTED` (`docs/P7_V10_STATUS.md`).

V11 reprend le même design **entièrement**, sur un runtime tenu de bout en
bout, avec un Q0 neuf exécuté sur ce runtime.

## Incorporation

V11 conserve par incorporation toutes les décisions scientifiques et
opérationnelles de V10 (gel `bc8497f6bb083ff2c27632ded784e13ea264cc5d`),
elles-mêmes incorporées de V8 (`88590fcc…`) via V9 (`882f10cc…`) : hypothèse,
corpus, hash du pool, seed globale `20260817`, sélection, segmentation,
producteurs et digests, fixtures Q0, prompts producteurs, rubrique,
politiques, knobs, mapping 128–768, calibration de 12 cas, tenu de 60 cas,
trajectoires, contre-balancement 30 ABBA / 30 BAAB, evidence pack et son
inversion, seuils Q1 et C0–C12, observables O1–O24, logique de verdict par
producteur et globale, clause anti-confirmation.

Les deux amendements de V10 sont incorporés et deviennent partie du gel V11 :

- `docs/P7_V10_PRERUN_AMENDMENT.md` — portée épistémique des énoncés et
  répartition des répétitions. Chaque verdict V11 porte les mêmes mentions ;
- `docs/P7_V10_PRODUCER_CONTEXT_AMENDMENT.md` — fenêtre des producteurs, dont
  la substance est promue en §Runtime ci-dessous.

Le verdict de programme **`PANEL_BIJUGE_CLOS`** (`docs/P7_META_ARRET.md`, gel
`89d22f9`) reste en vigueur : V11 est un design **juge unique**, et son échec
ne rouvrirait ni le panel bi-juge ni un troisième banc de qualification.

## Instrument : inchangé

Juge unique `qwen3.8:27b`, digest
`22130167c4c20e20c7b71454612966ca8e8171e9b3cc8ab6ce8aa6cbfec79643`, famille
`qwen35`, quantification `Q4_K_M`. Contrat réduit de Q-1 inchangé. Transport
Ollama `JSON_ONLY_PROMPTED` : `think=false`, `stream=false`, température 0,
`num_predict=512`, `num_ctx=32768`, `format=json`, contrat dans le prompt.
Deux appels juge par paire, ordre gelé
`sha256(seed ‖ "judge_order" ‖ judge_digest ‖ pack_sha256 ‖ orientation)`,
un seul bloc, digest revérifié avant et après.

**Affaiblissement documenté**, reconduit sans changement : l'indépendance
inter-famille entre juges n'est pas disponible ; chaque énoncé de verdict V11
porte la mention « juge unique — indépendance inter-famille non disponible ».

## Scope

### Runtime — le seul changement de fond

Python 3.14.7, Pydantic 2.13.4, Ollama **[DÉCISION 1 : version à constater au
gel, `0.33.2` observée le 2026-08-30]**.

Trois exigences nouvelles, qui répondent aux deux incidents de V10 :

1. **Fenêtre des producteurs : 32 768 tokens**, imposée au serveur
   (`OLLAMA_CONTEXT_LENGTH`) et jamais dans les requêtes — les payloads
   producteurs restent ceux du design gelé, sans `num_ctx`. Valeur non
   arbitraire : contexte maximum de `mistral:latest`, donc la seule que les
   quatre modèles acceptent tous, et celle du juge. Marge 9,3× sur le pire cas
   des 72 prompts (~3 500 tokens) : aucune troncature possible.
2. **Le runtime est tenu, pas seulement épinglé.** La mise à jour automatique
   d'Ollama est neutralisée **avant** le gel et le reste pendant toute la
   campagne : le serveur est lancé à la main depuis le binaire épinglé
   (`ollama serve`), sans l'application de la zone de notification, qui est
   l'agent de mise à jour. **[DÉCISION 2 : valider ce mode d'exécution.]**
3. **La version est vérifiée, pas constatée.** Tout écart entre la version
   servie et la version gelée arrête la phase **avant** son verrou, et est
   revérifié autour de chaque bloc producteur et du bloc juge. Une mise à jour
   survenant en cours de phase est donc vue et non absorbée.

Versions, digests, fenêtres et preuves GPU entrent au manifeste de chaque
phase. Aucun écart n'est corrigé après verrou.

### Données et budget — inchangés

Corpus, hash, seed, sélection, segmentation, calibration de 12 cas, tenu de
60 cas, trajectoires, cinq appels producteur par cas complet,
contre-balancement 30/30 par producteur : ceux de V8.

**[DÉCISION 3 — réemploi du jeu tenu.]** V10 n'a lu ni généré aucun cas : les
12 cas de calibration n'ont jamais été ouverts et les 60 cas tenus sont
intacts. V11 les reprend donc à l'identique, ce qui est la condition pour que
le design reste le même. La clause V8 « une version successeure utilise un
nouveau jeu tenu » visait un successeur formulant une hypothèse *distincte*
après avoir consommé son jeu tenu ; ici l'hypothèse est identique et rien n'a
été consommé. **À confirmer explicitement au gel** — c'est le point le plus
discutable de cette préinscription.

Plafonds inchangés : 18 appels juge Q0 ; 432 producteur et 432 juge en
calibration ; 900 producteur et 360 juge sur le principal — **2 142 appels**.
Contrôles opérationnels, pas des quotas.

### Exécution

Commande unique `scripts/p7_v10.py run` **[DÉCISION 4 : renommer en
`p7_v11.py` ou reparamétrer le runner existant sur le gel V11 ; le harnais
lui-même est inchangé et déjà testé]** : Q0 → calibration → tenu → scoreur.
Un verrou exclusif par phase, créé après la preuve GPU de sa phase.
Interrompre après un verrou invalide la phase ; aucune reprise, aucune
seconde tentative sous ce gel.

La chaîne peut redémarrer sans rejouer une phase close : un verrou Q0 assorti
d'un résumé `Q0_PASSED` sous **ce** gel fait reprendre le résultat sans le
réexécuter, et sa provenance entre au manifeste de la phase suivante ; un
verrou sans résumé passant fait refuser la commande. Aucune phase ne tourne
deux fois.

Avant tout run vivant : tests hors-ligne verts, smoke de cycle de vie sans
Ollama ni corpus ni fixture, et préflight prouvant pour les quatre modèles
`size_vram == size > 0` aux fenêtres spécifiées.

## Q0 — qualification du juge sur le runtime de V11

Q0 est **rejouée intégralement** : trois fixtures V8, deux orientations, trois
répétitions, `3 × 2 × 3 = 18` appels, sous le contrat réduit et le transport
ci-dessus. C'est la raison d'être de V11.

**Aucune donnée de la Q0 de V10 n'entre dans un verdict V11.** Son succès sur
0.32.15 motive le design ; il ne le qualifie pas sur le runtime de V11. Cette
interdiction est de même nature que celle qui écarte les bancs d'admission et
Q-1.

Conditions de passage, seuils et conséquence d'un échec
(`V11_ABORTED_BEFORE_CALIBRATION`, H11 `UNTESTED`) : identiques à V10.

## Q1, C0–C12, verdicts

Repris mot pour mot de V10, avec `H11` substitué à `H10`. Aucun seuil,
dénominateur, ordre ni table de caractéristiques opératoires n'est modifié.

Q1 conserve ses quatre clauses, dont la première — « le round-robin gelé est
complet sans relance sélective » — porte sur la conduite du run et est
constatée par l'exécuteur à côté des trois autres.

## Anti-confirmation clause

La clause de V10 est reconduite intégralement, et étendue :

- aucun échec, `TIE`, désaccord, instabilité, erreur, ordre défavorable ou
  réponse invalide selon Pydantic ne peut être retiré du dénominateur ;
- aucun prompt, fixture, seuil, contrat, enum, ordre, modèle ou paramètre
  n'est ajusté après l'ouverture de Q0 — **la version du runtime et les
  fenêtres de contexte sont explicitement des paramètres au sens de cette
  clause** ;
- aucune donnée des bancs d'admission, de Q-1, ni de la campagne V10 — Q0
  comprise — ne peut être recyclée dans un verdict V11 ;
- l'échec de toute porte ne rouvre ni le panel bi-juge ni un troisième banc ;
- une correction après gel qui dépasse ce qui est décrit ici, change le
  contrat réduit, le canal `response`, autorise une relance ou touche
  Q0/Q1/C0–C12 annule V11 et exige V12 ;
- un résultat positif autorise une ablation ou une réplication, jamais un
  déploiement ni une revendication de supériorité générale.

La continuation d'ingénierie reste valide indépendamment du verdict.

## Ce que V11 ne peut pas devenir

V11 est une **reprise à runtime tenu**, pas une nouvelle question. Si elle
échoue à Q0, le constat sera que le juge ne se qualifie pas sur ce moteur —
un fait sur l'instrument, pas sur H11, et le dixième arrêt du programme. Rien
dans ce document n'autorise à essayer un troisième moteur pour obtenir un Q0
passant : un tel essai serait une recherche de résultat et non une mesure.
