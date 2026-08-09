# La Vigie — frontière de quarantaine

**Date :** 2026-08-09  
**Statut :** contrat Lyra et sidecar EPP autonome implémentés et testés ;
qualification sur modèles Ollama réels non encore menée ; aucune promotion
mémoire automatique.

## But

Faire analyser des contenus publics non fiables sans leur donner le pouvoir de
modifier Lyra, EPP ou le monde extérieur. La sécurité ne dépend pas de
l'obéissance parfaite d'un LLM : une erreur de jugement doit rester sans effet.

La frontière précède la politique éditoriale. Deux verdicts ne doivent jamais
être confondus :

1. sécurité : `PASS | QUARANTINE | REJECT | ESCALATE` ;
2. intérêt : `IGNORE | DEFER | AUDIT | AMPLIFY`.

Un contenu peut être très pertinent et rester hostile.

## Contrat mince Lyra → EPP

Implémentation : `agency/tools/vigie/quarantine.py`.

Lyra lance un processus sans shell, lui transmet un unique JSON sur `stdin` et
exige un unique JSON sur `stdout`. L'identité du cas est liée au verdict par
`item_id` et par le SHA-256 du contenu UTF-8. Le schéma de réponse est fermé :
toute clé absente ou supplémentaire est un échec.

Le processus enfant ne reçoit pas l'environnement parent. Seules les variables
système indispensables et les contraintes suivantes franchissent la frontière :

```text
EPP_QUARANTINE_MODE=1
OLLAMA_HOST=http://127.0.0.1:11434
NO_PROXY=127.0.0.1,localhost
```

Une erreur de lancement, un timeout, un code retour non nul, `stderr`, une
sortie trop grande, un JSON invalide, une identité différente ou un verdict
dégradé donnent tous le même effet sûr : `QUARANTINE`, avec un code d'erreur
explicite. Aucun fallback silencieux n'est admis.

## Sidecar EPP autonome

Implémentation : `EPP_Verdict/epp_quarantine_sidecar.py`.

Le sidecar :

- exige `EPP_QUARANTINE_MODE=1` et refuse sinon ;
- exige entre deux et huit modèles distincts explicitement nommés ; aucun
  modèle par défaut ou provider API ;
- n'accepte que l'endpoint exact `http://127.0.0.1:11434` et ouvre une connexion
  directe sans mécanisme de redirection HTTP ;
- ne charge aucun package historique EPP : aucune base, aucun graphe, aucun
  cache, flywheel, orchestrateur ou stockage temporaire ;
- ne transmet aucun outil au modèle, n'ouvre jamais l'URL portée par le contenu
  et demande `keep_alive=0` ;
- contraint chaque modèle par un schéma JSON fermé et ne laisse traverser aucun
  texte libre généré : décisions, flags et raisons sont des vocabulaires clos ;
- exige l'unanimité pour `PASS` comme pour `REJECT`. Une divergence devient
  `QUARANTINE`, sauf demande explicite d'escalade ;
- rend uniquement le schéma `vigie.quarantine.v1`, sans logs sur stdout ou
  stderr en cas de succès.

Le `run_pipeline()` EPP actuel ne doit pas être appelé contre une base réelle :
il stocke les attestations, appelle le hook post-cristallisation et injecte des
triplets selon ses propres seuils. Le booléen `inject_triplets` de
`ESMMRunConfig` ne constitue donc pas à lui seul une frontière suffisante.

## Limite de la première frontière

Le protocole subprocess retire les secrets, interdit le shell et rend les
sorties inertes. Il ne crée pas une sandbox OS : le code Python du sidecar reste
un code local de confiance disposant des droits du compte utilisateur. Sa seule
connexion implémentée vise directement la boucle locale, mais une restriction
réseau au niveau OS restera nécessaire avant tout élargissement de capacité.

## Déploiement gradué

### S0 — Shadow

L'ensemble EPP rend un verdict journalisé mais sans effet. Une baseline
déterministe rend un second verdict sur les mêmes cas. Aucun contenu ne rejoint
Nemeton.

### S1 — Probation

Les `PASS` peuvent rejoindre un magasin temporaire séparé, avec provenance et
expiration. Cette matière est consultable pour l'évaluation mais ne pilote ni
les boutons, ni Memento, ni Nemeton.

### S2 — Promotion différée

La promotion porte sur une proposition dérivée et sourcée, jamais sur le texte
brut. Elle exige une règle gelée de corroboration/ancienneté. Les reprises d'une
même origine ne comptent pas comme preuves indépendantes.

### S3 — Contrôle humain ciblé

L'humain traite les `ESCALATE`, toute action externe et un échantillon aléatoire
des décisions automatiques. Le taux d'échantillonnage et les seuils seront
pré-enregistrés avant la campagne, pas choisis après observation.

## Comment l'utilité d'EPP sera jugée

EPP n'est pas son propre oracle. Sur un corpus tenu et annoté humainement mêlant
contenus bénins, injections directes/indirectes, attaques adaptatives visant le
filtre connu et empoisonnements coordonnés, on comparera le gate EPP à la
baseline déterministe sur :

- baits échappés ;
- contenus bénins perdus ;
- volume d'escalades humaines ;
- contaminations de la mémoire de probation ;
- coût et latence.

Aucun seuil n'est fixé dans ce document : il décrit la frontière technique, pas
le verdict scientifique.

## Preuves actuelles

`tests/test_vigie_quarantine.py` couvre le transport JSON hostile, le retrait
des secrets, l'interdiction du shell, les limites de taille et de temps, les
codes retour, `stderr`, le schéma fermé, le hash et les verdicts dégradés.

Dans EPP, `tests/test_quarantine_sidecar.py` couvre le contrat d'entrée, la
connexion Ollama directe, l'absence d'outils et de stockage, le schéma de sortie
des modèles, l'unanimité, la divergence, les pannes et les contenus adversariaux.
Au 2026-08-09 : 26 tests ciblés et la suite EPP complète (934 réussis, 11
ignorés) sont verts sous Python 3.14.7. Un essai réel Lyra → processus EPP avec
des modèles volontairement inexistants aboutit à
`QUARANTINE / sidecar_degraded`.

Un smoke test manuel sur Ollama local a ensuite confirmé le transport live et
révélé une sortie modèle contradictoire (`PASS` associé à une raison
d'exfiltration). Un test RED en conserve la trace : le parseur exige désormais
la cohérence décision/raison et transforme ce cas en quarantaine dégradée. Ces
essais exploratoires ne constituent pas une mesure de qualité.

Ce que ces tests ne prouvent pas encore : la qualité de classification d'un
ensemble Ollama live, l'isolation réseau OS et l'innocuité d'une promotion
mémoire. Ces preuves appartiennent aux paliers suivants.
