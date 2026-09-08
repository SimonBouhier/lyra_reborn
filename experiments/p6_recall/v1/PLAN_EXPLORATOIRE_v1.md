# P6 — plan d'analyse exploratoire des rappels corrigés, v1

**Date : 8 septembre 2026.** Plan approuvé dans son principe par Simon ;
spécification opérationnelle par l'agent. Sceau détaché :
`PLAN_EXPLORATOIRE_v1.sha256`. Ce fichier et son sceau deviennent immuables après gel.
Cette expérience est distincte de P7 et de ses préenregistrements numérotés.

## 1. Question et niveau de conclusion

Dans quelles conditions un assistant utilise-t-il la valeur actuellement déclarée
lorsqu'un passage rappelé contient une information ancienne et sa correction ?
Le diagnostic croise quatre interventions de présentation et quatre configurations
installées. Il cherche des effets et des interactions ; il ne qualifie pas un
modèle pour l'usage général et ne tranche pas une hypothèse confirmatoire.

Les mécanismes candidats déjà cadrés sont : influence d'une ancienne consigne,
lisibilité du statut des versions, frontières des messages, présence d'un ancien
accusé assistant, et dépendance de leurs effets à la configuration du modèle.
Les effets d'architecture, de template et de modèle ne sont pas nécessairement
exclusifs. Un phénomène partagé ne permet pas d'attribuer sa cause à Ollama ou
aux poids. Une différence entre configurations ne constitue pas un effet pur de famille.

Il n'existe pas encore d'hypothèse confirmatoire ni de seuil d'effet validés.
Ils seront formulés après ce diagnostic, puis préenregistrés avant toute sortie
de confirmation. Aucun seuil d'effet ni « soutien » n'est inventé pour cette collecte.
Les exemples ayant motivé le chantier et les présentes fixtures sont du développement.

## 2. Population mesurée et isolement

Panel fixe : `gemma3:latest` (4.3B), `llama3.1:8b`, `granite3.3:latest` (8.2B),
`mistral:latest` (7.2B), tels qu'installés. Les noms ne sont pas les identités
suffisantes : chaque digest, runtime, template, paramètres et métadonnées sont
capturés par `prepare`. Aucune mise à jour, aucun pull, aucune substitution.
Le contrat runtime visé est celui déjà inspecté, Ollama 0.33.3.
Qwen est hors de ce premier panel ; ses versions restent intactes.

Le runner utilise HTTP local et des stimuli synthétiques. Aucune conversation
personnelle, base utilisateur, donnée tenue P7, réponse de relecteur externe ou
pièce de confirmation n'entre dans les requêtes. Aucune mémoire dérivée ni
recherche documentaire n'est appelée pendant une génération.

L'assembleur diagnostique est séparé de l'application. Les tests vérifient la
parité de sa cellule B0_C0_D0 avec le rappel produit par `app/context.py`, pour
les deux niveaux de A. Cette parité ne vaut pas qualification de tout le serveur.
Les données restent des déclarations d'une fiction, pas des faits vérifiés.

## 3. Corpus et unités

Le fichier `corpus.py` contient six patrons : classement d'un dossier, code d'un
casier, salle d'un rendez-vous, quai d'une navette, nom d'une liste, marque d'un colis.
Chaque patron croise deux sens de mise à jour et deux rôles de provenance
(`user`, `assistant`). Cela donne **24 scénarios dérivés de six patrons**.

Les rôles de provenance sont des étiquettes dans le passage rappelé ; celui-ci
reste un message effectif `user`. Les 24 scénarios ne sont pas 24 échantillons
indépendants d'un usage réel. Les graines ne sont pas de nouveaux exemples.
Les analyses conservent `template_id`, `case_id`, condition, modèle et graine.
Toute future incertitude inférentielle doit tenir compte du regroupement par
patron ; aucun intervalle de population n'est revendiqué dans cette version.

