# LEXIQUE PATCH — V7.3 TOPDOWN_MARKET_READER

## TOPDOWN_MARKET_READER
Lecteur top-down PowerFlow. Assemble HTF, MTF et LTF pour produire une lecture exploitable du flux.

## HTF_CONTEXT
Contexte Weekly / Daily / H4. Sert a localiser le prix dans les zones, rotations, provenance, vitesse et tendance nouvelle.

## MTF_DAY_PLAN
Plan de jour prepare sur H1 / M30 / M15. Ne declenche pas. Il prepare les scenarios.

## LTF_EXECUTION_CONDITION
Condition d'attention M15 / M5 / M1. Ne decide pas. Qualifie si l'entree potentielle merite attention.

## ZONE_TESTED
Zone touchee ou travaillee par le prix, sans rejet net ni cassure confirmee.

## ZONE_REJECTED
Zone testee puis repoussee. Peut signaler absorption, trap ou debut de rotation.

## BREAK_AND_REINTEGRATE
Cassure d'une zone puis retour rapide dans la zone. Signature candidate de sweep ou de faux breakout.

## BREAK_AND_HOLD
Cassure suivie d'une tenue au-dela de la zone. Signature candidate de continuation structurelle.

## ROTATION_BUILDING
Rotation en construction. Le flux change de cote de range ou repart d'une zone vers une autre.

## ROTATION_FAILED
Rotation avortee. Le mouvement echoue a prolonger la bascule attendue.

## PROVENANCE_FAST
Mouvement provenant d'une impulsion rapide. La zone peut etre fragile ou susceptible d'etre retestee.

## PROVENANCE_ABSORBED
Mouvement provenant d'une progression lente ou absorbee. Energie moins explosive, comportement plus compressif.

## M1_MICROFILM_ACTIVE
M1 montre une activite exploitable en perception. Cela ne valide pas une decision.

## M5_RELAY_THIN
Relais M5 present mais mince. Le M1 peut etre lu, mais la structure tactique reste fragile.

## M5_RELAY_CLEAN
Relais M5 propre. Le microfilm M1 est mieux raccorde au plan tactique.

## HTF_IMMATURE
Historique Weekly / Daily / H4 trop fin ou incomplet. Ne bloque pas M1, mais reduit la robustesse structurelle.

## FULL_STACK_SIGNAL_READY
Etat ou les couches data / HTF / MTF / LTF sont suffisamment presentes pour une lecture complete.

## M1_TACTICAL_THIN_HTF
M1 vivant et M5 present, mais HTF trop mince. Lecture tactique autorisee, structure HTF qualifiee faible.

## DAILY_MARKET_READER
Fiche quotidienne pre-remplie par PowerFlow : niveaux, close position, intention machine, scenarios, conditions.

## LIQUIDITY_SWEEP_CANDIDATE
Cassure/reintegration candidate d'un niveau. Necessite comparaison trader avec contexte HTF/MTF.

## HIGH_SWEEP_REINTEGRATION
Sweep au-dessus d'un high suivi d'une reintegration sous le niveau.

## LOW_SWEEP_REINTEGRATION
Sweep sous un low suivi d'une reintegration au-dessus du niveau.

## ORGANIC_SURFACE_READING
Langue intermediaire PowerFlow. Elle traduit les mesures en flux, zone, rotation, relais, fenetre.
