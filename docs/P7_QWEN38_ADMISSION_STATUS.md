# P7 — statut de la première admission Qwen 3.8

**Date :** 2026-08-17  
**Protocole gelé :** `876d13f5cf8eac6bb863ee1205a5f172c824919d`  
**Statut :** `ABORTED_GPU_NOT_DETECTED`  
**Qualification V10 :** non testée

## Déroulement observé

Le runner a vérifié Ollama 0.32.14 et le digest gelé de `qwen3.8:27b`, acquis
son verrou, puis commencé la matrice de 24 appels. Son manifeste ne capturait
pas encore la résidence GPU.

Le premier appel, `TRANSPORT_PARITY:forward`, répétition 3, a terminé après
202,6 secondes. Il était entièrement valide et juste : HTTP 200,
`done_reason=stop`, canal `thinking` vide, verdict Pydantic valide et préférence
`TIE` attendue. Le second appel a été journalisé comme commencé, puis le runner
a été interrompu volontairement afin de ne pas poursuivre environ une heure de
calcul CPU. Il n'existe ni réponse 2 ni résumé final.

## Cause externe établie

`/api/ps` rapportait `size_vram=0` et le journal serveur plaçait poids, cache
KV, mémoire récurrente, vision et calcul sur CPU. Le journal de démarrage montre
la séquence suivante :

- Ollama 0.32.13 détecte la RTX 4090 via CUDA à 22:13:12 ;
- l'auto-mise à jour lance Ollama 0.32.14 à 22:13:34 ;
- ce serveur ne détecte que le CPU, alors que l'installation des bibliothèques
  se poursuit jusqu'à 22:14:30.

Après arrêt ciblé des seuls processus Ollama et redémarrage de l'application,
0.32.14 détecte de nouveau `CUDA0`, compute 8.9, 24 Go de VRAM dont 22,5 Go
libres. Un smoke séparé à contexte 32K répond `CUDA`, puis `/api/ps` rapporte
`size_vram = size = 17 399 745 083` octets pour le modèle. La cause est donc un
serveur lancé avant la fin de sa propre mise à jour, pas une incompatibilité de
Qwen 3.8 ni une insuffisance de la RTX 4090.

## Empreintes de l'exécution interrompue

- run : `data/runs/p7_qwen38_admission_20260817T214953.736028Z` ;
- manifeste :
  `0cfdab8717f950a45f58920939d0bb1e361a943de6304828b00cb70f90c49aca` ;
- journal append-only :
  `286ba3a8c2c1f58e90a325b6bfe136e2ff3fde5403125743410d80f957ce4c10` ;
- verrou :
  `1eb2e9c0d3fa633728683ba734c537780d7b3fce1d2f5650650cc2218a89aad2` ;
- réponse valide 1 :
  `2d353e087e29d8beac2f7c2e48108fe7f344aeef4334d33503e130b9534ab8ad`.

## Reprise autorisée

Le verrou initial reste consommé. Une V2 distincte conserve la matrice et la
règle de décision, mais ajoute avant tout verrou une postcondition externe : le
bon digest doit être déjà chargé et `/api/ps` doit rapporter
`size_vram == size > 0`. L'échec de cette précondition arrête le runner sans
appel de fixture et sans consommer son verrou.
