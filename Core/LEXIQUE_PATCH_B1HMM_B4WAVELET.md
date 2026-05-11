# Lexique patch — B1+ HMM + B4+ Wavelet

## REGIME_HMM
Régime HTF produit par B1+ HMM. Valeurs: COMPRESSION, TENDANCE, RANGE, TRANSITION.

## HMM_GAUSSIAN
Méthode probabiliste à états cachés avec émissions gaussiennes multivariées.

## STATE_PROBABILITIES
Distribution de probabilité sur les régimes HMM. Elle expose l'incertitude au trader, sans choisir à sa place.

## WAVELET_COMPRESSING
État B4+ indiquant concentration d'énergie sur périodes courtes avec dérive récente vers la compression.

## WAVELET_EXPANDING
État B4+ indiquant concentration d'énergie sur périodes longues ou dérive vers expansion.

## WAVELET_MULTI_SCALE
État B4+ indiquant énergie significative sur plusieurs bandes simultanément.

## WAVELET_TRANSITIONING
État B4+ indiquant changement de bande dominante en cours.

## WAVELET_SILENT
État B4+ valide indiquant énergie trop faible pour signal exploitable. Ce n'est pas une panne.

## DOMINANT_SCALE_BARS
Échelle dominante actuelle détectée par CWT Morlet, exprimée en nombre de barres.

## WAVELET_ENERGY_RATIO
Ratio énergie basse fréquence / haute fréquence. Sert à distinguer expansion longue vs compression courte.

## SCALE_DRIFT_DIRECTION
Direction récente de dérive d'échelle: COMPRESSING, EXPANDING ou STABLE.

## MULTI_SCALE_FLAG
Booléen indiquant plusieurs bandes actives simultanément.

## COMPRESSION_ONSET
Booléen indiquant une naissance récente de compression de cycle.

## CWT_MORLET
Transformée ondelette continue avec ondelette Morlet. Mesure temps-fréquence non stationnaire.

## DUAL_ARCHITECTURE
Deux méthodes indépendantes exposées côte à côte. Jamais fusionnées, jamais moyennées.

## FRESHNESS (FRESH / AGING / STALE)
Fraîcheur d'un bloc dashboard: FRESH < 300s, AGING entre 300s et 600s, STALE >= 600s.

## DATA_BRICK_DISPLAY
Attribut HTML `data-brick` qui trace la brique source du bloc affiché.
