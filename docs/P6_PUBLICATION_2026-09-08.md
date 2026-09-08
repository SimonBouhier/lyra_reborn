# P6 — lot de publication du 8 septembre 2026

Ce lot regroupe le dialogue durable P6, l'instrument de diagnostic des rappels
corrigés et la documentation de leur état réel. La branche de travail est
`codex/p7-meta-arret` du dépôt `SimonBouhier/lyra_reborn` ; elle reste distincte
de `main`. EPP et Origami ne comportaient aucun changement local à publier.

## Contenu et portée

- Journal SQLite v3, cycle durable des demandes, contexte conversationnel,
  corrections liées, rappels explicites et navigation, avec scripts de migration
  sur copie et tests déterministes.
- Instrument exploratoire séparé : plan scellé, corpus synthétique, runner,
  scoreur, exports de relecture et transcription compacte.
- Contrat P6, état de construction, note de cloisonnement Jachère, méthode de
  relecture et provenance historique de la correction de concurrence.

Les bases personnelles, résultats de calcul, archives générées, réponses brutes
de relecteurs, leur consolidation privée et la note personnelle P7 restent locaux.
Les chemins vers `data/runs/` et `output/` servent à retrouver ces pièces sur le
poste de travail ; elles ne sont pas présentes dans le dépôt GitHub.

Le [manifeste public des preuves locales](preuves/P6_MANIFESTE_PUBLIC_2026-09-08.json)
donne les empreintes, les comptes rendus de tests et leur portée. Il constitue un
index, pas une copie des traces ni une confirmation indépendante. Les 29 fichiers
du contrôle produit et les sources de l'instrument correspondent aux empreintes
des vérifications existantes : 73 Python + 9 JavaScript pour le produit, 212 tests
pour l'instrument. Aucune nouvelle génération ni migration utilisateur n'est
nécessaire pour cette publication.

La collecte exploratoire comporte 6 336 réponses techniquement valides et quatre
admissions préalables. Sa confirmation sur de nouvelles situations et l'admission
d'usage de P6 restent ouvertes. Voir [le diagnostic](P6_DIAGNOSTIC_RAPPELS_2026-09-08.md)
et [le mode d'emploi des relectures](P6_RELECTURE_MODE_EMPLOI_2026-09-08.md).

## Conservation des empreintes

Les attributs Git préservent les octets des fichiers référencés par les preuves P6,
y compris leurs fins de ligne. Cela évite une conversion automatique au staging
ou au checkout. Aucun plan, sceau ou fichier de campagne n'est réécrit. Les blobs
commités doivent être comparés aux fichiers et empreintes d'origine avant push.

Le contrôle des espaces autorise les fins de ligne CRLF présentes dans certaines
pièces conservées ; il continue de signaler les autres espaces superflus. Cette
configuration ne change pas le comportement de l'application.

## Reproduire les contrôles locaux

Depuis la racine du clone, avec ses dépendances existantes :

```powershell
.\scripts\verifier_p6.ps1
.\.venv\Scripts\python.exe -B -X utf8 -m pytest -q `
  tests/test_p6_recall_corpus.py tests/test_p6_recall_study.py `
  tests/test_p6_recall_packets.py tests/test_p6_recall_reading.py
```

Ces contrôles utilisent des clients factices. Les commandes de collecte réelle
sont explicites et décrites dans [le guide de l'expérience](../experiments/p6_recall/README.md).
Le script de concurrence conservé avec les relectures du 5 septembre exige son
ancien commit : il n'est pas une commande de validation du code actuel.
