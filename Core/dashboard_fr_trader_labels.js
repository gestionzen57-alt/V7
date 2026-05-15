/*
  PowerFlow V7.6.7 - Dashboard FR Trader Labels
  Role: display-only translation layer for dashboard/cockpit/Reality Board.
  It keeps engine enums intact and translates visible dashboard text to French trader wording.
*/
(function () {
  "use strict";

  const PF_FR_LABELS = {
    // Core state / visibility
    FULL_STACK_VISIBLE: "Lecture complète",
    TACTICAL_OK: "Lecture tactique exploitable",
    RECONSTRUCTED: "Lecture reconstruite",
    READING_PARTIAL: "Lecture partielle",
    PARTIAL: "Partiel",
    PARTIAL_STALE: "Partiel / données vieillissantes",
    DEGRADED: "Lecture dégradée",
    UNKNOWN: "Lecture inconnue",
    THIN_DATA: "Données insuffisantes",
    STALE: "Données périmées",
    DATA_HEALTH_PARTIAL_STALE: "Santé data : partielle / vieillissante",
    FRESHNESS_PARTIAL_STALE: "Fraîcheur : partielle / vieillissante",
    CONTRACT_OK: "Contrat OK",

    // Zones
    HIGH_ZONE: "Zone haute",
    LOW_ZONE: "Zone basse",
    MID_ZONE: "Zone médiane",
    HIGH_ZONE_EXTENSION: "Extension en zone haute",
    HIGH_ZONE_REJECTION: "Rejet de zone haute",
    HIGH_ZONE_CONSUMED: "Zone haute consommée",
    HIGH_ZONE_EXHAUSTION: "Épuisement en zone haute",
    HIGH_ZONE_EXHAUSTION_RISK: "Risque d’épuisement en zone haute",
    EXHAUSTION_RISK: "Risque d’épuisement",
    LOW_ZONE_DEFENDED: "Zone basse défendue",
    LOWER_ZONE_TOUCH: "Contact zone basse",
    MID_REINTEGRATION_ZONE: "Zone médiane de réintégration",
    FAILED_REINTEGRATION: "Réintégration échouée",
    REINTEGRATION_ATTEMPT: "Tentative de réintégration",
    ZONE_BREATHING: "Respiration de zone",
    ZONE_CONSUMED: "Zone consommée",
    ZONE_ACCEPTED: "Zone acceptée",
    ZONE_REJECTED: "Zone rejetée",

    // Nodes
    NODE_TERRAIN_V767: "Node terrain V7.6.7",
    HIGH_REJECTION_NODE: "Node de rejet haut",
    LOW_REJECTION_NODE: "Node de rejet bas",
    LOWER_ZONE_TOUCH_NODE: "Node de contact zone basse",
    LOWER_ZONE_DEFENDED_NODE: "Node de zone basse défendue",
    FAILED_REINTEGRATION_NODE: "Node de réintégration échouée",
    PULLBACK_ABSORBED_NODE: "Node de pullback absorbé",
    SECOND_LEG_TRIGGER_NODE: "Node de déclenchement deuxième jambe",
    HIGH_EXHAUSTION_NODE: "Node d’épuisement haut",
    POST_HIGH_UNWIND_NODE: "Node de déroulement après haut",
    POST_LOW_REACTION_NODE: "Node de réaction après zone basse",
    LATE_COUNTER_BOUNCE_NODE: "Node de rebond tardif",
    FALSE_BIRTH_NODE: "Node de fausse naissance",

    // Movement / scene roles
    RELEASE_UP: "Relâchement haussier",
    RELEASE_DOWN: "Relâchement baissier",
    RELEASE_ACTIVE: "Relâchement actif",
    RELEASE_VALIDATED: "Relâchement validé",
    FIRST_LEG_UP: "Première jambe haussière",
    FIRST_LEG_DOWN: "Première jambe baissière",
    SECOND_LEG_UP: "Deuxième jambe haussière",
    SECOND_LEG_DOWN: "Deuxième jambe baissière",
    COUNTER_BREATH: "Respiration inverse",
    COUNTER_BREATH_UP: "Respiration inverse haussière",
    COUNTER_BREATH_DOWN: "Respiration inverse baissière",
    COUNTER_BREATH_REJECTED: "Respiration inverse rejetée",
    POST_RELEASE_PULLBACK: "Pullback après relâchement",
    PULLBACK_ABSORBED: "Pullback absorbé",
    POST_LOW_REACTION: "Réaction après zone basse",
    POST_HIGH_UNWIND: "Déroulement après rejet haut",
    LATE_THIN_BOUNCE: "Rebond tardif fragile",
    LATE_UP: "Hausse tardive",
    LATE_UNWIND: "Déroulement tardif",
    FALSE_BIRTH: "Fausse naissance",
    EVENT_STACK_ONLY: "Empilement d’événements seulement",

    // Reading states
    DOMINANT_READING: "Lecture dominante",
    ALTERNATIVE_READING: "Lecture alternative",
    SCENE_BUILDING: "Scène en construction",
    SCENE_DECONSTRUCTING: "Scène en déconstruction",
    SCENE_REBUILDING: "Scène en reconstruction",
    RECONSTRUCTION_POSSIBLE: "Reconstruction possible",
    INVALIDATION_CONDITION: "Condition d’invalidation",
    TRANSFORMATION_CONDITION: "Condition de transformation",
    STRONG_INTERPRETATION: "Interprétation forte",
    OPEN_HYPOTHESIS: "Hypothèse ouverte",
    STRATEGY_CANDIDATE: "Stratégie de lecture candidate",
    NEEDS_MORE_DAYS: "À vérifier sur d’autres journées",

    // Pair bias / driver
    PAIR_UP: "Pression haussière brute de la paire",
    PAIR_DOWN: "Pression baissière brute de la paire",
    BASE_OUTRUNS_QUOTE: "La devise de base surperforme la cotation",
    QUOTE_OUTRUNS_BASE: "La cotation surperforme la devise de base",
    BASE_STRENGTH_DOMINANT: "Force dominante de la devise de base",
    QUOTE_WEAKNESS_DOMINANT: "Faiblesse dominante de la cotation",
    BOTH_UP_BASE_STRONGER: "Les deux montent, mais la base monte plus fort",
    BOTH_UP_QUOTE_STRONGER: "Les deux montent, mais la cotation monte plus fort",
    BOTH_DOWN_BASE_WEAKER: "Les deux baissent, mais la base baisse plus fort",
    BOTH_DOWN_QUOTE_WEAKER: "Les deux baissent, mais la cotation baisse plus fort",
    USD_BROAD_STRENGTH: "Force USD généralisée",
    USD_BROAD_WEAKNESS: "Faiblesse USD généralisée",
    PAIR_SPECIFIC_EXCEPTION: "Exception propre à la paire",

    // Time profile / events
    M1_ACCELERATION: "Accélération M1",
    M5_ACCELERATION: "Accélération M5",
    M15_ACCELERATION: "Accélération M15",
    M30_ACCELERATION: "Accélération M30",
    H1_ACCELERATION: "Accélération H1",
    H4_ACCELERATION: "Accélération H4",
    LTF_RELEASE_ACTIVE: "Relâchement actif LTF",
    MTF_RELEASE_ACTIVE: "Relâchement actif MTF",
    HTF_RELEASE_ACTIVE: "Relâchement actif HTF",
    LTF_DIVERGENT_RELEASE: "Relâchement divergent LTF",
    MTF_DIVERGENT_RELEASE: "Relâchement divergent MTF",
    HTF_DIVERGENT_RELEASE: "Relâchement divergent HTF",
    DAILY_LONG_ACCUMULATION: "Accumulation longue journalière",
    REJECTION_OR_TRAP_WATCH: "Surveiller rejet ou piège",
    CONFLICT_OR_REINTEGRATION_TEST: "Conflit ou test de réintégration",

    // Reality Board / terrain
    STRUCTURAL_BULLISH_WITH_LTF_MTF_COUNTERFLOW: "Structure haussière dominante avec contre-respiration LTF/MTF",
    LTF_MTF_COUNTERFLOW_ACTIVE: "Contre-respiration LTF/MTF active",
    HIGH_REJECTION_OR_UNWIND: "Rejet haut ou déroulement",
    LATE_HIGH_REJECTION_WITH_DEEP_UNWIND: "Rejet haut tardif avec déroulement profond",
    ALIGNED_OR_PARTIAL: "Aligné ou partiel",
    WATCH_FOR_TRUE_ACCEPTANCE_NOT_LATE_EXTENSION: "Surveiller acceptation propre, pas extension tardive",
    REJECTION_DETACHMENT: "Détachement de rejet",
    LTF_MTF_RELAY: "Relais LTF vers MTF",
    PRICE_REJECTED_LOW: "Prix rejeté vers le bas",
    EVENT_TIME_AHEAD_OF_DETECTED_AT: "Événement détecté avec décalage temporel",
    EVENT_TIME_OFFSET: "Décalage temporel de l’événement",
    LIVE_INFO: "Information live",
    LIVE_ATTENTION_PRESENT: "Attention live présente",
    MULTIREAD_WAKE_TRADER: "Réveil multi-lecture",
    MULTIREAD_CONFLICT: "Conflit multi-lecture",
    MULTIREAD_CONFLICT_OR_REINTEGRATION_TEST: "Conflit multi-lecture ou test de réintégration",
    REINTEGRATION_TEST: "Test de réintégration",

    // B6 / memory
    B6_NO_ALERT: "B6 sans alerte immédiate",
    B6_NO_IMMEDIATE_PRESSURE: "B6 sans pression immédiate",
    LATE_HIGH_REJECTION_WITH_DEEP_UNWIND: "Rejet haut tardif avec déroulement profond",
    RELEASE_UP_PULLBACK_ABSORBED: "Relâchement haussier puis pullback absorbé",
    FALSE_BIRTHS_RELEASE_UP_SECOND_LEG_EXHAUSTION: "Fausses naissances puis deuxième jambe haussière et épuisement",

    // Attention / severity
    WAKE_TRADER: "Réveiller l’attention",
    WATCH_CONTEXT: "Contexte à surveiller",
    INFO: "Information",
    HOT: "Priorité forte",
    WATCH: "Surveillance",
    LOW: "Faible",
    MEDIUM: "Moyen",
    HIGH: "Élevé",

    // Technical data risks
    B8_CROSS_SYMBOL: "B8 cross-symbol",
    B8_CROSS_SYMBOL_DEGRADED: "B8 cross-symbol dégradé",
    B8_INSUFFICIENT_CROSS_PAIR_COVERAGE: "Couverture cross-pair B8 insuffisante",
    EURUSD_HTF_INCOMPLETE: "HTF EURUSD incomplet",
    EURUSD_TEMPORAL_GAPS: "Trous temporels EURUSD",
    GBPUSD_HTF_INCOMPLETE: "HTF GBPUSD incomplet",
    GBPUSD_TEMPORAL_GAPS: "Trous temporels GBPUSD",
    USDJPY_HTF_INCOMPLETE: "HTF USDJPY incomplet",
    USDJPY_TEMPORAL_GAPS: "Trous temporels USDJPY",
    D1_THIN_ROWS: "Données D1 insuffisantes",
    M1_COVERAGE_GAPS: "Trous de couverture M1",
    ZONE_ENGINE_STALE: "Lecture de zone périmée / non fraîche",
    NODE_DB_MISSING: "Node DB absent",
    FLOW_PACKETS_MISSING: "Packets absents",
    FLOW_PACKETS_START_AFTER_MAIN_MOVE: "Packets démarrés après le mouvement principal",
    PACKETS_STALE_AFTER_MARKET_CONTINUES: "Packets arrêtés alors que le prix continue",

    // Execution / cycle
    DRY_RUN: "Cycle test sans envoi",
    dry_run: "Cycle test sans envoi",
    SENT: "Envoyé",
    NOT_SENT: "Non envoyé"
  };

  const KEY_REPLACEMENTS = [
    [/\bdashboard_bias\s*=/gi, "biais dashboard = "],
    [/\bstructure\s*=/gi, "structure = "],
    [/\bcounterflow\s*=/gi, "contre-flux = "],
    [/\bTopdown\s*=/g, "Top-down = "],
    [/\bLiveBrief\s*=/g, "Brief live = "],
    [/\bAlignment\s*=/g, "Alignement = "],
    [/\bbias\s*=/gi, "biais = "],
    [/\bfake_risk\s*=/gi, "risque de fausse lecture = "],
    [/\bstate\s*=/gi, "état = "],
    [/\bphase\s*=/gi, "phase = "],
    [/\bprice\s*=/gi, "prix = "],
    [/\btime\s*=/gi, "temps = "]
  ];

  const SECTION_REPLACEMENTS = [
    [/\bTELEGRAM CANDIDATE\b/g, "MESSAGE TELEGRAM CANDIDAT"],
    [/\bEVIDENCE BUS\b/g, "BUS DE PREUVES"],
    [/\bSESSION MEMORY\b/g, "MÉMOIRE DE SESSION"],
    [/\bCOCKPIT SOURCE\b/g, "SOURCE COCKPIT"],
    [/\bTIME PROFILES\b/g, "PROFILS TEMPS"],
    [/\bDOMINANT RAW\b/gi, "brut dominant"],
    [/\bRAW BIAS\b/gi, "biais brut"],
    [/\bQUALIFIED BIAS\b/gi, "biais qualifié"],
    [/\bLAST EVENT\b/gi, "dernier événement"],
    [/\bMOVEMENT ROLE\b/gi, "rôle du mouvement"],
    [/\bTEXTURE\b/gi, "texture"],
    [/\bPROPAGATION\b/gi, "propagation"],
    [/\bRISKS\b/gi, "risques"],
    [/\bRISK\b/gi, "risque"],
    [/\bFAKE\b/gi, "fausse lecture"]
  ];

  const sortedKeys = Object.keys(PF_FR_LABELS).sort((a, b) => b.length - a.length);

  function escapeRegExp(value) {
    return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  function replaceEnumTokens(text) {
    let output = text;
    for (const key of sortedKeys) {
      const re = new RegExp("(^|[^A-Z0-9_])(" + escapeRegExp(key) + ")(?=$|[^A-Z0-9_])", "g");
      output = output.replace(re, function (_match, prefix) {
        return prefix + PF_FR_LABELS[key];
      });
    }
    return output;
  }

  function fallbackHumanize(text) {
    const trimmed = String(text || "").trim();
    if (!trimmed) return text;
    if (!/^[A-Z0-9_]+$/.test(trimmed)) return text;
    if (PF_FR_LABELS[trimmed]) return PF_FR_LABELS[trimmed];
    return trimmed
      .toLowerCase()
      .replaceAll("_", " ")
      .replace(/^\p{L}/u, function (c) { return c.toUpperCase(); });
  }

  function pfTranslateText(value) {
    if (value === null || value === undefined) return value;
    let text = String(value);
    const original = text;

    // Exact match first.
    const exact = text.trim();
    if (PF_FR_LABELS[exact]) return text.replace(exact, PF_FR_LABELS[exact]);

    for (const [re, replacement] of KEY_REPLACEMENTS) text = text.replace(re, replacement);
    for (const [re, replacement] of SECTION_REPLACEMENTS) text = text.replace(re, replacement);
    text = replaceEnumTokens(text);
    text = fallbackHumanize(text);

    return text || original;
  }

  function shouldSkipElement(el) {
    if (!el || el.nodeType !== 1) return false;
    const tag = el.tagName;
    if (["SCRIPT", "STYLE", "NOSCRIPT", "SVG", "CANVAS"].includes(tag)) return true;
    if (el.closest && el.closest("[data-pf-no-fr], .pf-no-fr")) return true;
    return false;
  }

  function translateTextNode(node) {
    if (!node || !node.nodeValue || !node.nodeValue.trim()) return;
    const parent = node.parentElement;
    if (shouldSkipElement(parent)) return;
    const translated = pfTranslateText(node.nodeValue);
    if (translated !== node.nodeValue) {
      if (parent && !parent.dataset.pfOriginalEnum) {
        parent.dataset.pfOriginalEnum = node.nodeValue.trim();
        parent.title = parent.title || node.nodeValue.trim();
      }
      node.nodeValue = translated;
    }
  }

  function translateFormValue(el) {
    if (!el || shouldSkipElement(el)) return;
    if (!["TEXTAREA", "INPUT"].includes(el.tagName)) return;
    const type = (el.getAttribute("type") || "text").toLowerCase();
    if (!["text", "search", "hidden"].includes(type) && el.tagName !== "TEXTAREA") return;
    if (!el.value || !el.value.trim()) return;
    const translated = pfTranslateText(el.value);
    if (translated !== el.value) {
      if (!el.dataset.pfOriginalValue) el.dataset.pfOriginalValue = el.value;
      el.value = translated;
    }
  }

  function translateAttributes(el) {
    if (!el || shouldSkipElement(el)) return;
    for (const attr of ["title", "aria-label", "placeholder"]) {
      const value = el.getAttribute(attr);
      if (!value) continue;
      const translated = pfTranslateText(value);
      if (translated !== value) el.setAttribute(attr, translated);
    }
  }

  function translateRoot(root) {
    const scope = root || document.body;
    if (!scope) return;

    if (scope.nodeType === Node.TEXT_NODE) {
      translateTextNode(scope);
      return;
    }

    if (scope.nodeType === Node.ELEMENT_NODE) {
      if (shouldSkipElement(scope)) return;
      translateAttributes(scope);
      translateFormValue(scope);
    }

    const walker = document.createTreeWalker(
      scope,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode: function (node) {
          return shouldSkipElement(node.parentElement)
            ? NodeFilter.FILTER_REJECT
            : NodeFilter.FILTER_ACCEPT;
        }
      }
    );

    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach(translateTextNode);

    if (scope.querySelectorAll) {
      scope.querySelectorAll("textarea,input,[title],[aria-label],[placeholder]").forEach(function (el) {
        translateAttributes(el);
        translateFormValue(el);
      });
    }
  }

  function installObserver() {
    const observer = new MutationObserver(function (mutations) {
      for (const mutation of mutations) {
        if (mutation.type === "characterData") {
          translateTextNode(mutation.target);
        }
        if (mutation.type === "childList") {
          mutation.addedNodes.forEach(function (node) { translateRoot(node); });
        }
        if (mutation.type === "attributes") {
          translateAttributes(mutation.target);
          translateFormValue(mutation.target);
        }
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
      characterData: true,
      attributes: true,
      attributeFilter: ["title", "aria-label", "placeholder", "value"]
    });

    return observer;
  }

  window.PF_FR_LABELS = PF_FR_LABELS;
  window.pfFr = function (value) { return pfTranslateText(value); };
  window.pfTranslateDashboardToFR = function () { translateRoot(document.body); };

  function boot() {
    translateRoot(document.body);
    installObserver();
    document.documentElement.dataset.pfFrTraderLabels = "active";
    console.info("PowerFlow FR Trader labels active", Object.keys(PF_FR_LABELS).length, "labels");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot, { once: true });
  } else {
    boot();
  }
})();
