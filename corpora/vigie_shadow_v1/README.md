# Corpus local — Vigie shadow V1

Ce dossier conserve les captures publiques, la file de revue et les labels
humains de `PREREGISTRATION_v1.md`. Les fichiers JSON/JSONL sont ignorés par
Git : leurs SHA-256, pas les textes tiers, assurent la traçabilité.

Ordre obligatoire :

```powershell
& .\.venv\Scripts\python.exe scripts\vigie_campaign.py acquire
& .\.venv\Scripts\python.exe scripts\vigie_campaign.py annotate
# seulement si au moins un choix EXCLUDE :
& .\.venv\Scripts\python.exe scripts\vigie_campaign.py rebuild-excluded
& .\.venv\Scripts\python.exe scripts\vigie_campaign.py annotate
& .\.venv\Scripts\python.exe scripts\vigie_campaign.py seal
& .\.venv\Scripts\python.exe scripts\vigie_campaign.py verify-models
& .\.venv\Scripts\python.exe scripts\vigie_campaign.py run
& .\.venv\Scripts\python.exe scripts\vigie_campaign.py score
```

`annotate` est reprenable et écrit après chaque choix. Un item douteux doit être
marqué `EXCLUDE`; il ne faut ni deviner ni modifier un label pour atteindre les
comptes gelés. `rebuild-excluded` remplace alors son porteur par l'item suivant
dans l'ordre déterministe, conserve les annotations encore valides et permet de
reprendre la revue avant scellage.

Le runner ne lit jamais `labels.jsonl`. Il vérifie uniquement le manifeste et
le hash de `items.jsonl`, journalise chaque verdict au fil de l'eau et reprend
un fichier de prédictions incomplet sans rejouer les lignes déjà présentes.
