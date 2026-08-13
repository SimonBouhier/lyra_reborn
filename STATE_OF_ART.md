# État de l'art — politique adaptative et évaluation agentique

**Dernière revue : 2026-08-13**
**Question locale :** une politique qui transforme des métriques textuelles bon
marché en décisions de contrôle produit-elle de meilleures trajectoires qu'une
politique statique, sur des cas réels tenus ?

Ce registre ne cherche pas à donner à Lyra un décor emprunté. Il sert à éviter
de revendiquer comme nouvelle une idée déjà publiée et à importer seulement les
contraintes expérimentales qui empêchent une conclusion trompeuse.

## 1. Ce qui existe déjà

### 1.1 L'adaptation du décodage est une vraie famille de méthodes

*Learning Adaptive LLM Decoding* formule le choix dynamique d'une stratégie de
décodage comme un bandit contextuel au niveau séquence et comme un POMDP au
niveau token. Les auteurs gardent le modèle gelé, comparent à une meilleure
politique statique sous budget fixé et rapportent des gains sur des tâches à
récompense terminale vérifiable. Conséquence pour Lyra : le principe
« observer, puis changer température/top-p/budget » est plausible, mais il
n'est pas une nouveauté en soi. Une baseline statique forte et une enveloppe de
calcul commune sont obligatoires.

