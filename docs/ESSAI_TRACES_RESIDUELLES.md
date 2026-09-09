# Trace résiduelle de rêve — principe d’injection opportuniste

> **Statut au 9 septembre 2026 : intention conservée, proposition historique.**
> Les mentions ci-dessous de métriques « pré-enregistrées » et de Songe « validé »
> sont des conditions envisagées, pas des acquis. Les
> [métriques candidates](METRIQUES_SONGE.md) sont à réviser ; la
> [note Jachère du 7 septembre](NOTE_ARCHITECTURE_JACHERE_CLOISONNEMENT_2026-09-07.md)
> fait référence pour les droits, l'admission et le retrait. Le futur contrat
> des traces doit préciser stockage séparé, provenance, portée, seuil, budget,
> décroissance et retrait, y compris après correction ou suppression de source.
> [ETAT_ACTUEL](ETAT_ACTUEL.md) porte le statut d'implémentation ; le
> [registre des intentions](REGISTRE_INTENTIONS.md) et le
> [plan actif](PLAN_EDIFICATION.md) conservent son prochain jalon.
> Aucune injection automatique dans la P6 de référence n'est activée par ce texte.

Les phases de Songe (Organe 2) opèrent sur les états latents de la mémoire (vecteurs du Nemeton, contextes récents, arêtes de co-occurrence). Elles doivent rester strictement pondérées par les métriques pré-enregistrées de nouveauté et de consolidation (METRIQUES_SONGE.md) : ni copie, ni bruit, ni compression destructrice de la fenêtre récente.
Cependant, un rêve réussi peut laisser une trace résiduelle subtile — un signal faible, non dominant, distinct des nœuds et arêtes explicitement consolidés ou compostés. Cette trace n’entre pas dans le graphe principal comme fait ou relation stable. Elle est stockée à part, avec un poids très bas et une décroissance temporelle (écologie d’oubli appliquée aussi aux traces).
Rôle :
Lors d’une inférence ultérieure (ou d’un autre processus de modulation / exploration), si une correspondance locale significative apparaît entre le contexte courant et une trace résiduelle, celle-ci peut teinter légèrement la récupération ou le scoring — en tant qu’« intuition d’abstraction » héritée de la Jachère.
Ce n’est jamais systématique :

le déclenchement est conditionnel (seuil de correspondance + opportunité contextuelle) ;
l’influence reste bornée (poids maximal faible, jamais prioritaire sur les faits consolidés ou les sources déterministes) ;
l’absence de correspondance laisse la trace s’éteindre sans effet.

Lien avec l’existant :

Envisage de s'appuyer sur le Nemeton et le journal d'oubli / compost. Le « magasin des vecteurs » désigne ici un horizon ; le graphe courant de nœuds et d'arêtes n'est pas un magasin vectoriel complet (voir [l'état du code](ETAT_ACTUEL.md#correspondance-entre-les-organes-et-le-code)).
Respecte la séparation Consolidation / Dreaming du Songe.
Reste compatible avec la charte : aucun claim de « conscience » ; la trace est un mécanisme de mémoire faible, testable, et doit échouer bruyamment si elle se comporte comme une injection systématique ou non ancrée.

DoD candidate (à pré-enregistrer avant implémentation) :

Après une phase de Songe validée, au moins une trace résiduelle est écrite avec poids initial faible et métadonnées d’origine.
En absence de correspondance contextuelle, la trace n’influence ni le rappel ni le scoring (test d’isolation).
En présence d’une correspondance au-dessus du seuil gelé, l’influence est mesurable, bornée, et n’écrase pas les éléments consolidés.
La trace finit par être oubliée ou compostée selon l’écologie existante si elle n’est jamais réactivée.
