# P6 — diagnostic des rappels corrigés et relectures séparées

**8 septembre 2026 — travail local autorisé par Simon.** L'instrument est construit,
le plan exploratoire v1 est scellé et les **6 336 appels sont terminés**. La confirmation
indépendante reste une étape ultérieure, sur de nouvelles situations et après
préenregistrement de ses hypothèses. Aucune confirmation externe n'a été réalisée.

**Lecture depuis GitHub :** le plan, les sources, les tests et les guides sont
versionnés. Les rapports et traces sous `data/runs/`, ainsi que les archives et
PDF sous `output/`, sont ignorés par Git. Leurs liens ci-dessous désignent des
preuves locales et ne permettent pas de les télécharger depuis GitHub. Le
[guide d'exécution](../experiments/p6_recall/README.md) et le
[guide des exports](P6_RAPPEL_EXPORTS_2026-09-08.md) donnent les commandes ; les
archives existantes se transmettent manuellement selon le
[mode d'emploi](P6_RELECTURE_MODE_EMPLOI_2026-09-08.md).

## Objet et périmètre

Une ancienne information, sa correction et une ancienne instruction peuvent
coexister dans un rappel. Le diagnostic cherche quelles interventions sur cette
présentation changent l'utilisation de la valeur actuelle. Il porte sur le
générateur conversationnel P6 ; il n'évalue pas les juges P7.

Le [plan scellé](../experiments/p6_recall/v1/PLAN_EXPLORATOIRE_v1.md) fixe les
facteurs, effectifs, témoins, métriques, dénominateurs, interruptions et limites
avant les générations. Empreinte SHA-256 :
`98b9c1698828deb985bba64e184c58a14f4bdb5d2c2f20630bc9585b32fe4ef1`.

- Quatre configurations installées : Gemma 3, Llama 3.1, Granite 3.3 et Mistral.
- Seize combinaisons de présence d'une ancienne instruction, rendu des versions,
  séparation des messages et présence d'un ancien accusé assistant.
- Six patrons, chacun décliné dans deux sens de correction et deux rôles de
  provenance : 24 scénarios. Trois graines par scénario et configuration.
- 4 608 appels factoriels et 1 728 témoins, soit 6 336 appels planifiés.
- Quatre appels techniques préalables, tous admis le 8 septembre. Cette admission
  vérifie la forme et le transport, sans sélectionner les réponses sémantiques.

Le code expérimental est séparé de l'application. Il n'utilise aucune base de
conversation personnelle. Aucune mise à jour de moteur, installation de modèle,
migration utilisateur, génération Qwen ou publication n'a été effectuée.

## Ce que les contrôles établissent

L'[index public des preuves locales](preuves/P6_MANIFESTE_PUBLIC_2026-09-08.json)
fournit leurs empreintes et leur portée. Les rapports complets liés ci-dessous
restent locaux ; cet index ne constitue pas une réplication indépendante.

Les **212 tests** du corpus, du runner, de l'export et de la transcription compacte
ont réussi à la clôture. Un premier lot de 185 tests avait réussi avant le
lancement de la collecte. Ils utilisent des clients factices : ils vérifient notamment
la parité du rendu de référence avec l'assembleur P6, les témoins, le score exact,
les effets sur des sorties fabriquées, la conservation des erreurs, la reprise
sans rejeu, les empreintes et l'analyse après déplacement des fichiers.

Le bilan final ne comporte **aucun échec, erreur ni test ignoré**.
Le [rapport de l'instrument](../data/runs/p6-recall/v1/instrument-final-verification.json)
référence le JUnit conservé et les empreintes du code testé. Ce résultat est
distinct des 73 tests Python et 9 JavaScript de l'étape produit précédente.

La [vérification de la collecte](../data/runs/p6-recall/v1/verification.json)
constate 6 336 traces terminales techniquement valides, des corps cohérents avec
les requêtes réservées et les objets décodés, ainsi que des empreintes concordantes.
La collecte s'est achevée à **09:54:51 UTC**. Les quatre admissions préalables
portent le nombre total de générations réelles de cette campagne à **6 340**.
Le statut `valid` qualifie la forme de réponse, pas son exactitude sémantique.

Les calculs descriptifs prévus sont conservés et scellés dans `analyse.json`,
hors des archives de relecture. Aucune interprétation ni conclusion comparative
de l'auteur n'a été ajoutée aux paquets. Les retours pourront être examinés avant
de rédiger la synthèse contradictoire.

Le runner réserve chaque requête avant envoi et conserve les corps HTTP reçus.
Une erreur ou une exécution incertaine reste dans le dénominateur prévu. Les
sorties complètes sont accessibles même lorsqu'elles ne respectent pas le
format attendu. L'analyse automatique refuse une collection partielle.

Ces contrôles ne démontrent ni une compétence générale des familles, ni une
cause architecturale pure, ni la validité d'usage de P6. Les graines répétées
ne constituent pas des scénarios indépendants ; les 24 variantes restent
regroupées dans six patrons. Les effets sont descriptifs de ce corpus fermé.

## Pièces et partage

Le [guide d'exécution](../experiments/p6_recall/README.md) décrit les commandes et
la portabilité. Le [guide des exports](P6_RAPPEL_EXPORTS_2026-09-08.md) décrit
les archives, empreintes et formulaires.

Le dossier de campagne est `data/runs/p6-recall/v1/`. Il contient le manifeste,
une copie scellée du plan, les stimuli complets, les métadonnées des modèles,
la qualification et les traces. Les archives partagées sont produites sous
`output/p6-recall/` et restent locales, ignorées par Git.

Le premier paquet fournit le contexte, la méthode et le formulaire. Le second
ajoute les sorties brutes, sans les taux calculés ni notre interprétation.
Simon les transmet manuellement. Une lecture documentaire, une analyse exécutée
et une réplication externe sont des missions distinctes ; les accès et opérations
réels doivent figurer dans chaque retour. Des conversations séparées isolent les
avis ; elles ne garantissent pas l'indépendance statistique des modèles utilisés.

Le [dossier de réception](relectures/2026-09-08_p6_rappels/README.md) donne les
instructions de partage et les emplacements de conservation des réponses.
Le [mode d'emploi](P6_RELECTURE_MODE_EMPLOI_2026-09-08.md) pointe vers les fichiers
finaux : archive complète de 24,1 Mo et compagnon unique de 147 pages, également
disponible en Markdown (276 050 caractères). Les 6 336 réponses du compagnon
ont été restituées depuis le Markdown et depuis l'extraction du PDF, puis
comparées aux originaux avec leurs métadonnées. Le nombre de tokens dépend du
modèle destinataire et n'a pas été mesuré.

Les [preuves d'intégrité de l'export](../data/runs/p6-recall/v1/export-verification/verification-integrity.json)
et les [contrôles de transcription](../output/p6-recall/lecture_compacte_v1/verification_lecture.json)
sont conservés séparément. La révision de pagination ne change aucun stimulus
ni résultat. Ces contrôles techniques ne constituent pas les avis externes attendus.

Les contributeurs internes à la construction ne sont pas les relecteurs externes
demandés. Lors d'une recherche interne, des lignes d'import de scripts P7 ont été
affichées par une recherche trop large ; elle a été resserrée. Aucune donnée ni
sortie P7 n'a été consultée par cette recherche et aucune pièce P7 n'entre dans
les paquets. Cet écart de périmètre de lecture est déclaré séparément des tests
de l'instrument ; aucun verdict global de relecture indépendante n'est revendiqué.

## Suite après les premiers retours

Conserver les rapports initiaux séparément, avec identité déclarée du modèle,
pièces consultées et éventuelles exécutions. L'arbitrage devra rattacher chaque
proposition à ses preuves, distinguer redondance et corroboration et conserver
les désaccords motivés. Une éventuelle confrontation entre avis formera un second
tour explicitement identifié.

La confirmation exigera une nouvelle question testable, des situations différentes
des six patrons, un effet utile défini et un dimensionnement adapté. Elle sera
figée avant ses propres sorties. Le présent diagnostic et les relectures de son
dossier ne satisfont pas, à eux seuls, cette confirmation.
