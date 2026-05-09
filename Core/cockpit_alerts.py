# ============================================================
#  PowerFlow V3 — alerts.py
# ============================================================

import asyncio
import aiohttp
import urllib.parse
import os
import time
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from collections import deque
from datetime import datetime
from models import Signal, HTFContext, Brain
from system_config import (
    TELEGRAM_TOKEN, TELEGRAM_CHAT_ID,
    GRAPH_ENABLED, GRAPH_PREMIUM_ONLY, GRAPH_HISTORY_LEN,
    DEBUG_CROSS
)

# ------------------------------------------------------------
#  HISTORIQUE GRAPHIQUE
# ------------------------------------------------------------
graph_history = {}

def push_graph_point(tick, brain):
    key = f"{tick.symbol}M{tick.timeframe}"
    if key not in graph_history:
        graph_history[key] = deque(maxlen=GRAPH_HISTORY_LEN)
    graph_history[key].append({
        "ts"  : datetime.now().strftime("%H:%M"),
        "a"   : tick.val_a,
        "b"   : tick.val_b,
        "bid" : tick.bid,
    })

# ------------------------------------------------------------
#  CONSTANTES
# ------------------------------------------------------------
EMOJIS = {
    "CROSS"          : "📊",
    "SUPER_SWITCH"   : "💥",
    "FAKEOUT"        : "⚠️",
    "SNIPER_REVERSAL": "🎯",
    "CONVERGENCE"    : "🔗",
    "SLINGSHOT"      : "🪃",
    "EXTREME_HIGH"   : "🔴",
    "EXTREME_LOW"    : "🟢",
    "KISS_REJECT"    : "💋",
    "APPROACH"       : "⏳",
}

LEVEL_EMOJI = {
    "PREMIUM"  : "🏆",
    "CONFIRM"  : "✅",
    "STANDARD" : "📌",
}

TF_LABELS = {1:"M1",5:"M5",15:"M15",30:"M30",60:"H1",240:"H4"}

# ------------------------------------------------------------
#  FILTRE ALERTES LIVE — réduction du spam Telegram
# ------------------------------------------------------------
#  Règles (signaux PowerFlow réels, pas de noms génériques) :
#    - M1            → aucune alerte live
#    - M5            → principaux uniquement
#    - M15 / M30 / H1 → principaux + contexte
#    - H4 / D1       → contexte uniquement
#    - COMPRESSION_* → JAMAIS seul en live (toutes TF confondues)
#
#  Le filtre ne bloque QUE les envois Telegram (texte + photo).
#  La persistance (datalake, log_cross, log_context) continue à tourner
#  pour conserver une trace complète, y compris des signaux filtrés.
# ------------------------------------------------------------
SIGNALS_PRINCIPAUX = {
    "CROSS", "KISS_REJECT", "SUPER_SWITCH",
    "CONVERGENCE", "SLINGSHOT", "FAKEOUT",
}

SIGNALS_CONTEXTE = {
    "ZONE_BATTLE", "EXTREME_HIGH", "EXTREME_LOW", "APPROACH",
}

SIGNALS_COMPRESSION_BLOQUES = {
    "COMPRESSION", "COMPRESSION_BREAK", "COMPRESSION_SQUEEZE",
}

# TF (en minutes) -> catégories autorisées côté Telegram
TF_TO_TELEGRAM_CATEGORIES = {
    1:    set(),                                     # M1  : rien
    5:    {"PRINCIPAL"},                             # M5  : principaux seuls
    15:   {"PRINCIPAL", "CONTEXTE"},                 # M15 : tout
    30:   {"PRINCIPAL", "CONTEXTE"},                 # M30 : tout
    60:   {"PRINCIPAL", "CONTEXTE"},                 # H1  : tout
    240:  {"CONTEXTE"},                              # H4  : contexte seul
    1440: {"CONTEXTE"},                              # D1  : contexte seul
}


