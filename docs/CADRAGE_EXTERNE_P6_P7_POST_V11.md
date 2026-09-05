# Cadrage externe P6–P7 après V11

> **Actualisation documentaire du 2026-09-05.** La persistance SQLite a été
> livrée depuis la première rédaction, au commit `d7353d4`. L'état courant
> et les limites conversationnelles sont décrits dans [ETAT_ACTUEL](ETAT_ACTUEL.md).
> Le cadrage métrologique ci-dessous reste un document de travail, sans nouveau gel.

**Date :** 2026-09-02
**Statut :** document de travail pour audit externe et recherche bibliographique
**Autorité :** non normatif — ce document n'est ni une préinscription, ni un gel,
ni une autorisation de lancer V12
**État de référence :** branche `codex/p7-meta-arret`, HEAD `6e7d694`, avec la
réparation P6 des sessions encore locale au moment de la rédaction

## Résumé exécutif

Lyra est une couche de contrôle, de mémoire et d'exploration au-dessus de
modèles locaux. Deux chantiers se sont progressivement confondus : construire
une application utilisable (P6) et démontrer qu'une politique adaptative prend
de meilleures décisions qu'une politique statique simple (P7).

V11 est la première campagne P7 à avoir produit une calibration complète. Elle
n'a pas testé l'hypothèse finale : la porte Q1 a arrêté la campagne avant les
60 cas tenus. Cet arrêt a protégé le seul jeu encore vierge. Il a aussi montré
que l'instrument de jugement n'était pas dépourvu de signal, mais qu'il restait
insuffisamment stable et confondu avec la position, la longueur et le budget de
génération.

La décision actuelle est donc :

1. faire de P6 le chantier principal et rendre Lyra utilisable localement ;
2. maintenir P7 en atelier métrologique, sur données de développement ;
3. séparer l'entretien de l'instrument du futur test gelé de l'hypothèse ;
4. ne concevoir V12 qu'après examen conjoint du budget, du contrat producteur,
   de la référence humaine et de la règle de jugement ;
5. ne pas ouvrir le jeu tenu pendant cet atelier.

Ce document expose les faits, les décisions closes et les questions à soumettre
à la littérature ou à un auditeur. Il ne propose aucun nouveau seuil.

## 1. Les deux objets à ne plus confondre

### P6 — l'application

P6 doit fournir une Lyra minimale utilisable au quotidien. Le socle FastAPI
existe : un tour de chat traverse P0–P2 et le graphe conceptuel P3 ; la
mémoire ESMM P4 n'est pas appelée par ce parcours. Les sessions sont
accessibles par HTTP et le moteur est isolé par session.
La persistance SQLite de l'état et la restauration après redémarrage sont
livrées. Restent le contexte conversationnel, le réaffichage des échanges,
les retours utilisateur durables, un accès REST au graphe, la sélection
multimodèle et une authentification minimale avant toute exposition.

P6 peut avancer sans verdict P7. Son usage local peut produire le matériau
natif qui manque aujourd'hui : demandes réelles, sorties réellement choisies,
désaccords, reformulations et retours de l'utilisateur.

### P7 — l'évaluation

La question scientifique demeure comparative : conditionnellement à un premier
tour commun, la politique adaptative de Lyra apporte-t-elle un avantage robuste
et pratiquement utile sur la meilleure politique statique simple, à modèle,
gabarit et enveloppe de calcul comparables ?

Cette question n'a jamais été testée. V3 à V10 se sont arrêtées avant toute
mesure de l'hypothèse ; V11 a exécuté Q0 et la calibration, puis s'est arrêtée à
Q1. `H11` est donc `UNTESTED`, et non réfutée.

## 2. État factuel de V11