Source primaire : [Su et al., 2026](https://arxiv.org/abs/2603.09065).

*Adaptive Decoding via Test-Time Policy Learning* ajuste aussi les paramètres
de sampling d'un modèle gelé, ici par apprentissage de politique. Son ablation
est plus importante pour notre cas que ses chiffres : les objectifs fondés sur
le seul recouvrement textuel ne donnent pas les gains des récompenses
composites. Conséquence pour Lyra : `kw_overlap`, `structure_score` et
`repeat4_rate` peuvent guider une action, mais ne peuvent pas constituer le
verdict de qualité de cette même action.

Source primaire : [Bhardwaj et al., 2026](https://arxiv.org/abs/2603.18428).

### 1.2 Une trajectoire agentique ne se réduit pas à sa dernière chaîne

*Agent-as-a-Judge* évalue des agents sur des tâches réalistes en inspectant
leurs exigences et leur progression, plutôt qu'en notant seulement leur sortie
finale. Le travail montre l'intérêt d'un évaluateur capable de réunir des
preuves sur la trajectoire, tout en restant un résultat propre au domaine du
code et non une garantie universelle. Conséquence pour Lyra : le juge doit voir
la source, les trois tours, les options réellement envoyées et les contrôles
déterministes ; il doit pouvoir citer les éléments qui fondent sa préférence.

Source primaire : [Zhuge et al., 2024](https://arxiv.org/abs/2410.10934).

Les benchmarks d'agents en environnements exécutables vont dans le même sens :
OSWorld emploie des évaluateurs d'état/exécution adaptés aux tâches, tandis
qu'AgentBoard sépare succès final et progression. Conséquence : dès qu'un
oracle déterministe existe, il passe avant une impression produite par un LLM.

Sources primaires : [OSWorld](https://arxiv.org/abs/2404.07972),
[AgentBoard](https://arxiv.org/abs/2401.13178).

### 1.3 Un LLM juge est un instrument instable, pas un oracle

Sage teste la cohérence locale et la transitivité des juges. Même des modèles
forts changent de préférence sur une part substantielle des cas difficiles ;
une rubrique explicite et un panel améliorent la stabilité sans la garantir.
Conséquence pour Lyra : chaque comparaison est exécutée dans les deux ordres.
Une préférence qui change avec l'ordre, un `TIE` ou un désaccord du panel reste
`UNRESOLVED`. Aucun arbitre ne transforme automatiquement cette incertitude en
victoire.

Source primaire : [Feng et al., 2025](https://arxiv.org/abs/2512.16041).

### 1.4 Une grammaire de sortie ne remplace pas le contrat de validation

*Generating Structured Outputs from Language Models: Benchmark and Studies*
évalue plusieurs moteurs de décodage contraint sur des milliers de schémas JSON
réels et montre que la couverture pratique des contraintes dépend du moteur.
Conséquence pour Lyra : le schéma accepté par le compilateur de grammaire
d'Ollama doit être gelé et testé comme un artefact distinct ; il ne peut pas
être supposé équivalent à tout le vocabulaire JSON Schema produit par
Pydantic.

Source primaire : [Geng et al., 2025](https://arxiv.org/abs/2501.10868).

Les grammaires incrémentales garantissent utilement la forme syntaxique des
sorties structurées, mais des travaux sur le *grammar-aligned decoding*
montrent aussi qu'une contrainte peut déformer la distribution du modèle.
Conséquence pour Lyra : la même grammaire doit être appliquée à tous les
juges et candidats ; la conformité grammaticale reste séparée de la qualité du
jugement et toute réponse non conforme au contrat Pydantic complet reste
`INVALID`, sans réparation.

Sources primaires : [Geng et al., 2023](https://arxiv.org/abs/2305.13971),
[Park et al., 2024](https://arxiv.org/abs/2405.21047).

## 2. Ce que l'audit local change

### 2.1 Les métriques Lyra sont des capteurs, pas des preuves de qualité

Le chemin réel actuel calcule : recouvrement de mots-clés, répétitions de
4-grammes, marqueurs de structure, suspicion de troncature et utilisation du
budget. Le pont P2 en dérive cohérence, fit, pression et tension. Ces signaux
sont réels et modulent effectivement `rho`, `delta_r`, `tau_c` et `kappa`, mais
ils favorisent mécaniquement certaines formes — notamment les listes et
sections. Les réutiliser comme score final rendrait la conclusion circulaire.

### 2.2 La signature 5D d'EPP ne doit pas être appelée « juge indépendant »

EPP apporte une bonne enveloppe : modèles distincts, votes, provenance,
attestation, proposition Git et frontière de promotion. Mais son chemin de
repli remplit encore `centrality` et `stability` à `0.5`, tandis que
`semantic_consistency` est dérivée de la dispersion de confiance. EPP mesure
donc un processus de délibération ; il ne fournit pas encore, seul, la vérité
terrain de l'expérience P7.

### 2.3 L'effet de la politique n'apparaît qu'après le premier tour

`LyraLoop.generate()` observe une sortie puis prépare les boutons du tour
suivant. Une campagne composée de prompts indépendants avec état réinitialisé à
chaque génération testerait essentiellement les réglages initiaux, pas la
politique. L'unité expérimentale doit donc être une trajectoire multi-tour, et
l'état doit être réinitialisé seulement entre les cas.

## 3. Décisions méthodologiques retenues

1. **Objet causal :** la politique adaptative existante de Lyra, avec le modèle
   producteur gelé ; EPP reste une inspiration de traçabilité.
2. **Unité :** une source réelle et une trajectoire éditoriale de trois tours :
   compréhension, contradiction, décision finale.
3. **Comparateurs :** réglages par défaut et meilleure politique statique
   choisie sur un jeu de calibration séparé.
4. **Équité :** mêmes modèles, gabarits, graines, nombre d'appels et plafonds de
   génération par paire ; tokens et latence restent des observables de garde.
5. **Oracle en couches :** contrat déterministe de sortie, puis juge pairwise
   agentique aveugle, ordre inversé et panel de deux familles distinctes.
6. **Indépendance :** aucun score qui pilote Lyra n'entre dans la rubrique du
   juge ni dans la logique du verdict scientifique.
7. **Tenue :** calibration sur données déjà ouvertes ; sélection et scellement
   déterministes du jeu principal après le gel, sans afficher son contenu.
8. **Portée :** le verdict qualifiera une politique, trois modèles locaux et un
   type de trajectoire. Il ne prouvera ni conscience, ni supériorité générale,
   ni aptitude au déploiement autonome.

## 4. Valeur propre de l'expérience

La contribution éventuelle n'est pas « l'adaptive decoding ». Elle est plus
étroite : tester si les capteurs interprétables déjà hérités de Lyra peuvent
piloter utilement une trajectoire de décision en français, sur des fragments
réels et hétérogènes, sans être récompensés par leurs propres proxys. Un résultat
négatif est pleinement informatif : il indiquerait que la modulation est réelle
mais que sa politique actuelle n'achète pas de meilleures décisions.