Une seule question et une seule instruction de sortie sont conservées pour
toutes les cellules d'un scénario : une valeur seule, ou `inconnu` si absente.
Ce format fermé facilite la vérification, mais modifie la tâche naturelle.
Une étude ultérieure en réponse libre restera nécessaire ; elle ne sera pas
confondue avec la présente mesure d'exactitude sous contrat court.

## 4. Plan factoriel complet

| Facteur | Niveau 0 | Niveau 1 |
|---|---|---|
| A | Ancienne consigne absente | Ajouter seulement « Réponds simplement : noté. » après le fait ancien |
| B | Balisage actuel du rappel produit | Marquer explicitement version ancienne remplacée et version actuelle |
| C | Source et correction dans un même message user | Correction dans un second message user |
| D | Ancien accusé absent | Message assistant `Noté.` après source/correction, avant la question |

Les 16 combinaisons sont présentes dans chaque scénario, graine et modèle.
Changer C conserve exactement les caractères concaténés, l'ordre et les rôles
user ; le template peut néanmoins ajouter des séparateurs propres au moteur.
Changer B modifie le texte, sa longueur et la répétition des identifiants :
l'effet estimé porte sur ce rendu complet, pas une abstraction de « clarté ».
D ajoute simultanément un contenu, un rôle assistant et une frontière. Il ne
permet pas d'isoler à lui seul une autorité intrinsèque du rôle assistant.

Chaque cellule utilise les graines **1001, 1002, 1003** à température **0.3**.
Les graines identiques ne promettent pas des tirages équivalents entre familles
ni une reproductibilité bit à bit. Profil : `num_ctx=8192`, `num_predict=1024`,
`top_p=0.9`, `repeat_penalty=1.0`, `think=false`, `truncate=false`, `shift=false`.
Les autres paramètres sont ceux du modèle installé et sont consignés.

Total factoriel : **4 × 16 × 24 × 3 = 4 608 appels**.

## 5. Témoins, séparés des taux factoriels

| Témoin | Valeur attendue |
|---|---|
| `current_only` | Valeur actuelle seule fournie |
| `old_only` | Valeur ancienne, seule déclaration en vigueur |
| `unchanged` | Valeur ancienne confirmée sans changement |
| `unknown` | `inconnu`, aucune valeur renseignée |
| `other_subject` | Valeur ancienne ; la correction vise explicitement un sujet différent |
| `multiple_updates` | Dernière valeur, après une valeur de transit puis correction finale |

Ces témoins ont leur vérité propre. Dans trois témoins, répondre par la valeur
nommée « ancienne » dans le scénario est correct. Ils ne sont jamais ajoutés
au taux factoriel. `multiple_updates` montre plusieurs corrections au modèle :
c'est un stimulus expérimental, car le produit n'injecte que la dernière tête.

Total témoins : **4 × 6 × 24 × 3 = 1 728 appels**.
Collecte complète : **6 336 appels**, hors quatre appels d'admission technique.
L'admission vérifie transport, canal final non vide et compteurs positifs ; elle
ne sélectionne pas les facteurs ou les modèles selon leur succès sémantique.

## 6. Ordre, budgets et continuité

Chaque répétition contient un bloc complet de 528 stimuli par modèle. L'ordre
des modèles est décalé cycliquement entre les trois répétitions. L'ordre interne
des cas/cellules/témoins est mélangé avec `20260908 + indice_de_répétition` et
identique entre modèles de la même répétition. La liste complète est conservée
avant le premier appel et ne dépend pas des sorties. Les trois rotations ne
constituent pas un carré latin complet à quatre modèles.

Une seule invocation du runner détient le verrou OS de la campagne. Les appels
sont séquentiels, sans compétition créée par le runner sur le GPU. Version et
digest sont contrôlés au début de chaque bloc et à la fin de l'invocation ; les
empreintes du code sont vérifiées au chargement et aux frontières de blocs.
Une modification extérieure entre contrôles reste une limite explicitement admise.
La disposition GPU chargée est capturée à l'admission ; elle n'est pas une preuve
de résidence identique à chaque appel ni une garantie matérielle générale.