def should_send_live_alert(sig) -> bool:
    """Décide si le signal doit déclencher une alerte Telegram live.

    Ne bloque QUE les envois Telegram. Les logs DB continuent en amont.
    Non-bloquant : en cas d'attribut manquant, renvoie False par sécurité
    (mieux manquer une alerte que planter le moteur)."""
    try:
        stype = getattr(sig, "signal_type", None)
        tf    = getattr(sig, "timeframe", None)

        if stype is None or tf is None:
            return False

        # Règle 1 : compressions jamais en live, toutes TF confondues
        if stype in SIGNALS_COMPRESSION_BLOQUES:
            return False

        # Règle 2 : catégories autorisées pour cette TF
        allowed = TF_TO_TELEGRAM_CATEGORIES.get(tf, set())
        if not allowed:
            return False   # TF inconnu ou interdit (ex : M1)

        if stype in SIGNALS_PRINCIPAUX and "PRINCIPAL" in allowed:
            return True
        if stype in SIGNALS_CONTEXTE and "CONTEXTE" in allowed:
            return True

        return False
    except Exception as e:
        print(f"❌ should_send_live_alert : {e}")
        return False

# ------------------------------------------------------------
#  FORMATAGE MESSAGE
# ------------------------------------------------------------
def format_message(sig: Signal, brain: Brain) -> str:
    emoji   = EMOJIS.get(sig.signal_type, "📡")
    lv_emoji= LEVEL_EMOJI.get(sig.level, "")
    tf_lbl  = TF_LABELS.get(sig.timeframe, f"M{sig.timeframe}")
    lines   = []

    lines.append(
        f"{emoji} <b>{sig.signal_type}</b> — "
        f"{sig.symbol} {tf_lbl} "
        f"{lv_emoji} <b>{sig.level}</b> (score {sig.score})"
    )
    lines.append(
        f"💪 <b>{sig.dev_strong.upper()}</b> ▶ {sig.dev_weak.upper()}"
    )
    if sig.volume_badge:
        lines.append(sig.volume_badge)
    if sig.note:
        lines.append(sig.note)
    if sig.htf:
        h = sig.htf
        lines.append("─────────────────")
        lines.append(f"<b>Biais HTF :</b> {h.bias} | {h.bias_state}")
        lines.append(
            f"<b>Scénario :</b> {h.scenario} | "
            f"Leader : {h.leader} | Rang : {h.fractal_rank}/5"
        )
        lines.append(f"<b>Alignés :</b> {h.aligned_count} TF")
        if h.details:
            lines.append(" ".join(h.details))
    if sig.convergence:
        c = sig.convergence
        lines.append("─────────────────")
        lines.append(
            f"🔗 <b>Convergence</b> {c['label1']}+{c['label2']} "
            f"— {c['niveau']} ({c['delta']} min)"
        )
    if not sig.spread_ok:
        lines.append("⛔ Spread élevé — prudence")

    sym      = sig.symbol
    snapshot = []
    for tf_n, lbl in [(5,"M5"),(15,"M15"),(30,"M30"),(60,"H1"),(240,"H4")]:
        k = f"{sym}M{tf_n}"
        if k in brain:
            t   = brain[k]
            dom = t.dev_a if t.val_a >= t.val_b else t.dev_b
            val = max(t.val_a, t.val_b)
            snapshot.append(f"{lbl}:{dom.upper()}({val:.0f})")
    if snapshot:
        lines.append("─────────────────")
        lines.append("📋 " + " | ".join(snapshot))

    return "\n".join(lines)    # ← vrai \n, pas \\n

# ------------------------------------------------------------
#  ENVOI TELEGRAM — texte
# ------------------------------------------------------------
async def send_telegram_text(text: str):
    try:
        encoded = urllib.parse.quote(text)
        url = (
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
            f"/sendMessage?chat_id={TELEGRAM_CHAT_ID}"
            f"&text={encoded}&parse_mode=HTML"
        )
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    print(f"❌ Telegram erreur {resp.status}: {body[:100]}")
    except Exception as e:
        print(f"❌ Telegram réseau : {e}")

# ------------------------------------------------------------
#  ENVOI TELEGRAM — photo
# ------------------------------------------------------------
async def send_telegram_photo(path: str, caption: str):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field("chat_id", TELEGRAM_CHAT_ID)
            data.add_field("caption", caption, content_type="text/plain")
            data.add_field("parse_mode", "HTML")
            with open(path, "rb") as f:
                data.add_field(
                    "photo", f,
                    filename=os.path.basename(path),
                    content_type="image/png"
                )
            async with session.post(url, data=data) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    print(f"❌ Telegram photo erreur {resp.status}: {body[:100]}")
    except Exception as e:
        print(f"❌ Telegram photo réseau : {e}")

