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

    // Actions / attention
    "WAKE_TRADER": "Réveiller l’attention",
    "WATCH_CONTEXT": "Contexte à surveiller",
    "LIVE_ATTENTION_PRESENT": "Attention live présente",

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

    // Rôles de mouvement
    "POST_HIGH_UNWIND": "Déroulement après rejet haut",
    "POST_LOW_REACTION": "Réaction après zone basse",
    "RELEASE_UP": "Relâchement haussier",
    "RELEASE_DOWN": "Relâchement baissier",
    "RELEASE_ACTIVE": "Relâchement actif",
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

    // Events / phases
    "M1_ACCELERATION": "Accélération M1",
    "M5_ACCELERATION": "Accélération M5",
    "M15_ACCELERATION": "Accélération M15",
    "M30_ACCELERATION": "Accélération M30",
    "H1_ACCELERATION": "Accélération H1",
    "H4_ACCELERATION": "Accélération H4",
    "THIN_DATA": "Données fines / insuffisantes",

    // Data / risques techniques
    "B8_INSUFFICIENT_CROSS_PAIR_COVERAGE": "Couverture cross-pair B8 insuffisante",
    "EURUSD_HTF_INCOMPLETE": "HTF EURUSD incomplet",
    "EURUSD_TEMPORAL_GAPS": "Trous temporels EURUSD",
    "GBPUSD_HTF_INCOMPLETE": "HTF GBPUSD incomplet",
    "GBPUSD_TEMPORAL_GAPS": "Trous temporels GBPUSD",
    "USDJPY_HTF_INCOMPLETE": "HTF USDJPY incomplet",
    "USDJPY_TEMPORAL_GAPS": "Trous temporels USDJPY",
    "DATA_HEALTH_PARTIAL_STALE": "Santé data partielle / stale",
    "FRESHNESS_PARTIAL_STALE": "Fraîcheur partielle / stale",

    // Reality Board
    "WATCH_FOR_TRUE_ACCEPTANCE_NOT_LATE_EXTENSION": "Surveiller acceptation propre, pas extension tardive",
    "REJECTION_DETACHMENT": "Détachement de rejet",
    "LTF_MTF_RELAY": "Relais LTF vers MTF",
    "PRICE_REJECTED_LOW": "Prix rejeté vers le bas",
    "EVENT_TIME_AHEAD_OF_DETECTED_AT": "Événement détecté avec avance temporelle",
    "EVENT_TIME_OFFSET": "Décalage temporel événement"
  };

  function translateText(s) {
    if (!s || typeof s !== "string") return s;

    let out = s;

    const keys = Object.keys(PF_FR).sort((a, b) => b.length - a.length);

    for (const key of keys) {
      const val = PF_FR[key];
      out = out.replaceAll(key, val);
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
            if (!node.nodeValue || !node.nodeValue.includes("_")) return NodeFilter.FILTER_SKIP;
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

    setTimeout(() => translatePage(document.body), 500);
    setTimeout(() => translatePage(document.body), 1500);
    setTimeout(() => translatePage(document.body), 3000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
