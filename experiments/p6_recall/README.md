# Diagnostic P6 des rappels corrigés

Ce dossier contient une expérience synthétique séparée du produit et de P7.
Le plan v1 est exploratoire : aucune confirmation ni comparaison générale des
familles ne doit être déduite de ses taux. La confirmation sera préenregistrée
sur de nouvelles situations après diagnostic et relectures séparées.

Lire [le plan](v1/PLAN_EXPLORATOIRE_v1.md). Toutes les commandes partent de la
racine Lyra et utilisent le Python existant. Aucun téléchargement ni changement
de modèle n'est exécuté par ces commandes.

```powershell
# Métadonnées seulement ; le dossier de destination doit être neuf.
.\.venv\Scripts\python.exe -B -X utf8 scripts/p6_recall_study.py prepare `
  --protocol experiments/p6_recall/v1/PLAN_EXPLORATOIRE_v1.md `
  --destination data/runs/p6-recall/v1
# Live explicite : 4 appels techniques, aucun score sémantique d'admission.
.\.venv\Scripts\python.exe -B -X utf8 scripts/p6_recall_study.py qualify --study data/runs/p6-recall/v1
# Live explicite : collecte planifiée. --max-calls permet une pause sans réordonner.
.\.venv\Scripts\python.exe -B -X utf8 scripts/p6_recall_study.py run --study data/runs/p6-recall/v1
# Refuse une collecte incomplète. Le résultat est séparé des exports aveugles.
.\.venv\Scripts\python.exe -B -X utf8 scripts/p6_recall_study.py analyse `
  --study data/runs/p6-recall/v1 --destination data/runs/p6-recall/v1/analyse.json
```

Les fichiers existants ne sont pas écrasés. Un résultat inconnu après interruption
n'est jamais recalculé automatiquement. Les évolutions après gel doivent créer
un nouveau plan et une nouvelle campagne, sans réécrire les preuves.

Le code `packets.py` crée les dossiers Markdown/PDF/JSONL et ZIP à partir d'une
liste explicite de pièces. Simon les partage manuellement. Une archive créée
n'est ni une relecture effectuée ni une réplication indépendante.

Dans une archive extraite, la racine d'exécution est `pieces/`. Les sources y
conservent leurs chemins ; le manifeste trouve le plan scellé dans le dossier
de campagne. L'analyse des traces exige Python 3.10+ et la bibliothèque standard,
sans Ollama. Remplacer le chemin `.venv` par l'interpréteur disponible. La
qualification et la collecte appellent en revanche Ollama local et exigent les
identités exactes consignées. Aucun environnement Python ni binaire de modèle
n'est embarqué dans les archives. Les tests utilisent pytest déjà disponible.

Pour une relecture documentaire, suivre le formulaire et déclarer les pièces
effectivement consultées. Toute mission d'analyse exécutée ou de réplication
doit être donnée explicitement par Simon ; elle constitue une condition d'accès
distincte. Les archives et traces générées restent ignorées par Git.
