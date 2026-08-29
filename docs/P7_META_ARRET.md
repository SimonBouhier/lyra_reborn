# P7 — Règle méta d'arrêt du programme de qualification du panel

**Nature :** règle de gouvernance du programme d'évaluation, pré-enregistrée —
aucune mesure, aucune donnée

**Gel initial :** `TO_BE_STAMPED`

## Contexte

De V3 à V10, huit campagnes consécutives se sont arrêtées avant toute mesure
confirmatoire : aucune hypothèse H n'a jamais été testée. Chaque arrêt est
individuellement rigoureux ; collectivement, la couche d'évaluation consomme
le programme sans critère d'arrêt propre. Q-1 (gel
`7540912d57ba1a113e1af7f2d43cec261f0834d8`) a qualifié Qwen 3.8 seul (18/18
sur les six cellules) et disqualifié GLM-4.7-flash. La décision de remplacer
le second juge par `gemma3:27b` (digest Ollama `a418f5838eaf`, 17 Go — à ne
pas confondre avec `gemma3:latest`, 4B) est prise.

La présente règle applique au programme d'évaluation lui-même la discipline
d'arrêt appliquée à Origami v7 : un budget gelé avant les bancs, et une
bascule écrite avant de savoir si elle servira. But : que l'échec éventuel
produise un verdict, pas un neuvième arrêt.

## 1. Budget gelé

Le design « panel de deux juges locaux de familles distinctes »
(STATE_OF_ART §3.5) dispose d'exactement **deux bancs restants** :

1. **Banc A — admission de `gemma3:27b`**, sur le patron de l'admission
   Qwen 3.8 v2 (`docs/P7_QWEN38_ADMISSION_V2.md`) : gel propre, digests,
   GPU intégral (`size_vram == size`), transport et contrat comptés
   séparément ;
2. **Banc Q-2 — qualification du panel** Qwen 3.8 + gemma3 sous le contrat
   réduit de Q-1, **inchangé**.

Chaque banc rend exactement un verdict sous son propre gel. Tout résultat
autre que « admis » (banc A) ou « qualifié » (banc Q-2) — y compris une
invalidation d'intégrité — consomme le banc. Aucune substitution : pas de
candidat de remplacement si l'admission échoue, pas de réduction
supplémentaire du contrat, pas de normalisation ajoutée après coup, pas de
seconde tentative sous un même gel (règle Q-1 reconduite).

## 2. Conditions de bascule

La bascule du §3 s'active dès que l'un des cas suivants survient :

- le banc A rend `gemma3:27b` non admis ;
- le banc Q-2 rend le panel non qualifié.

Si le banc Q-2 qualifie le panel, la présente règle s'éteint et la
préinscription de H10 devient possible.

## 3. La bascule pré-écrite (décision Simon, 2026-08-29)

Si le budget s'épuise sans panel qualifié :

1. **Verdict du programme : `PANEL_BIJUGE_CLOS`.** Le design deux-familles
   est fermé comme résultat négatif d'instrumentation — publiable, au même
   titre que la clôture Origami v7. Il ne rouvre pas sans élément **externe**
   au programme (nouveau modèle local à la capacité démontrée ailleurs, ou
   changement matériel) — jamais sur relecture des échecs passés.
2. **La série H se poursuit en juge unique `qwen3.8:27b`**, avec :
   - contrôles d'auto-cohérence : répétitions et inversion d'ordre,
     unanimité requise par cellule (reconduits de Q-1) ;
   - vérifications déterministes comptées séparément : validité du contrat,
     résolution des segments sources, couverture des tours ;
   - affaiblissement documenté : chaque verdict H portera la mention
     « juge unique — indépendance inter-famille non disponible » ;
     STATE_OF_ART §3.5 sera amendé au moment de la bascule, pas avant.

## 4. Ce que cette règle interdit

- ouvrir un troisième banc de qualification bi-juge sans document successeur
  explicite, motivé par un élément nouveau externe au programme ;
- choisir quoi que ce soit rétroactivement à partir des données Q-1
  (reconduction du gel Q-1) ;
- convertir une invalidation d'intégrité en banc « qui ne compte pas ».

## 5. Ce que cette règle ne décide pas

- le contenu des gels des bancs A et Q-2 — leurs documents propres, à geler
  chacun avant leur exécution ;
- H10 elle-même — préinscription séparée, après qualification ;
- rien d'empirique : ce document ne lit ni ne produit aucune donnée.
