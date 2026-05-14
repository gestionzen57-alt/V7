#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations


# PF_V767_FINAL_FR_LABELS_V1
# Trader-facing French labels only. Raw machine enums remain unchanged.

_PF_V767_FR = {
    "DATA FIRST": "LECTURE TERRAIN",
    "REALITY BOARD": "RÉALITÉ MARCHÉ",
    "Reality Board": "Réalité marché",
    "ALIGNED_OR_PARTIAL": "alignement partiel",
    "LATE_HIGH_REJECTION_WITH_DEEP_UNWIND": "high tardif rejeté puis unwind profond",
    "READING_PARTIAL": "lecture partielle",
    "HIGH_ZONE_EXHAUSTION_RISK": "risque d’épuisement en zone haute",
    "HIGH_ZONE_REJECTION": "rejet de zone haute",
    "EXHAUSTION_RISK": "risque d’épuisement",
    "PRICE_REJECTED_LOW": "prix rejeté en bas",
    "LTF_MTF_RELAY": "relais LTF vers MTF",
    "REJECTION_DETACHMENT": "détachement de rejet",
}

def _pf_v767_fr(value):
    out = str(value or "")
    fixes = {"Ã©":"é","Ã¨":"è","Ãª":"ê","Ã ":"à","Ã´":"ô","Ã®":"î","Ã§":"ç","â€™":"’","â€”":"-","â†’":"→"}
    for old, new in fixes.items():
        out = out.replace(old, new)
    for old, new in _PF_V767_FR.items():
        out = out.replace(old, new)
    return out

