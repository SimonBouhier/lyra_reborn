# Corpus local — Vigie shadow V2

V2 remplace la revue exhaustive de V1 par un protocole à provenance explicite :

- 60 attaques synthétiques sont labellisées construction ;
- 60 porteurs bénins commencent en silver_source ;
- 24 bénins sont tirés dans six strates et audités par Simon Bouhier ;
- toute strate où apparaît UNSAFE ou EXCLUDE passe de 4 à 10 audits ;
- chaque remplacement doit lui-même recevoir BENIGN avant le scellage.

La construction réutilise exclusivement la capture V1 gelée. Elle exclut les
120 porteurs sélectionnés en V1, décode les entités HTML et filtre localement
courriels, téléphones et liens de cloud personnel. Seuls des compteurs de codes
de filtrage sont conservés.

Ordre obligatoire :

~~~powershell
& .\.venv\Scripts\python.exe scripts\vigie_campaign_v2.py prepare
& .\.venv\Scripts\python.exe scripts\vigie_campaign_v2.py annotate
# uniquement si annotate annonce des désaccords :
& .\.venv\Scripts\python.exe scripts\vigie_campaign_v2.py rebuild-audit
& .\.venv\Scripts\python.exe scripts\vigie_campaign_v2.py annotate
# répéter rebuild-audit puis annotate tant qu'un désaccord subsiste
& .\.venv\Scripts\python.exe scripts\vigie_campaign_v2.py seal
& .\.venv\Scripts\python.exe scripts\vigie_campaign_v2.py verify-models
& .\.venv\Scripts\python.exe scripts\vigie_campaign_v2.py run
& .\.venv\Scripts\python.exe scripts\vigie_campaign_v2.py score
~~~

La commande annotate est reprenable et écrit après chaque choix. Les verdicts
de modèles ne sont jamais affichés pendant l'audit. La commande seal refuse
tout audit incomplet ou désaccord non reconstruit. La commande run ne lit
jamais labels.jsonl.

Même si H2 est soutenue, V2 reste une qualification exploratoire sur labels
mixtes. Elle ne constitue ni un benchmark gold ni une autorisation de
déploiement S1.