| Élément | Observation vérifiée | Portée |
|---|---:|---|
| Appels producteur | 432, sans erreur de transport | exécution complète de la calibration |
| Appels juge | 146/146 valides et propres au transport | contrat de sortie respecté |
| Comparaisons complètes | 81 | deux traces producteur valides |
| Comparaisons jugées | 73 | 8 paires rejetées par l'égalité stricte du pack |
| Comparaisons résolues | 40/73 | stabilité après inversion et verdict non-TIE |
| Stabilité brute | 54,8 % | insuffisante pour la porte tenue C4 à 75 % |
| Accord attendu sous les marginales observées | 36,5 % | le juge n'est pas assimilable à du pur hasard |
| Cohen κ | 0,288 [0,108–0,468] | signal faible mais détectable |
| Test unilatéral contre le hasard | p = 0,0011 | le contenu influence le jugement |
| Échecs producteur au tour 3 | 53/144 | tous correspondent à une fin par limite de longueur |
| Jeu tenu | 60/60 cas jamais lus ni générés | actif intact |

Le fait important n'est donc ni « le juge est aléatoire », ni « l'instrument
est presque validé ». Le juge réagit au contenu, mais son signal est trop faible
et trop mêlé à des effets parasites pour soutenir la campagne finale.

## 3. Les trois défauts intriqués

### D1 — seuil et plancher du hasard

Le seuil de résolution à 50 % a été transposé du panel bi-juge au juge unique
sans redériver le plancher propre à la nouvelle règle. Pour le juge observé, le
plancher dérivé des marginales est de 36,5 %. Le dépassement est réel, mais le
seuil avait été fixé sans connaître ni borner la structure du biais.

### D2 — incompatibilité du budget et du contrat producteur

Les budgets de sortie et les longueurs minimales du JSON ont été gelés
séparément. Trois presets sur quatre ont souvent manqué de place pour terminer
leur réponse. La calibration a donc partiellement sélectionné la capacité à
finir le formulaire plutôt que la qualité éditoriale.

### D3 — longueur confondue avec la variable testée

Le bouton `δr` commande la longueur disponible. Or le classement des victoires
suit celui des budgets, et les juges LLM peuvent préférer les réponses plus
longues. Le design V11 ne sépare pas une meilleure décision d'une réponse
simplement plus développée.

Ces défauts doivent être éprouvés ensemble sur du matériau de développement.
Corriger un seul d'entre eux puis relancer un gel recréerait le même risque.

## 4. Séparation proposée des régimes

### Régime A — développement de l'instrument

- données explicitement marquées développement ;
- itérations autorisées et journalisées ;
- corpus de calibration V11 déjà consommé, corpus en attente et futures données
  natives de P6 réutilisables ;
- aucune lecture des 60 cas tenus ;
- aucune conclusion sur l'hypothèse adaptatif contre statique.

### Régime B — test d'hypothèse

- version précise de l'instrument citée et immuable pendant la campagne ;
- hypothèse, observables, seuils, exclusions et verdicts pré-enregistrés ;
- données tenues ouvertes une seule fois selon la règle gelée ;
- portée limitée à l'instrument, aux modèles et aux tâches effectivement testés.

### Régime C — déploiement et surveillance

- instrument versionné mais révisable entre deux périodes ;
- dérive, coûts, erreurs et désaccords suivis ;
- aucune réinterprétation rétroactive d'un verdict gelé ;
- nouvelles versions réétalonnées avant promotion.

L'erreur structurelle à éviter est de geler ensemble un instrument encore en
développement et l'hypothèse qu'il doit mesurer.

## 5. Forme du jugement à étudier

Le choix n'est probablement pas exclusivement ponctuel ou comparatif.

- Le **comparatif** correspond directement à la question finale : adaptatif
  contre statique. Il doit contrôler l'ordre, la position et la longueur.
- Le **ponctuel par critères** aide à diagnostiquer les causes : respect des
  contraintes, correction, pertinence, concision, couverture et traçabilité.
  Il expose toutefois aux effets plafond et à la dérive d'échelle.
- Un dispositif **hybride** peut utiliser le ponctuel pour qualifier
  l'instrument et le comparatif aveugle pour le verdict final.

Une autre piste à examiner est un méta-jugement portant uniquement sur la
cohérence d'une justification avec une grille humaine. Il ne doit pas produire
subrepticement une préférence sur les candidats ni être présenté comme une
réouverture du panel bi-juge clos.

## 6. Référence humaine et ouverture du panel

Le chercheur est actuellement l'unique annotateur humain. Cela permet de
mesurer la répétabilité d'un même opérateur, pas la reproductibilité entre
opérateurs ni une « préférence humaine » générale.