def _pf_v767_fr_state_file(path):
    import json as _json
    from pathlib import Path as _Path
    p = _Path(path)
    if not p.exists():
        return False
    state = _json.loads(p.read_text(encoding="utf-8", errors="replace"))

    labels = state.get("labels_fr")
    if not isinstance(labels, dict):
        labels = {}

    def tr(raw, fallback=""):
        return _PF_V767_FR.get(str(raw or ""), _pf_v767_fr(raw or fallback))

    labels.update({
        "board_title_fr": "RÉALITÉ MARCHÉ",
        "priority_label_fr": "LECTURE TERRAIN",
        "reading_status_fr": tr(state.get("reading_status") or state.get("data_visibility"), "lecture partielle"),
        "data_visibility_fr": tr(state.get("data_visibility"), "lecture partielle"),
        "session_alignment_fr": tr(state.get("session_alignment"), "alignement partiel"),
        "film_sequence_fr": tr(state.get("film_sequence") or state.get("b6_nearest_film")),
        "b6_nearest_film_fr": tr(state.get("b6_nearest_film") or state.get("film_sequence")),
        "qualified_bias_fr": tr(state.get("qualified_bias") or state.get("current_move_role")),
        "move_role_fr": tr(state.get("current_move_role") or state.get("qualified_bias")),
    })
    for k, v in list(labels.items()):
        if isinstance(v, str):
            labels[k] = _pf_v767_fr(v)
    state["labels_fr"] = labels

    state["display_fr"] = {
        "titre": "RÉALITÉ MARCHÉ",
        "priorité": "LECTURE TERRAIN",
        "statut_lecture": labels.get("reading_status_fr", "lecture partielle"),
        "alignement_session": labels.get("session_alignment_fr", "alignement partiel"),
        "film_mémoire": labels.get("film_sequence_fr") or labels.get("b6_nearest_film_fr"),
        "lecture_active": labels.get("qualified_bias_fr") or labels.get("move_role_fr"),
    }

    telegram = state.get("telegram_candidate")
    if isinstance(telegram, dict):
        text = _pf_v767_fr(telegram.get("text_fr", ""))
        text = text.replace("GBPUSD - RÉALITÉ MARCHÉ", "GBPUSD - Réalité marché")
        text = text.replace("GBPUSD — Réalité marché", "GBPUSD - Réalité marché")
        telegram["text_fr"] = text
        state["telegram_candidate"] = telegram

    state["final_fr_labels_polish"] = "V1_DISPLAY_ONLY"
    p.write_text(_json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    return True

def _pf_v767_fr_postprocess_outputs():
    try:
        from pathlib import Path as _Path
        root = _Path.cwd()
        for path in (root / "output" / "dashboard_surface").glob("*/reality_board_state.json"):
            _pf_v767_fr_state_file(path)
    except Exception as exc:
        print("[WARN] V7.6.7 final FR label polish failed:", exc)

try:
    import atexit as _pf_v767_fr_atexit
    _pf_v767_fr_atexit.register(_pf_v767_fr_postprocess_outputs)
except Exception as exc:
    print("[WARN] V7.6.7 final FR label registration failed:", exc)

# PF_V767_FINAL_FR_LABELS_V1_END



# PF_V767_DIRECT_OUTPUT_CLEANUP_V8
# Output-level cleanup for Reality Board display fields.
# Registered with atexit near the top of the file so it runs after direct CLI generation.

def _pf_v767_v8_text_clean(value):
    out = str(value or "")
    replacements = {
        "GBPUSD Ã¢â‚¬â€ Reality Board": "GBPUSD - Reality Board",
        "GBPUSD â€” Reality Board": "GBPUSD - Reality Board",
        "GBPUSD — Reality Board": "GBPUSD - Reality Board",
        "GBPUSD ÔÇö Reality Board": "GBPUSD - Reality Board",
        "GBPUSD “” Reality Board": "GBPUSD - Reality Board",
        "GBPUSD ”” Reality Board": "GBPUSD - Reality Board",
        "Ã¢â‚¬â€": "-",
        "Ã¢â‚¬â€™": "->",
        "Ã¢â€â€™": "->",
        "Ã¢â‚¬â„¢": "'",
        "â€™": "'",
        "â€”": "-",
        "ÔÇö": "-",
        "“”": "-",
        "””": "-",
        "ÃƒÂ©": "é",
        "ÃƒÂ¨": "è",
        "ÃƒÂª": "ê",
        "ÃƒÂ ": "à",
        "ÃƒÂ´": "ô",
        "ÃƒÂ®": "î",
        "ÃƒÂ§": "ç",
        "Alternative : Alternative :": "Alternative :",
        "Piège : Piège :": "Piège :",
        "Piege : Piege :": "Piege :",
    }
    for old, new in replacements.items():
        out = out.replace(old, new)
    return out


def _pf_v767_v8_scalar(value):
    if value in (None, "", [], {}):
        return ""
    if isinstance(value, (dict, list, tuple, set)):
        return ""
    return str(value)


def _pf_v767_v8_parse_profile(value):
    import ast as _ast

    if isinstance(value, dict):
        return value
    raw = str(value or "").strip()
    if raw.startswith("{") and raw.endswith("}"):
        try:
            parsed = _ast.literal_eval(raw)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            return {}
    return {}


def _pf_v767_v8_enum(value):
    raw = _pf_v767_v8_scalar(value)
    if not raw:
        return ""
    mapping = {
        "ABSORPTION_OR_REJECTION": "absorption / rejet",
        "RELEASE_ACTIVE": "release active",
        "HIGH_ZONE_REJECTION": "rejet zone haute",
        "HIGH_ZONE_EXHAUSTION_RISK": "risque epuisement zone haute",
        "PAIR_UP": "pression UP",
        "PAIR_DOWN": "pression DOWN",
        "UNKNOWN": "inconnu",
        "LOW": "faible",
        "MEDIUM": "moyen",
        "HIGH": "fort",
        "PARTIAL_STALE": "partiel / stale",
        "READING_PARTIAL": "lecture partielle",
    }
    return mapping.get(raw, raw.replace("_", " ").lower())


def _pf_v767_v8_short_time(value):
    raw = _pf_v767_v8_scalar(value)
    if not raw:
        return ""
    if "T" in raw:
        try:
            return raw.split("T", 1)[1][:5]
        except Exception:
            return raw
    return raw


def _pf_v767_v8_compact_profile(value, fallback_label):
    src = _pf_v767_v8_parse_profile(value)
    if src and isinstance(src.get("last_event"), dict):
        src = src["last_event"]

    if not src:
        raw = _pf_v767_v8_text_clean(value)
        if not raw:
            return "non disponible"
        if "events_total" in raw or "{" in raw:
            return "profil actif, detail brut masque"
        return raw[:220]

    ctx = src.get("context") if isinstance(src.get("context"), dict) else {}
    tf = _pf_v767_v8_scalar(src.get("timeframe") or src.get("tf") or src.get("profile"))
    event = _pf_v767_v8_enum(src.get("event_type") or src.get("event") or src.get("last_event"))
    phase = _pf_v767_v8_enum(src.get("phase_after") or src.get("phase") or src.get("state") or ctx.get("tf_phase") or ctx.get("profile_state"))
    bias = _pf_v767_v8_enum(src.get("bias") or ctx.get("dominant_bias"))
    fake = _pf_v767_v8_enum(src.get("fake_risk") or ctx.get("fake_risk"))
    price = _pf_v767_v8_scalar(src.get("price"))
    ts = _pf_v767_v8_short_time(src.get("timestamp_utc") or src.get("updated_at"))

    parts = []
    head = " ".join(x for x in [tf, event or phase] if x).strip()
    if head:
        parts.append(head)
    if bias:
        parts.append("biais " + bias)
    if fake:
        parts.append("fake " + fake)
    if price:
        parts.append("prix " + price)
    if ts:
        parts.append("temps " + ts)

    return " | ".join(parts[:5]) if parts else (fallback_label + " non disponible")


def _pf_v767_v8_strip_prefix(text, prefixes):
    out = str(text or "").strip()
    for prefix in prefixes:
        if out.lower().startswith(prefix.lower()):
            return out[len(prefix):].strip()
    return out


def _pf_v767_v8_clean_state_file(path):
    import json as _json
    from pathlib import Path as _Path

    p = _Path(path)
    if not p.exists():
        return False

    state = _json.loads(p.read_text(encoding="utf-8", errors="replace"))

    labels = {
        "htf": "HTF - Analyse",
        "mtf": "MTF - Plan",
        "ltf": "LTF - Action",
    }

    roles = state.get("time_profile_roles")
    if isinstance(roles, dict):
        for key, label in labels.items():
            item = roles.get(key)
            if isinstance(item, dict):
                raw = item.get("summary_fr") or item.get("summary") or item
                item["label_fr"] = label
                item["summary_fr"] = _pf_v767_v8_compact_profile(raw, label)
                item["state"] = _pf_v767_v8_scalar(item.get("state")) or "ACTIVE"
                roles[key] = item

    telegram = state.get("telegram_candidate")
    if isinstance(telegram, dict):
        text = _pf_v767_v8_text_clean(telegram.get("text_fr", ""))
        if "Reality Board" in text:
            lines = text.splitlines()
            if lines:
                lines[0] = "GBPUSD - Reality Board"
                text = "\n".join(lines)
        text = text.replace("Alternative : Alternative :", "Alternative :")
        telegram["text_fr"] = text
        state["telegram_candidate"] = telegram

    for k in ("alternative_strategy", "alternative"):
        item = state.get(k)
        if isinstance(item, dict) and isinstance(item.get("label_fr"), str):
            clean = _pf_v767_v8_text_clean(item["label_fr"])
            item["label_fr"] = _pf_v767_v8_strip_prefix(clean, ("Alternative :", "Alternative:"))

    item = state.get("trap")
    if isinstance(item, dict) and isinstance(item.get("label_fr"), str):
        clean = _pf_v767_v8_text_clean(item["label_fr"])
        item["label_fr"] = _pf_v767_v8_strip_prefix(clean, ("Piège :", "Piege :", "Piège:", "Piege:"))

    for container_key in ("dominant_strategy", "labels_fr"):
        item = state.get(container_key)
        if isinstance(item, dict):
            for k, v in list(item.items()):
                if isinstance(v, str):
                    item[k] = _pf_v767_v8_text_clean(v)

    state["semantic_display_cleanup"] = "V8_DIRECT_OUTPUT"

    p.write_text(_json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    return True


def _pf_v767_v8_postprocess_outputs():
    try:
        from pathlib import Path as _Path

        root = _Path.cwd()
        paths = list((root / "output" / "dashboard_surface").glob("*/reality_board_state.json"))
        for path in paths:
            _pf_v767_v8_clean_state_file(path)
    except Exception as exc:
        print("[WARN] V7.6.7 direct output cleanup failed:", exc)


try:
    import atexit as _pf_v767_v8_atexit

    _pf_v767_v8_atexit.register(_pf_v767_v8_postprocess_outputs)
except Exception as exc:
    print("[WARN] V7.6.7 atexit cleanup registration failed:", exc)

# PF_V767_DIRECT_OUTPUT_CLEANUP_V8_END

import argparse,json
from pathlib import Path
from datetime import datetime,timezone
FORBIDDEN={"BUY","SELL","ENTRY","EXIT","STOP","TARGET"}

def rj(p):
    try:
        p=Path(p)
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    except Exception: return {}
def first(root,paths):
    for x in paths:
        d=rj(root/x)
        if d: return d,x
    return {},None
def pick(*xs,default=""):
    for x in xs:
        if x not in (None,"",[],{}): return x
    return default
def lab(labels,bucket,key):
    sec=labels.get(bucket,{})
    return sec.get(key,key.replace("_"," ").lower()) if isinstance(sec,dict) else key

def requali(t):
    film=str(pick(t.get("film_state"),default="UNKNOWN")); last=str(pick(t.get("last_structural_event"),default="UNKNOWN")); raw=str(pick(t.get("raw_bias"),t.get("bias"),default="UNKNOWN")); q=str(pick(t.get("qualified_bias"),default="")); price=str(pick(t.get("price_confirmation"),default="PENDING"))
    if q: return q,q,"Requalification lue depuis terrain_packet V7.6."
    if raw=="PAIR_UP" and ("LOWER_LOCK" in last or "RELEASE_DOWN" in last): return "COUNTER_BREATH_UP","COUNTER_BREATH_UP","PAIR_UP aprÃ¨s release down/lower lock."
    if raw=="PAIR_UP" and "LOWER_LOW" in last: return "POST_LOW_REACTION","POST_LOW_REACTION","PAIR_UP aprÃ¨s lower low."
    if raw=="PAIR_UP" and ("HIGH_ZONE" in film or "HIGH" in last): return "HIGH_ZONE_EXHAUSTION_RISK","HIGH_ZONE_EXHAUSTION_RISK","PAIR_UP tardif aprÃ¨s high."
    if raw=="PAIR_DOWN" and ("HIGH_ZONE_REJECTION" in film or "HIGH_ZONE_REJECTION" in last): return "POST_HIGH_UNWIND","POST_HIGH_UNWIND","PAIR_DOWN aprÃ¨s high rejetÃ©."
    if raw=="PAIR_DOWN" and "COUNTER_BREATH_REJECTED" in last: return "SECOND_LEG_DOWN","SECOND_LEG_DOWN","PAIR_DOWN aprÃ¨s counter-breath rejetÃ©."
    if raw=="HOT" and price=="PENDING": return "PRESSURE_PENDING","PRESSURE_PENDING","HOT sans dÃ©placement prix."
    return raw,raw,"Fallback: rÃ´le non requalifiÃ©."

def summ(d):
    if not d: return "non disponible"
    for k in ("summary_fr","summary","state_fr","state","bias","dominant_state"):
        if d.get(k): return str(d[k])
    return "non disponible"
def time_roles(tp,ltf,mtf,htf):
    def one(keys,fb,role,label):
        src={}
        for k in keys:
            if isinstance(tp,dict) and tp.get(k): src=tp[k]; break
        if not src: src=fb or {}
        return {"role":role,"label_fr":label,"state":src.get("state") or src.get("bias") or "UNKNOWN","summary_fr":summ(src)}
    return {"htf":one(["HTF","htf"],htf,"ANALYSE","HTF â€” Analyse"),"mtf":one(["MTF","mtf"],mtf,"PLAN","MTF â€” Plan"),"ltf":one(["LTF","ltf"],ltf,"ACTION","LTF â€” Action")}

def strategies(q,film):
    Q=q.upper(); F=film.upper()
    if "HIGH_ZONE_EXHAUSTION" in Q or "HIGH_ZONE_REJECTION" in F:
        return ("PrioritÃ© lecture rejet haut / unwind. Les poussÃ©es tardives ne sont pas des continuations propres sans rÃ©intÃ©gration.","Alternative : rÃ©intÃ©gration propre au-dessus de la zone haute avec relais LTF â†’ MTF.","Confondre extension tardive avec continuation saine.")
    if "COUNTER_BREATH" in Q:
        return ("Lecture counter-breath : rÃ©action contre le film dominant, Ã  qualifier par absorption ou rÃ©intÃ©gration.","Alternative : la rÃ©action devient rÃ©intÃ©gration si le prix accepte et relaie.","Confondre counter-breath et nouvelle release.")
    if "SECOND_LEG" in Q or "UNWIND" in Q:
        return ("Unwind actif : surveiller relance du mouvement aprÃ¨s respiration absorbÃ©e.","Alternative : essoufflement du unwind si le prix rÃ©intÃ¨gre la zone prÃ©cÃ©dente.","Lire chaque rebond comme retournement au lieu de respiration.")
    return ("Lecture partielle : stratÃ©gie de surveillance, pas de conclusion dure.","Alternative ouverte tant que prix, propagation et mÃ©moire ne convergent pas.","SurinterprÃ©ter un signal brut sans rÃ´le dans le film.")

def build_state(root:Path,symbol="GBPUSD"):
    labels,_=first(root,["schema/reality_board_labels_fr_v767.json"])
    terrain,ts=first(root,[f"output/dashboard_surface/{symbol}/terrain_packet.json",f"Core/output/dashboard_surface/{symbol}/terrain_packet.json"])
    mem,ms=first(root,[f"output/dashboard_surface/{symbol}/film_memory_match.json",f"Core/output/dashboard_surface/{symbol}/film_memory_match.json"])
    ltf,ls=first(root,[f"output/dashboard_surface/{symbol}/ltf_session_memory.json",f"Core/output/dashboard_surface/{symbol}/ltf_session_memory.json"])
    mtf,mis=first(root,[f"output/dashboard_surface/{symbol}/mtf_session_memory.json",f"Core/output/dashboard_surface/{symbol}/mtf_session_memory.json"])
    htf,hs=first(root,[f"output/dashboard_surface/{symbol}/htf_session_memory.json",f"Core/output/dashboard_surface/{symbol}/htf_session_memory.json"])
    tp,tps=first(root,["output/dashboard_surface/time_profiles_dashboard.json","Core/output/dashboard_surface/time_profiles_dashboard.json"])
    flags=[]; risks=[]
    if not terrain: flags.append("INPUT_MISSING_TERRAIN_PACKET"); risks.append("terrain_packet introuvable")
    if not mem: flags.append("INPUT_MISSING_B6_MEMORY"); risks.append("film_memory_match introuvable")
    if not (ltf or mtf or htf): flags.append("SESSION_MEMORY_MISSING"); risks.append("session memory introuvable dans output et Core/output")
    if not tp: flags.append("TIME_PROFILES_MISSING")
    film=str(pick(terrain.get("film_state"),mem.get("input_features",{}).get("film_state"),default="READING_PARTIAL")); q,role,reason=requali(terrain)
    data=str(pick(terrain.get("data_visibility"),mem.get("input_features",{}).get("data_visibility"),default="FULL_STACK_VISIBLE"))
    if flags or data!="FULL_STACK_VISIBLE": data="READING_PARTIAL"; flags.append("READING_PARTIAL") if "READING_PARTIAL" not in flags else None
    dom,alt,trp=strategies(q,film)
    session_state="SESSION_MEMORY_AVAILABLE" if (ltf or mtf or htf) else "SESSION_MEMORY_MISSING"
    session_align="ALIGNED_OR_PARTIAL" if session_state=="SESSION_MEMORY_AVAILABLE" else "UNKNOWN"
    b6=pick(mem.get("memory_match"),default="UNKNOWN"); conf=pick(mem.get("memory_confidence_bucket"),default="UNKNOWN")
    labels_fr={"film_state_fr":lab(labels,"film_state",film),"move_role_fr":lab(labels,"current_move_role",role),"data_visibility_fr":lab(labels,"data_visibility",data),"price_read_fr":lab(labels,"price_confirmation",str(pick(terrain.get("price_confirmation"),default="PENDING"))),"footer":labels.get("footer","PowerFlow Ã©claire le terrain. Le trader arbitre.")}
    tel=f"{symbol} â€” Reality Board\n\nLecture : {dom}\nB6 : {b6}\nSession : {session_align}\nAlternative : {alt}\nPiÃ¨ge : {trp}\nData : {labels_fr['data_visibility_fr']}\nRappel : stratÃ©gie de lecture, dÃ©cision trader."
    state={"symbol":symbol,"timestamp":datetime.now(timezone.utc).isoformat(),"session":str(pick(terrain.get("session"),default="UNKNOWN")),"board_version":"V7.6.7","reading_status":"READING_PARTIAL" if data!="FULL_STACK_VISIBLE" else "TACTICAL_OK","film_state":film,"film_sequence":pick(terrain.get("film_sequence"),b6,default="UNKNOWN"),"last_structural_event":str(pick(terrain.get("last_structural_event"),default="UNKNOWN")),"last_structural_direction":str(pick(terrain.get("last_structural_direction"),default="UNKNOWN")),"last_structural_time":str(pick(terrain.get("last_structural_time"),terrain.get("event_time"),default="UNKNOWN")),"current_zone":pick(terrain.get("current_zone"),terrain.get("zone"),default="UNKNOWN"),"current_move_role":role,"raw_packet":str(pick(terrain.get("raw_packet"),terrain.get("packet_type"),terrain.get("raw_bias"),default="UNKNOWN")),"raw_bias":str(pick(terrain.get("raw_bias"),default="UNKNOWN")),"qualified_bias":q,"packet_quality":str(pick(terrain.get("packet_quality"),q,default="READING_PARTIAL")),"packet_maturity":str(pick(terrain.get("packet_maturity"),default="UNKNOWN")),"price_confirmation":str(pick(terrain.get("price_confirmation"),default="PENDING")),"reason_short":reason,"propagation_state":str(pick(terrain.get("propagation_state"),default="LTF_ONLY")),"propagation_detail":str(pick(terrain.get("propagation_detail"),default="UNKNOWN")),"detachment_texture":str(pick(terrain.get("detachment_texture"),default="NOISY_DETACHMENT")),"relay_quality":str(pick(terrain.get("relay_quality"),default="UNKNOWN")),"capture_quality":str(pick(terrain.get("capture_quality"),default="UNKNOWN")),"data_visibility":data,"data_flags":sorted(set(flags)),"technical_risks":sorted(set(risks + (terrain.get("technical_risks") if isinstance(terrain.get("technical_risks"),list) else []))),"b6_nearest_film":b6,"b6_similarity_reason":str(pick(mem.get("memory_reason_fr"),default="")),"b6_learned_rule":str(pick((mem.get("similar_historical_days") or [{}])[0].get("rule_fr") if isinstance(mem.get("similar_historical_days"),list) else "",default="")),"b6_confidence_label":str(conf),"session_memory_state":session_state,"session_alignment":session_align,"session_conflict":"","main_conflict":"","dominant_strategy":{"type":"DOMINANT_READING","label_fr":dom},"alternative_strategy":{"type":"ALTERNATIVE_READING","label_fr":alt},"trap":{"type":"TRAP","label_fr":trp},"watch_condition":"Surveiller acceptation, rejet ou relais selon le film actif.","confirmation_condition":"Prix + propagation + texture alignÃ©s.","invalidation_condition":"Prix invalide le packet ou data devient stale.","labels_fr":labels_fr,"telegram_candidate":{"mode":"candidate_only","send_enabled":False,"text_fr":tel},"time_profile_roles":time_roles(tp,ltf,mtf,htf),"input_sources":{"terrain_packet":ts,"film_memory_match":ms,"ltf_session_memory":ls,"mtf_session_memory":mis,"htf_session_memory":hs,"time_profiles":tps}}
    blob=json.dumps(state,ensure_ascii=False).upper(); leaks=[x for x in FORBIDDEN if x in blob]
    if leaks: raise RuntimeError(f"Forbidden trade terms leaked: {leaks}")
    return state

def write_state(root:Path,symbol="GBPUSD"):
    st=build_state(root,symbol); out=root/"output"/"dashboard_surface"/symbol/"reality_board_state.json"; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(st,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--symbol",default="GBPUSD"); ap.add_argument("--root",default="."); a=ap.parse_args(); out=write_state(Path(a.root).resolve(),a.symbol); print(f"[OK] reality board written: {out}")
if __name__=="__main__": main()

# PF_V767_SEMANTIC_DISPLAY_CLEANUP_V4
# Output-level semantic cleanup for Reality Board display.
# Does not change packet detection logic.

import ast as _pf_v767_ast
from typing import Any as _PFV767Any, Dict as _PFV767Dict

def _pf_v767_scalar(value: _PFV767Any) -> str:
    if value in (None, "", [], {}):
        return ""
    if isinstance(value, (dict, list, tuple, set)):
        return ""
    return str(value)

def _pf_v767_parse_dict_like(value: _PFV767Any) -> _PFV767Dict[str, _PFV767Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        raw = value.strip()
        if raw.startswith("{") and raw.endswith("}"):
            try:
                parsed = _pf_v767_ast.literal_eval(raw)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                return {}
    return {}

def _pf_v767_enum_fr(value: _PFV767Any) -> str:
    raw = _pf_v767_scalar(value)
    if not raw:
        return ""
    mapping = {
        "ABSORPTION_OR_REJECTION": "absorption / rejet",
        "RELEASE_ACTIVE": "release active",
        "HIGH_ZONE_REJECTION": "rejet zone haute",
        "HIGH_ZONE_EXHAUSTION_RISK": "risque epuisement zone haute",
        "PAIR_UP": "pression UP",
        "PAIR_DOWN": "pression DOWN",
        "UNKNOWN": "inconnu",
        "LOW": "faible",
        "MEDIUM": "moyen",
        "HIGH": "fort",
        "PARTIAL_STALE": "partiel / stale",
        "READING_PARTIAL": "lecture partielle",
    }
    return mapping.get(raw, raw.replace("_", " ").lower())

def _pf_v767_short_time(value: _PFV767Any) -> str:
    raw = _pf_v767_scalar(value)
    if not raw:
        return ""
    if "T" in raw:
        try:
            return raw.split("T", 1)[1][:5]
        except Exception:
            return raw
    return raw

def _pf_v767_compact_profile(value: _PFV767Any, fallback_label: str) -> str:
    src = _pf_v767_parse_dict_like(value)
    if not src:
        s = _pf_v767_scalar(value)
        if not s:
            return "non disponible"
        if "events_total" in s or "{" in s:
            return "profil actif, detail brut masque"
        return s[:220]

    tf = _pf_v767_scalar(src.get("timeframe") or src.get("tf") or src.get("profile") or src.get("layer"))
    event = _pf_v767_enum_fr(src.get("event_type") or src.get("event") or src.get("last_event"))
    phase = _pf_v767_enum_fr(src.get("phase_after") or src.get("phase") or src.get("state") or src.get("profile_state"))
    bias = _pf_v767_enum_fr(src.get("bias") or src.get("dominant_bias"))
    fake = _pf_v767_enum_fr(src.get("fake_risk") or src.get("risk") or src.get("fake_risk_level"))
    price = _pf_v767_scalar(src.get("price"))
    ts = _pf_v767_short_time(src.get("timestamp_utc") or src.get("last_event_time") or src.get("updated_at"))

    parts = []
    head = " ".join(x for x in [tf, event or phase] if x).strip()
    if head:
        parts.append(head)
    if bias:
        parts.append("biais " + bias)
    if fake:
        parts.append("fake " + fake)
    if price:
        parts.append("prix " + price)
    if ts:
        parts.append("temps " + ts)

    return " | ".join(parts[:5]) if parts else (fallback_label + " non disponible")

def _pf_v767_strip_prefix(text: str, prefixes: tuple[str, ...]) -> str:
    out = str(text or "").strip()
    for prefix in prefixes:
        if out.lower().startswith(prefix.lower()):
            return out[len(prefix):].strip()
    return out

def _pf_v767_clean_text(text: str) -> str:
    out = str(text or "")
    replacements = {
        "GBPUSD â€œâ€ Reality Board": "GBPUSD - Reality Board",
        "GBPUSD â€â€ Reality Board": "GBPUSD - Reality Board",
        "GBPUSD â€” Reality Board": "GBPUSD - Reality Board",
        "GBPUSD Ã”Ã‡Ã¶ Reality Board": "GBPUSD - Reality Board",
        "Alternative : Alternative :": "Alternative :",
        "PiÃ¨ge : PiÃ¨ge :": "PiÃ¨ge :",
        "Piege : Piege :": "Piege :",
    }
    for old, new in replacements.items():
        out = out.replace(old, new)
    return out

_pf_v767_original_build_state = build_state

def build_state(root, symbol):
    state = _pf_v767_original_build_state(root, symbol)

    roles = state.get("time_profile_roles")
    if isinstance(roles, dict):
        labels = {
            "htf": "HTF - Analyse",
            "mtf": "MTF - Plan",
            "ltf": "LTF - Action",
        }
        for key, label in labels.items():
            item = roles.get(key)
            if isinstance(item, dict):
                raw_summary = item.get("summary_fr") or item.get("summary") or item
                item["label_fr"] = label
                item["summary_fr"] = _pf_v767_compact_profile(raw_summary, label)
                item["state"] = _pf_v767_scalar(item.get("state")) or "ACTIVE"
                roles[key] = item

    telegram = state.get("telegram_candidate")
    if isinstance(telegram, dict):
        text = _pf_v767_clean_text(telegram.get("text_fr", ""))
        text = text.replace("Alternative : Alternative :", "Alternative :")
        telegram["text_fr"] = text
        state["telegram_candidate"] = telegram

    alt = state.get("alternative")
    if isinstance(alt, dict) and isinstance(alt.get("label_fr"), str):
        alt["label_fr"] = _pf_v767_strip_prefix(alt["label_fr"], ("Alternative :", "Alternative:"))

    trap = state.get("trap")
    if isinstance(trap, dict) and isinstance(trap.get("label_fr"), str):
        trap["label_fr"] = _pf_v767_strip_prefix(trap["label_fr"], ("PiÃ¨ge :", "Piege :", "PiÃ¨ge:", "Piege:"))

    return state