# ------------------------------------------------------------
#  GRAPHIQUE
# ------------------------------------------------------------
def should_send_graph(sig: Signal) -> bool:
    if not GRAPH_ENABLED:
        return False
    if GRAPH_PREMIUM_ONLY:
        return sig.is_premium
    return True

def create_chart(sig: Signal) -> str | None:
    key  = f"{sig.symbol}M{sig.timeframe}"
    hist = list(graph_history.get(key, []))
    if len(hist) < 5:
        return None

    tf_lbl = TF_LABELS.get(sig.timeframe, f"M{sig.timeframe}")
    xs     = list(range(len(hist)))
    ya     = [p["a"] for p in hist]
    yb     = [p["b"] for p in hist]
    lbls   = [p["ts"] for p in hist]

    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(13, 6))
    ax.plot(xs, ya, color="#00d4ff", linewidth=2.2, label=sig.dev_strong.upper())
    ax.plot(xs, yb, color="#ff5e7a", linewidth=2.2, label=sig.dev_weak.upper())
    for lvl, col, ls in [(85,"#ffb000","--"),(15,"#00ff88","--"),(50,"white",":")]:
        ax.axhline(lvl, color=col, linestyle=ls, linewidth=1, alpha=0.6)
    ax.scatter(xs[-1], ya[-1], color="#00d4ff", s=60, zorder=5)
    ax.scatter(xs[-1], yb[-1], color="#ff5e7a", s=60, zorder=5)
    ax.set_title(
        f"PowerFlow — {sig.symbol} {tf_lbl} | {sig.signal_type}",
        fontsize=14, fontweight="bold"
    )
    ax.set_ylim(0, 100)
    ax.set_ylabel("Force devise")
    ax.grid(True, alpha=0.12)
    ax.legend(loc="upper left")
    step = max(1, len(xs) // 8)
    ax.set_xticks(xs[::step])
    ax.set_xticklabels(lbls[::step], fontsize=8)
    os.makedirs("output", exist_ok=True)
    path = f"output/{sig.symbol}_{tf_lbl}_{sig.signal_type}_{int(time.time())}.png"
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path

# ------------------------------------------------------------
#  SEND ALERT — point d'entrée unique ← UNE SEULE FOIS
# ------------------------------------------------------------
async def send_alert(sig: Signal, htf: HTFContext, brain: Brain):
    print(f"🚨 send_alert : {sig.symbol} {sig.signal_type} {sig.level}")

    # ------------------------------------------------------------
    #  FILTRE TELEGRAM — coupe uniquement les envois Telegram.
    #  Les logs datalake / persist_signal restent toujours exécutés
    #  pour conserver une trace complète, même des signaux filtrés.
    # ------------------------------------------------------------
    telegram_ok = should_send_live_alert(sig)
    if not telegram_ok:
        print(
            f"🔕 Telegram filtré : {sig.symbol} M{sig.timeframe} "
            f"{sig.signal_type} (DB toujours loggée)"
        )

    # Formatage + envoi Telegram uniquement si le filtre laisse passer
    if telegram_ok:
        try:
            msg = format_message(sig, brain)
            print(f"✅ Message formaté : {len(msg)} chars")
        except Exception as e:
            print(f"❌ format_message : {e}")
            msg = None

        if msg is not None:
            if DEBUG_CROSS:
                print("─" * 50)
                print(msg)
                print("─" * 50)

            try:
                await send_telegram_text(msg)
                print(f"✅ Telegram envoyé")
            except Exception as e:
                print(f"❌ send_telegram_text : {e}")

            if should_send_graph(sig):
                try:
                    chart_path = create_chart(sig)
                    if chart_path:
                        caption = (
                            f"{sig.symbol} {TF_LABELS.get(sig.timeframe)} "
                            f"— {sig.signal_type} {sig.level}"
                        )
                        await send_telegram_photo(chart_path, caption)
                        print(f"✅ Graphique envoyé")
                except Exception as e:
                    print(f"❌ create_chart : {e}")

    # ------------------------------------------------------------
    #  PERSISTANCE DATALAKE — TOUJOURS exécutée, y compris si Telegram filtré
    # ------------------------------------------------------------
    try:
        from datalake import log_cross, log_context
        from utils import get_session
        log_cross(sig, htf=htf, note=sig.note)
        log_context(sig, brain, htf=htf,
                    session=get_session(datetime.now().hour))
    except Exception as e:
        print(f"❌ DB log : {e}")