Le dispositif minimal à discuter avec un auditeur serait :

1. un échantillon de développement stratifié, limité et aveuglé ;
2. deux passages du même annotateur séparés dans le temps, avec ordre
   re-randomisé, pour mesurer la stabilité intra-annotateur ;
3. plusieurs annotateurs humains sur un sous-ensemble commun si le recrutement
   devient possible ;
4. des juges automatiques utilisés comme instruments ou filtres, jamais comme
   substituts fictifs à l'indépendance humaine ;
5. une adjudication humaine concentrée sur les désaccords, à condition que la
   règle de sélection des cas ne biaise pas l'estimation finale ;
6. une portée explicitement personnelle si une seule référence humaine demeure.

Avant toute collecte externe, il faudra définir le consentement, les données
conservées, la possibilité de retrait, la confidentialité et la charge demandée
aux participants. Ces choix ne sont pas des détails d'interface : ils changent
le corpus observable.

## 7. Lyra viable minimale comme producteur de données

Le déploiement envisagé est d'abord local et réversible. Il ne doit pas dépendre
d'une certification P7 achevée.

Configuration prudente proposée :

- politique simple comme comportement par défaut ;
- politique adaptative optionnelle ou exécutée en mode fantôme ;
- aucune action externe irréversible fondée sur une politique non validée ;
- journal forensique séparant entrée, configuration, sorties, latence, coût en
  tokens et retour humain ;
- conservation de la clé reliant une sortie à sa politique, cachée pendant le
  jugement mais récupérable après celui-ci ;
- possibilité d'exporter les données retenues pour l'atelier P7 ;
- contenu externe traité comme donnée non fiable, jamais comme instruction de
  contrôle du système.

La collecte quotidienne n'est pas automatiquement un benchmark. Elle devient
utile lorsqu'une règle explicite transforme les interactions en cas de
développement, de surveillance ou, plus tard, en cas tenus indépendants.

## 8. Ce qui est clos et ce qui reste réutilisable

### Clos dans le programme actuel

- le panel bi-juge tel que défini par les admissions V10 ;
- H11 dans V11, qui reste `UNTESTED` ;
- la calibration V11 comme sélection impartiale de `STATIC_BEST` ;
- le design juge unique par paires tel qu'instancié en V11 ;
- le pont Fisher d'Origami vers Lyra/EPP pour la série v4–v7.

### Réutilisable comme matériau ou infrastructure

- les 60 cas tenus, encore intacts, sous réserve de justifier leur futur emploi ;
- les corpus, graines, fixtures et règles de scellement ;
- le harnais d'exécution, les verrous, preuves GPU et journaux ;
- les 12 cas de calibration, désormais données de développement ;
- les corpus en attente ;
- le contrat complet, que Qwen 3.8 a satisfait 24/24 lors de son admission v2 ;
- les modèles précédemment étudiés, dans un nouvel atelier dont le rôle est
  explicitement distinct du panel clos.

« Clos » qualifie une inférence et un protocole. Cela n'ordonne pas de détruire
les actifs techniques ou les données qui peuvent servir à une autre question.

## 9. Conditions d'entrée d'une éventuelle V12

Les seuils restent volontairement ouverts. Ils devront être dérivés ou justifiés
sur des données de développement, puis gelés avant toute campagne.

V12 ne devrait être rédigée que lorsque les preuves suivantes existent :

1. le budget permet à chaque politique de satisfaire le même contrat à un taux
   compatible avec la comparaison visée ;
2. l'effet propre de la longueur est mesuré ou neutralisé ;
3. la sensibilité à la position et à l'inversion est quantifiée ;
4. la règle ponctuelle, comparative ou hybride a été choisie sur des critères
   définis avant le jeu tenu ;
5. la référence humaine a une portée et une répétabilité documentées ;
6. le mécanisme d'adjudication et le traitement des TIE/INVALID sont fixés ;
7. la version de l'instrument est séparable du protocole expérimental ;
8. l'usage du jeu tenu existant est justifié malgré les préinscriptions
   successives sur du matériau adjacent ;
9. un échec ou un résultat inconclusif laisse P6 exploitable avec la politique
   simple.

## 10. Questions prioritaires pour la littérature récente

