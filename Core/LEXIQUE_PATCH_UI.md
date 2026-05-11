# LEXIQUE_PATCH_UI - PowerFlow V7.2.1 Dashboard MultiSymbol + USDJPY Audit

Termes a integrer dans la continuite documentaire PowerFlow.

- DASHBOARD_MULTISYMBOL_TABS : navigation par symbole sans fusion de donnees.
- SYMBOL_TAB : selection GBPUSD/EURUSD/USDJPY/XAUUSD.
- CROSS_SYMBOL_VALIDATION_CARD : card globale lisant cross_validation.json.
- CURRENCY_STRENGTH_LABEL : WEAK/MODERATE/STRONG/UNKNOWN par devise.
- DRIVER_DETECTION : USD_WEAKNESS_DOMINANT, GBP_STRENGTH_GENUINE, EUR_DIVERGENT, JPY_SAFE_HAVEN, MIXED.
- SYMBOL_STATUS_DISPLAY : LIVE OK, ENGINE OK / HTF INCOMPLETE, ENGINE OK / DATA STALE.
- OUTPUT_PER_SYMBOL_DIRECTORY : output/dashboard_surface/{symbol}/.
- DASHBOARD_TAB_LOADER : chargement JS des JSON du symbole actif.
- FRESHNESS_BADGE_TIMESTAMP : FRESH/AGING/STALE/MISSING selon age.
- SYMBOL_WARNING_STATE : indicateur visuel jaune/rouge par risque technique.
- AUDIT_USDJPY_CAPTURE : diagnostic read-only de USDJPY dans force_snapshots.
- STALE_TIMESTAMP : timestamp > 24h pour une capture attendue live.
- CAPTURE_INACTIVE : pas de donnees recentes ou rows insuffisantes.
- BRIDGE_INSERTION_CHECK : verification insertion bridge vers force_snapshots.
- EA_SYMBOLS_LIST : liste symboles actifs cote MT4 EA.
- DATABASE_SYMBOL_COMPLETENESS : COUNT et MAX(timestamp) par symbole.
- USDJPY_STALE_DATA : USDJPY existe mais n'est pas vivant.
- USDJPY_INSUFFICIENT_ROWS : USDJPY rows insuffisantes pour perception robuste.
- EURUSD_HTF_CONTEXT_INCOMPLETE : moteur OK mais regime HTF encore incomplet.
- DATA_STALE_OR_THIN : capture ancienne ou faible densite.
- DASHBOARD_GLOBAL_CARD : card visible quel que soit le symbole actif.
- PER_SYMBOL_BLOCK : bloc lie a output/dashboard_surface/{symbol}/.
- UI_READ_ONLY_SURFACE : dashboard lecteur JSON uniquement.
- MISSING_OUTPUT_STATE : fichier JSON attendu absent.
- CROSS_VALIDATION_FRESHNESS : fraicheur de la card inter-symboles.
- TECHNICAL_RISK_BADGE : exposition UI d'un risque technique.
