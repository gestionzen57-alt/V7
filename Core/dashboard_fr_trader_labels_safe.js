(function () {
  "use strict";

  const PF_FR = {
    // États de lecture
    "READING_PARTIAL": "Lecture partielle",
    "FULL_STACK_VISIBLE": "Lecture complète",
    "TACTICAL_OK": "Lecture tactique exploitable",
    "RECONSTRUCTED": "Lecture reconstruite",
    "DEGRADED": "Lecture dégradée",
    "UNKNOWN": "Lecture inconnue",
    "PARTIAL_STALE": "Partiel / stale",
    "DATA_HEALTH_PARTIAL_STALE": "Santé data partielle / stale",
    "FRESHNESS_PARTIAL_STALE": "Fraîcheur partielle / stale",

    // Actions / attention
    "WAKE_TRADER": "Réveiller l’attention",
    "WATCH_CONTEXT": "Contexte à surveiller",
    "LIVE_ATTENTION_PRESENT": "Attention live présente",
    "WATCH": "Surveiller",
    "HOT": "Chaud",
    "INFO": "Information",

    // Bias bruts
    "PAIR_UP": "Pression haussière brute",
    "PAIR_DOWN": "Pression baissière brute",
    "NEUTRAL": "Neutre",

    // Zones
    "HIGH_ZONE": "Zone haute",
    "LOW_ZONE": "Zone basse",
    "MID_ZONE": "Zone médiane",
    "HIGH_ZONE_REJECTION": "Rejet de zone haute",
    "HIGH_ZONE_EXHAUSTION": "Épuisement en zone haute",
    "HIGH_ZONE_EXHAUSTION_RISK": "Risque d’épuisement en zone haute",
    "EXHAUSTION_RISK": "Risque d’épuisement",
    "LOW_ZONE_DEFENDED": "Zone basse défendue",
    "FAILED_REINTEGRATION": "Réintégration échouée",
    "REINTEGRATION_ATTEMPT": "Tentative de réintégration",

    // Nodes
    "HIGH_REJECTION_NODE": "Node de rejet haut",
    "LOW_REJECTION_NODE": "Node de rejet bas",
    "PULLBACK_ABSORBED_NODE": "Node de pullback absorbé",
    "SECOND_LEG_TRIGGER_NODE": "Node de déclenchement deuxième jambe",
    "HIGH_EXHAUSTION_NODE": "Node d’épuisement haut",

    // Rôles de mouvement
    "POST_HIGH_UNWIND": "Déroulement après rejet haut",
    "POST_LOW_REACTION": "Réaction après zone basse",
    "RELEASE_UP": "Relâchement haussier",
    "RELEASE_DOWN": "Relâchement baissier",
    "RELEASE_ACTIVE": "Relâchement actif",
    "FIRST_LEG_UP": "Première jambe haussière",
    "FIRST_LEG_DOWN": "Première jambe baissière",
    "SECOND_LEG_UP": "Deuxième jambe haussière",
    "SECOND_LEG_DOWN": "Deuxième jambe baissière",
    "PULLBACK_ABSORBED": "Pullback absorbé",
    "COUNTER_BREATH": "Respiration inverse",
    "COUNTER_BREATH_UP": "Respiration inverse haussière",
    "COUNTER_BREATH_DOWN": "Respiration inverse baissière",
    "COUNTER_BREATH_REJECTED": "Respiration inverse rejetée",
    "LATE_UNWIND": "Déroulement tardif",
    "LATE_UP": "Hausse tardive",
    "FALSE_BIRTH": "Fausse naissance",
    "EVENT_STACK_ONLY": "Empilement d’événements seulement",

    // Structure / cockpit
    "CONFLICT": "Conflit",
    "CONFLICT_OR_REINTEGRATION_TEST": "Conflit ou test de réintégration",
    "MULTIREAD_CONFLICT": "Conflit multi-lecture",
    "MULTIREAD_WAKE_TRADER": "Réveil multi-lecture",
    "STRUCTURAL_BULLISH_WITH_LTF_MTF_COUNTERFLOW": "Structure haussière avec contre-respiration LTF/MTF",
    "LTF_MTF_COUNTERFLOW_ACTIVE": "Contre-respiration LTF/MTF active",
    "RELEASE_VALIDATED": "Relâchement validé",
    "HIGH_REJECTION_OR_UNWIND": "Rejet haut ou déroulement",
    "LATE_HIGH_REJECTION_WITH_DEEP_UNWIND": "Rejet haut tardif avec déroulement profond",
    "ALIGNED_OR_PARTIAL": "Aligné ou partiel",
    "LONG_ACCUMULATION": "Accumulation longue",
    "REJECTION_OR_TRAP_WATCH": "Surveillance rejet ou piège",
    "ALERT_READY": "Alerte prête",
    "NO_ALERT": "Pas d’alerte immédiate",

    // Events / phases
    "M1_ACCELERATION": "Accélération M1",
    "M5_ACCELERATION": "Accélération M5",
    "M15_ACCELERATION": "Accélération M15",
    "M30_ACCELERATION": "Accélération M30",
    "H1_ACCELERATION": "Accélération H1",
    "H4_ACCELERATION": "Accélération H4",
    "H1_ABSORPTION_OR_REJECTION": "H1 absorption ou rejet",
    "M15_REACTION_OR_REJECTION": "M15 réaction ou rejet",
    "HTF_REACTION_ZONE": "Zone de réaction HTF",
    "LTF_RELEASE_ACTIVE": "Relâchement LTF actif",
    "MTF_REACTION_OR_REJECTION": "Réaction ou rejet MTF",
    "HTF_REACTION_OR_REJECTION": "Réaction ou rejet HTF",
    "THIN_DATA": "Données fines / insuffisantes",

    // Data / risques techniques
    "B8_INSUFFICIENT_CROSS_PAIR_COVERAGE": "Couverture cross-pair B8 insuffisante",
    "EURUSD_HTF_INCOMPLETE": "HTF EURUSD incomplet",
    "EURUSD_TEMPORAL_GAPS": "Trous temporels EURUSD",
    "GBPUSD_HTF_INCOMPLETE": "HTF GBPUSD incomplet",
    "GBPUSD_TEMPORAL_GAPS": "Trous temporels GBPUSD",
    "USDJPY_HTF_INCOMPLETE": "HTF USDJPY incomplet",
    "USDJPY_TEMPORAL_GAPS": "Trous temporels USDJPY",
    "D1_THIN_ROWS": "D1 lignes insuffisantes",
    "HTF_INCOMPLETE": "HTF incomplet",
    "TEMPORAL_GAPS": "Trous temporels",

    // Reality Board
    "WATCH_FOR_TRUE_ACCEPTANCE_NOT_LATE_EXTENSION": "Surveiller acceptation propre, pas extension tardive",
    "REJECTION_DETACHMENT": "Détachement de rejet",
    "LTF_MTF_RELAY": "Relais LTF vers MTF",
    "PRICE_REJECTED_LOW": "Prix rejeté vers le bas",
    "EVENT_TIME_AHEAD_OF_DETECTED_AT": "Événement détecté avec avance temporelle",
    "EVENT_TIME_OFFSET": "Décalage temporel événement",
    "REJECTION_DETACHMENT_LIMITS": "Limites du détachement de rejet"
  };

  const PHRASE_FR = [
    [/bias pression DOWN/gi, "biais de pression baissière"],
    [/bias pression UP/gi, "biais de pression haussière"],
    [/bias neutral/gi, "biais neutre"],
    [/fake faible/gi, "risque de fausse lecture faible"],
    [/fake moyen/gi, "risque de fausse lecture moyen"],
    [/fake low/gi, "risque de fausse lecture faible"],
    [/fake medium/gi, "risque de fausse lecture moyen"],
    [/absorption or rejection/gi, "absorption ou rejet"],
    [/m1 acceleration/gi, "accélération M1"],
    [/m5 acceleration/gi, "accélération M5"],
    [/m15 acceleration/gi, "accélération M15"],
    [/m30 acceleration/gi, "accélération M30"],
    [/h1 acceleration/gi, "accélération H1"],
    [/h4 acceleration/gi, "accélération H4"],
    [/h1 absorption or rejection/gi, "H1 absorption ou rejet"],
    [/m15 reaction or rejection/gi, "M15 réaction ou rejet"],
    [/release active/gi, "relâchement actif"],
    [/thin data/gi, "données fines / insuffisantes"],
    [/dashboard bias/gi, "biais dashboard"],
    [/dominant brut/gi, "dominante brute"],
    [/counterflow/gi, "contre-respiration"],
    [/topdown/gi, "lecture top-down"],
    [/live brief/gi, "brief live"],
    [/alignment/gi, "alignement"],
    [/confidence/gi, "confiance"],
    [/last/gi, "dernier"],
    [/age/gi, "âge"],
    [/freshness/gi, "fraîcheur"]
  ];

  function translateText(s) {
    if (!s || typeof s !== "string") return s;

    let out = s;

    const keys = Object.keys(PF_FR).sort((a, b) => b.length - a.length);
    for (const key of keys) {
      out = out.replaceAll(key, PF_FR[key]);
    }

    for (const pair of PHRASE_FR) {
      out = out.replace(pair[0], pair[1]);
    }

    return out;
  }

  function shouldSkipNode(node) {
    if (!node || !node.parentElement) return true;
    const tag = node.parentElement.tagName;
    return ["SCRIPT", "STYLE", "TEXTAREA", "INPUT", "CODE", "PRE"].includes(tag);
  }

  function translatePage(root) {
    try {
      const walker = document.createTreeWalker(
        root || document.body,
        NodeFilter.SHOW_TEXT,
        {
          acceptNode: function (node) {
            if (shouldSkipNode(node)) return NodeFilter.FILTER_REJECT;
            if (!node.nodeValue) return NodeFilter.FILTER_SKIP;
            const v = node.nodeValue;
            if (!v.includes("_") && !/bias|fake|acceleration|reaction|rejection|counterflow|freshness|alignment|confidence|release active|thin data/i.test(v)) {
              return NodeFilter.FILTER_SKIP;
            }
            return NodeFilter.FILTER_ACCEPT;
          }
        }
      );

      const nodes = [];
      while (walker.nextNode()) nodes.push(walker.currentNode);

      for (const node of nodes) {
        const before = node.nodeValue;
        const after = translateText(before);
        if (after !== before) node.nodeValue = after;
      }

      document.querySelectorAll("[title], [data-label], [data-tooltip]").forEach(el => {
        ["title", "data-label", "data-tooltip"].forEach(attr => {
          const v = el.getAttribute(attr);
          if (v) el.setAttribute(attr, translateText(v));
        });
      });
    } catch (e) {
      console.warn("[PowerFlow FR Trader] traduction ignorée:", e);
    }
  }

  window.pfTranslatePage = function () {
    translatePage(document.body);
  };

  function boot() {
    translatePage(document.body);

    const obs = new MutationObserver(function (mutations) {
      for (const m of mutations) {
        for (const n of m.addedNodes) {
          if (n.nodeType === Node.ELEMENT_NODE) translatePage(n);
          if (n.nodeType === Node.TEXT_NODE && n.nodeValue) {
            const after = translateText(n.nodeValue);
            if (after !== n.nodeValue) n.nodeValue = after;
          }
        }
      }
    });

    obs.observe(document.body, {
      childList: true,
      subtree: true,
      characterData: true
    });

    setTimeout(() => translatePage(document.body), 300);
    setTimeout(() => translatePage(document.body), 900);
    setTimeout(() => translatePage(document.body), 1800);
    setTimeout(() => translatePage(document.body), 3500);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
