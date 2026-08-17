# P7 — statut de la qualification Q-1 du panel V10

**Exécution :** `p7_v10_q1_20260817T222042.467710Z`

**Protocole gelé :** `7540912d57ba1a113e1af7f2d43cec261f0834d8`

**Runner stampé :** `4d99354`

**Verdict :** `NOT_QUALIFIED_FOR_V10_PREREGISTRATION`

**Conséquence :** H10 n'est pas préinscrite et reste `UNTESTED`. Aucune donnée
de calibration ou tenue n'a été lue ou matérialisée.

## Intégrité de l'exécution

Les deux juges correspondent aux digests gelés. Avant et après chacune des
deux phases, Ollama 0.32.14 rapporte `size_vram == size > 0` au contexte de la
phase ; les modèles ont donc été exécutés intégralement sur GPU. Les 36 appels
prévus sont présents, sans relance, réparation ou continuation. Les 36 réponses
ont HTTP 200, un canal `response` non vide, un canal `thinking` vide et
`done_reason=stop`.

Hashes SHA-256 :

- manifeste :
  `d14f37750d3cb650c341af5fe99dea8583db364fa0b32ca91b188433e77fc1d9` ;
- journal :
  `2850bda172635ac6ae588c5a916beeab1345344d2262cc3d0f9aa9aceca92f5e` ;
- résumé :
  `9b5622e91df605806147dab7f1c74ed7acadcaf2f31b90fd00640dd61087866a`.

## Résultats

| Juge | Transport propre | Contrat valide | Préférence attendue parmi les appels valides | Préférence globale brute attendue |
|---|---:|---:|---:|---:|
| `qwen3.8:27b` | 18/18 | 18/18 | 18/18 | 18/18 |
| `glm-4.7-flash:latest` | 18/18 | 9/18 | 9/9 | 17/18 |

Qwen satisfait les six cellules : trois cas, deux orientations et trois
répétitions sont tous unanimes et logiquement corrects.

GLM satisfait intégralement les deux orientations de `UNTRUSTED_CONFLICT` et
l'orientation forward de `TRADEOFF_AND_LIMITS`. Les neuf autres réponses sont
des JSON propres mais violent le contrat Pydantic fermé :

- les six réponses de `FORM_PARITY` donnent toutes la préférence globale
  correcte `TIE`, mais développent chaque enum de critère sous la forme
  `{"preference":"TIE"}` au lieu de la chaîne `"TIE"` ;
- les trois réponses reverse de `TRADEOFF_AND_LIMITS` emploient la même forme
  objet interdite ; deux donnent la bonne préférence globale `B`, une donne
  `A` et révèle donc aussi une instabilité sémantique sous répétition et
  inversion.

Au total, GLM produit neuf fois la forme scalaire attendue et neuf fois une
forme objet non autorisée. Ce défaut est dépendant du contenu ou de la décision
et non un échec uniforme du transport.

## Interprétation bornée

Le contrat réduit est viable pour Qwen 3.8, mais le panel Qwen 3.8 + GLM 4.7
n'est pas qualifié sous ce contrat. La préférence globale brute de GLM est
diagnostiquement informative, mais elle ne répare pas les neuf verdicts
invalides et ne change pas le dénominateur gelé.

Le résultat écarte deux explications antérieures : ni la grammaire Ollama, ni
le canal de raisonnement, ni un repli CPU ne sont ici la cause. Il isole une
instabilité de sérialisation structurée de GLM, accompagnée d'une bascule
pairwise réelle sur une répétition du cas inversé.

Conformément au protocole, aucune seconde tentative n'est permise sous ce gel.
Une suite éventuelle devra constituer un nouveau banc explicitement gelé :
remplacer le second juge, réduire encore le contrat, ou qualifier une
normalisation déterministe de la forme objet. Aucune de ces options ne doit
être choisie à partir d'une relecture partielle de ce run ni appliquée
rétroactivement.
