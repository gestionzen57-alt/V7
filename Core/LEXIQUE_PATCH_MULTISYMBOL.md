# LEXIQUE PATCH MULTISYMBOL — PowerFlow V7.2

## CROSS_SYMBOL_VALIDATION
Validation comportementale entre plusieurs symboles pour distinguer force propre d'une devise et faiblesse dominante d'une devise opposée.

## USD_WEAKNESS_DOMINANT
Driver détecté lorsque USD apparaît faible sur plusieurs crosses simultanément. Perception de champ, pas signal de trade.

## GBP_STRENGTH_GENUINE
Driver détecté lorsque GBP est fort sur plusieurs crosses disponibles, pas seulement fort vs USD.

## EUR_DIVERGENT
État où EUR peut être fort vs USD mais non confirmé comme force globale. Nécessite idéalement un cross direct type EURGBP/GBPEUR pour validation stricte.

## JPY_SAFE_HAVEN
État où JPY se renforce simultanément sur ses crosses disponibles. Qualifie une attraction relationnelle JPY.

## DRIVER_DETECTION
Qualification du moteur dominant du champ multi-symbol: force d'une devise, faiblesse d'une devise, ou mixte.

## TRUE_STRENGTH
Force nette d'une devise calculée sur tous les symboles disponibles. Labels: STRONG, MODERATE, WEAK, UNKNOWN.

## MULTI_SYMBOL_SCHEDULER
Scheduler séquentiel qui exécute les runners PowerFlow pour chaque symbole actif puis lance la cross-validation une seule fois.

## CYCLE_INTERVAL
Intervalle entre deux cycles scheduler, configuré par `scheduler_config.json`, défaut 300 secondes.

## SCHEDULER_GUARD
Garde de sécurité empêchant deux cycles scheduler de se chevaucher.

## OVERLAP_SKIP
Événement loggé quand un cycle est ignoré car le cycle précédent ou une autre instance détient encore le lock.

## DATA_SYMBOL_ATTRIBUTE
Attribut HTML `data-symbol` exposant le symbole associé à un bloc dashboard.

## SYMBOL_PARAMETRIC
Doctrine de code où le symbole est un paramètre explicite et jamais une branche métier différente.
