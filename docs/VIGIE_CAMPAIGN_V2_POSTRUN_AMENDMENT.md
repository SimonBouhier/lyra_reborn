# Amendement post-exécution — campagne Vigie shadow V2

Date : 2026-08-09
Statut : addendum technique au résultat pré-enregistré ; aucune modification du protocole ni des prédictions

## Résultat inchangé

La campagne V2 conclut `H2_NOT_SUPPORTED_IN_V2` : aucun des trois jurys
pré-enregistrés ne satisfait simultanément les portes C1 à C7. Les trois jurys
échouent C2, C3 et C6. Aucun déploiement n'est autorisé.

## Incident de lecture du résultat

Les 360 prédictions ont été produites intégralement avant le calcul des
métriques. La première tentative de score a ensuite échoué avant de produire
un verdict avec l'erreur `V2 prediction vote model is invalid`.

Le validateur local avait été écrit contre une représentation anticipée du
contrat du sidecar : identifiants de modèles bruts et exactement deux votes par
ligne. Le sidecar gelé a réellement sérialisé :

- les identifiants sous la forme `ollama::<modèle>` ;
- deux votes et aucune erreur lorsque le jury a répondu normalement ;
- zéro vote, `degraded=true` et une erreur explicite `sidecar_degraded` lorsque
  le pont a échoué avant de pouvoir constituer la paire.

La correction accepte uniquement ces deux formes explicites et cohérentes. Une
ligne non dégradée sans deux votes, une ligne dégradée contenant des votes, une
discordance entre `degraded` et `errors`, ou un identifiant étranger au jury
reste rejeté. La validation de reprise et le scoreur appliquent désormais le
même contrat.

## Intégrité de la mesure

La correction est intervenue après l'inférence et n'a modifié ni :

- les 120 items ou leurs labels ;
- les 360 lignes de prédiction ;
- les décisions ou actions produites ;
- les seuils, portes ou règles de verdict de `PREREGISTRATION_v2.md` ;
- le commit de gel `61f597267c33b9e74a0f0d7340e32eef08e70622`.

Empreintes de la campagne scorée :

- items : `f39f2981cee108c4305f692f89433e59819b6ab7d018058b2fa9ae61c099d83f` ;
- labels : `81228ad659b429aeea2ea5e82f344d3f8053dcbb0533c18915c78bde272eba01` ;
- prédictions : `890434bf022598387e07fdf6177976a9709a69428fc84638b16d5d714bdeda57`.

## Informations rendues visibles

Le rapport expose maintenant, sans changer le verdict :

- les paires de votes présentes et manquantes par jury ;
- le désaccord rapporté aux 120 cas et aux seules paires complètes ;
- les latences médiane, p95 et maximale ;
- l'état de chacune des portes C1 à C7 ;
- la provenance des labels, les exclusions de l'audit et le filtre de
  confidentialité.

Une limite diagnostique demeure : le sidecar réduit les causes techniques à
`sidecar_degraded`. La V2 permet donc de mesurer le taux de dégradation, mais
pas d'attribuer sûrement chaque échec à Ollama, au modèle, au parseur ou au
pont. Ce manque ne doit pas être réparé par une réexécution opportuniste de la
V2 ; il devra être instrumenté avant une éventuelle campagne pré-enregistrée
ultérieure.

## Lecture substantielle

Les jurys améliorent fortement la sécurité apparente (AER nul et UER compris
entre 0 et 0,05), mais au prix d'un BRR nul : aucun contenu bénin n'est laissé
passer, y compris parmi les paires de votes effectivement complétées. Les taux
de dégradation, compris entre 0,367 et 0,508, aggravent encore l'inutilisabilité
opérationnelle, mais n'expliquent donc pas seuls l'échec.

Les gains C1, C4 et C5 ne suffisent pas : sans C2, C3 et C6, une politique de
quasi-blocage pourrait paraître performante uniquement parce qu'elle refuse
tout. C'est précisément ce que les portes conjointes du protocole empêchent.
