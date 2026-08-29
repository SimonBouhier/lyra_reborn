Trace résiduelle de rêve — principe d’injection opportuniste
Les phases de Songe (Organe 2) opèrent sur les états latents de la mémoire (vecteurs du Nemeton, contextes récents, arêtes de co-occurrence). Elles doivent rester strictement pondérées par les métriques pré-enregistrées de nouveauté et de consolidation (METRIQUES_SONGE.md) : ni copie, ni bruit, ni compression destructrice de la fenêtre récente.
Cependant, un rêve réussi peut laisser une trace résiduelle subtile — un signal faible, non dominant, distinct des nœuds et arêtes explicitement consolidés ou compostés. Cette trace n’entre pas dans le graphe principal comme fait ou relation stable. Elle est stockée à part, avec un poids très bas et une décroissance temporelle (écologie d’oubli appliquée aussi aux traces).
Rôle :
Lors d’une inférence ultérieure (ou d’un autre processus de modulation / exploration), si une correspondance locale significative apparaît entre le contexte courant et une trace résiduelle, celle-ci peut teinter légèrement la récupération ou le scoring — en tant qu’« intuition d’abstraction » héritée de la Jachère.
Ce n’est jamais systématique :

le déclenchement est conditionnel (seuil de correspondance + opportunité contextuelle) ;
l’influence reste bornée (poids maximal faible, jamais prioritaire sur les faits consolidés ou les sources déterministes) ;
l’absence de correspondance laisse la trace s’éteindre sans effet.

Lien avec l’existant :

S’appuie sur le Nemeton (magasin des vecteurs) et le journal d’oubli / compost (mécanisme de sélection et d’oubli différé déjà prévu).
Respecte la séparation Consolidation / Dreaming du Songe.
Reste compatible avec la charte : aucun claim de « conscience » ; la trace est un mécanisme de mémoire faible, testable, et doit échouer bruyamment si elle se comporte comme une injection systématique ou non ancrée.

DoD candidate (à pré-enregistrer avant implémentation) :

Après une phase de Songe validée, au moins une trace résiduelle est écrite avec poids initial faible et métadonnées d’origine.
En absence de correspondance contextuelle, la trace n’influence ni le rappel ni le scoring (test d’isolation).
En présence d’une correspondance au-dessus du seuil gelé, l’influence est mesurable, bornée, et n’écrase pas les éléments consolidés.
La trace finit par être oubliée ou compostée selon l’écologie existante si elle n’est jamais réactivée.