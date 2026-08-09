# La Vigie — frontière de quarantaine

**Date :** 2026-08-09  
**Statut :** contrat Lyra implémenté et testé ; sidecar EPP réel non encore
branché ; aucune promotion mémoire automatique.

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

## Responsabilités du futur sidecar EPP

Le sidecar devra :

- exiger `EPP_QUARANTINE_MODE=1` et refuser sinon ;
- recevoir des providers explicites ; aucun modèle par défaut ou provider API ;
- n'accepter qu'Ollama local sur `127.0.0.1` ;
- créer une base SQLite temporaire propre au run ;
- désactiver cache, flywheel et sources déterministes externes ;
- ne jamais ouvrir l'URL portée par le contenu ;
- ne jamais utiliser la base, le graphe ou la couche Solana d'EPP ;
- rendre uniquement le schéma `vigie.quarantine.v1`, sans logs sur stdout ou
  stderr en cas de succès ;
- détruire sa base temporaire après émission du verdict.

Le `run_pipeline()` EPP actuel ne doit pas être appelé contre une base réelle :
il stocke les attestations, appelle le hook post-cristallisation et injecte des
triplets selon ses propres seuils. Le booléen `inject_triplets` de
`ESMMRunConfig` ne constitue donc pas à lui seul une frontière suffisante.

## Limite de la première frontière

Le protocole subprocess retire les secrets, interdit le shell et rend les
sorties inertes. Il ne crée pas une sandbox OS : le code Python du sidecar reste
un code local de confiance disposant des droits du compte utilisateur. Le
palier live devra ajouter une restriction réseau/processus vérifiable si EPP
reçoit un jour autre chose qu'un provider Ollama local sans outils.

## Déploiement gradué

### S0 — Shadow

L'ESMM rend un verdict journalisé mais sans effet. Une baseline déterministe
rend un second verdict sur les mêmes cas. Aucun contenu ne rejoint Nemeton.

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

EPP n'est pas son propre oracle. Sur un corpus tenu mêlant contenus bénins,
injections directes/indirectes et empoisonnements coordonnés, on comparera le
gate ESMM à la baseline déterministe sur :

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

Ce que ces tests ne prouvent pas encore : la qualité de classification d'un
ESMM live, l'isolation réseau OS et l'innocuité d'une promotion mémoire. Ces
preuves appartiennent aux paliers suivants.