Le délai par requête est 90 secondes. Un incident de transport ou une réponse
inexploitable est conservé puis interrompt l'invocation ; aucun réessai automatique
de cet appel. Une reprise continue à la prochaine cellule après examen technique.
Une réservation dont le résultat durable manque devient `uncertain_execution` ;
elle n'est pas rejouée. Les sorties coupées par la limite sont conservées comme
`output_truncated`, sans allonger leur budget.

Les pauses par nombre maximal d'appels sont permises pour gérer le temps de
calcul ; elles ne changent pas l'ordre ni l'effectif et ne permettent pas une
analyse comparative du préfixe collecté. Le runner affiche seulement progression
et statuts techniques. L'analyse automatique exige la collection complète.
Une impossibilité de finir donne `COLLECTE_INCOMPLETE`, sans classement partiel.

## 7. Mesures et analyse fixées

Le texte complet est normalisé par NFKC, casse Unicode, réduction des espaces
et retrait des seuls caractères terminaux `.!?,;:…`. Les accents, ponctuations
internes, guillemets, Markdown et préfixes restent présents. Comparaison exacte
à la valeur attendue. Aucun `contains(valeur)` ni juge LLM n'attribue le succès.

Catégories secondaires : valeur actuelle, valeur ancienne, abstention,
autre/hors format. L'étiquette « ancienne » exige la réponse entière égale à
cette valeur. Une phrase qui cite ou nie une valeur n'est pas interprétée par
heuristique. Le marqueur lexical `noté` est un indicateur distinct, sans attribution
causale. Les sorties brutes demeurent disponibles pour une lecture contradictoire.

Les erreurs techniques, réponses vides, troncatures et exécutions incertaines
sont séparées des catégories de texte. Elles valent zéro succès dans le taux
sur appels planifiés, sans être interprétées comme erreurs de croyance.
Le taux conditionnel sur réponses techniquement valides est aussi rapporté.

Pour chaque modèle, le taux principal est la moyenne à poids égaux des 1 152
cellules/répétitions factorielles. Chaque facteur F a pour effet descriptif :
`moyenne(succès | F=1) - moyenne(succès | F=0)`.
Les six interactions de deux facteurs F,G sont :
`p11 - p01 - p10 + p00`, en moyennant également les autres facteurs, cas et graines.
Les scores individuels permettent de distinguer patron et rôle de provenance.
Les témoins ont leurs propres dénominateurs et succès par configuration.

Les poids sont identiques entre les six patrons, chacun ayant quatre variantes.
Pas de classement global des familles, de p-value, de seuil de sélection ajusté
aux sorties ni de verdict confirmatoire. Les effets décrivent exclusivement
ce corpus, ces textes, ces configurations et ces conditions d'exécution.
Une moyenne n'efface pas les interactions ni les incidents techniques.

## 8. Qualification et statut de la collecte

Q1 : sceau du plan, empreintes de code et corpus concordants.
Q2 : aucun changement de modèle/runtime détecté, aucun contenu hors périmètre.
Q3 : scoreur testé sur cas adversariaux fabriqués et parité du rendu courant vérifiée.
Q4 : admission technique des quatre configurations, sans substitution.
Q5 : toutes les cellules planifiées ont une trace terminale, y compris leurs incidents.
Q6 : payload réservé, corps envoyé, corps reçu et objet décodé concordent ;
les réponses ont des empreintes détachées vérifiées. La concordance porte sur
les corps disponibles : un incident de transport peut ne laisser aucun corps
reçu, et `uncertain_execution` peut ne laisser que la réservation. Ces absences
doivent être qualifiées explicitement et ne deviennent pas des réponses valides.

