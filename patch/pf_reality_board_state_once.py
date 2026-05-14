#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations
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