L'audit bibliographique devrait chercher des résultats et des échecs publiés
sur les axes suivants :

1. comparaison **pairwise vs pointwise** pour sorties longues et proches ;
2. biais de **position, verbosité, style, identité du modèle et auto-préférence**
   des LLM-as-a-judge ;
3. protocoles d'inversion, répétition, permutation et agrégation qui estiment
   plutôt qu'ils ne masquent ces biais ;
4. calibration d'un juge contre plusieurs humains, avec désaccord légitime et
   erreur de mesure des annotateurs ;
5. plans réalistes pour petit panel humain : annotation répétée, échantillonnage
   actif, adjudication et estimation de l'incertitude ;
6. évaluation de politiques adaptatives lorsque l'intervention modifie aussi
   la longueur ou le coût de la sortie ;
7. séparation entre développement d'un évaluateur, test gelé et surveillance
   continue après déploiement ;
8. validité d'un jeu tenu conservé à travers plusieurs arrêts préalables sans
   accès à ses résultats, mais avec adaptation sur matériel voisin ;
9. méthodes de déploiement en **shadow mode**, interleaving ou essais séquentiels
   adaptées à un utilisateur principal et à de faibles volumes ;
10. gouvernance, consentement et confidentialité des corpus issus d'un usage
    conversationnel réel.

Termes de recherche possibles : `LLM-as-a-judge position bias`, `verbosity bias
pairwise evaluation`, `human annotator measurement error`, `intra-rater
reliability NLP evaluation`, `active sampling human evaluation`, `adaptive
policy shadow deployment`, `evaluator drift monitoring`, `preregistration
sequential experiments data reuse`.

## 11. Questions adressées à l'auditeur externe

1. L'estimand final est-il formulé assez précisément pour séparer qualité,
   longueur, coût et préférence personnelle ?
2. Un design hybride ponctuel/comparatif est-il justifié ici, ou introduit-il
   une flexibilité analytique excessive ?
3. Quelle quantité minimale d'annotation humaine commune permettrait d'estimer
   une reproductibilité utile sans imposer un panel industriel ?
4. Comment traiter les sorties non conformes sans sélectionner les politiques
   à travers leur budget ?
5. Quelle correction de position conserve le sens du verdict sans fabriquer
   artificiellement de la stabilité ?
6. Comment séparer l'effet de `δr` de la préférence du juge pour la longueur ?
7. Le jeu tenu historique peut-il encore servir de confirmation, et sous quelles
   déclarations de dépendance aux choix antérieurs ?
8. Quelles conditions suffisent pour promouvoir l'adaptatif du mode fantôme au
   mode actif chez un utilisateur unique ?
9. Quels mécanismes empêchent la collecte P6 de devenir une optimisation
   opportuniste sur les préférences du seul constructeur ?

## 12. Ordre de travail retenu

1. réaligner README, BUILD_STATUS, doctrine des ponts et TODO sur l'état réel ;
2. faire relire le présent cadrage et conduire la recherche bibliographique ;
3. construire la tranche P6 minimale sans dépendre d'un verdict P7 ;
4. alimenter l'atelier métrologique avec des données de développement natives ;
5. décider seulement ensuite si les conditions d'entrée de V12 sont réunies.

## Sources internes canoniques

- `docs/P7_V11_STATUS.md` — résultats et limites de V11 ;
- `PREREGISTRATION_v11.md` — contrat gelé de la campagne ;
- `docs/P7_META_ARRET.md` — règle d'arrêt et clôture du panel bi-juge ;
- `docs/Programme P7 · mise à plat.txt` — note locale de reprise,
  volontairement non versionnée ;
- `BUILD_STATUS.md` — état des briques ;
- `docs/PLAN_EDIFICATION.md` — dépendances et chemin critique ;
- `docs/ORGANES_ET_PONTS.md` — doctrine inter-projets ;
- `../Origa_Tranf_Test/NOTE_RESULTATS_v7.md` — clôture du pont Fisher ;
- `../TODO.md` — ordre de travail central du triptyque.

---

Ce document doit évoluer avec les conclusions de l'audit. Toute hypothèse ou
tout seuil issu de cette discussion devra vivre ensuite dans une préinscription
distincte, gelée avant la mesure correspondante.