Protocole rompu ou trace altérée : `INVALIDE`, sans conclusion comparative.
Admission manquante ou collecte incomplète : `INCONCLUSIF` pour le diagnostic
comparatif prévu. Collecte complète et contrôles concordants :
`DESCRIPTIF_EXPLORATOIRE_DISPONIBLE`. Ce dernier statut n'est pas un PASS d'usage.
Les erreurs terminales conservées ne disparaissent pas du descriptif ; leur
importance dans un contraste doit rester visible et discutée.

Les sceaux détectent une modification accidentelle. Ils ne constituent pas une
preuve anti-altération contre quelqu'un pouvant réécrire fichiers et empreintes.
Aucun commit, push ou horodatage externe n'est déduit du gel local.
La campagne conserve une copie exacte du plan et de son sceau, référencée par
un chemin relatif ; les sources exportées gardent leur arborescence. La relecture
et l'analyse des traces peuvent ainsi être déplacées sans dépendre du poste auteur.

## 9. Confirmation et impartialité des relectures

Aucune donnée de confirmation n'est créée ou consommée dans cette campagne.
Après diagnostic : formuler la ou les hypothèses, choisir le comparateur,
définir la différence utile, dimensionner le corpus et les incertitudes, puis
figer un préenregistrement confirmatoire distinct avant ses générations.
Les nouvelles situations doivent différer sémantiquement des six patrons,
pas seulement par permutation de mots. Si une représentation ou un modèle est
sélectionné après exploration, cette sélection sera déclarée.

Trois indépendances restent distinctes : nouvelles données, relecteur séparé,
exécution externe. Les sous-agents de construction/relecture actuels sont des
contributeurs internes ; ils ne satisfont pas l'indépendance externe demandée.
Simon transmet manuellement le même paquet à chaque destinataire, dans des
conversations séparées. Les destinataires ne reçoivent ni nos conclusions ni
les retours des autres avant leur premier rapport. Une seconde confrontation
contradictoire, si souhaitée, reçoit un statut et un dossier différents.

Paquet méthode : contexte neutre, présent plan/scellé, corpus, contrats,
code et formulaire. Paquet résultats : les mêmes pièces plus requêtes/réponses
brutes et conditions ; scores agrégés et synthèse auteur restent séparés.
Une allowlist ferme les pièces fournies ; aucun accès au reste du dépôt n'est
nécessaire. Les modes lecture, analyse locale et réplication sont déclarés par
le relecteur selon la mission explicitement transmise. Un rapport documentaire
ne devient pas une réplication, et des répétitions avec le même modèle ne sont
pas une indépendance des familles.

## 10. Révision et livrables

Après gel, toute correction de corpus, facteur, scoreur ou runner impose une
nouvelle version du plan et une nouvelle campagne ; les anciens fichiers restent.
Une correction de l'outil d'export seule ne permet pas de modifier la collecte.
Rapports : manifeste, corpus/cellules, jobs complets, métadonnées modèles,
qualification, réservations/requêtes/réponses scellées, progression, analyse
descriptive séparée, archives exportables et retours avec provenance.
Les données de run sont sous `data/runs/p6-recall/`, ignorées par Git ; les archives
partageables sous `output/p6-recall/`. Elles ne sont pas automatiquement publiées.

## 11. Fondements et limites de transfert

Le croisement complet permet de distinguer effets principaux et interactions
dans le plan choisi : [NIST, plans factoriels](https://www.itl.nist.gov/div898/handbook/pri/section3/pri3331.htm).
[LongMemEval](https://arxiv.org/abs/2410.10813) distingue notamment extraction,
mise à jour et abstention ; le présent corpus ne reprend ni son score ni son
jeu d'évaluation. Les travaux sur [la hiérarchie d'instructions](https://arxiv.org/abs/2404.13208)
motivent l'examen d'une ancienne consigne, sans établir le mécanisme local.
[Lost in the Middle](https://arxiv.org/abs/2307.03172) motive une extension future
position/longueur ; aucun effet de long contexte n'est testé dans ce plan court.
Les biais de position, budgets et critères identifiés dans les travaux antérieurs
du projet sont des vigilances reprises, pas des résultats transposés à P6.
