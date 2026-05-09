"""PowerFlow V6 - pf_temporal_nodes.py - MODULE A"""
import sqlite3,json
from datetime import datetime,timedelta,timezone
from dataclasses import dataclass,field
from typing import List,Dict,Optional

TF_WINDOWS={1:20,5:40,15:90,30:180,60:300,240:720,1440:1440}
TF_LABELS={1:"M1",5:"M5",15:"M15",30:"M30",60:"H1",240:"H4",1440:"D1",10080:"W1"}
SIGNAL_WEIGHTS={"COMPRESSION":1,"COMPRESSION_BREAK":2,"CONVERGENCE":5,"CROSS":2,"KISS_REJECT":3,"COMPRESSION_SQUEEZE":3,"SLINGSHOT":2,"REPULSION":4}
NODE_INTEREST={"NODE_COMPLET_FULL":"SIGNAL_VALIDATED","NODE_COMPLET":"TACTICAL_READY","NODE_REPULSION":"TACTICAL_READY","NODE_CROSS":"STRUCTURE_BUILDING","NODE_SIMPLE":"WATCH_ZONE"}
DEDUP_GAP_SECONDS=600

@dataclass
class RawSignal:
    created_at:str;symbol:str;timeframe:int;signal_type:str;score:int
    timestamp:datetime=field(init=False)
    def __post_init__(self):
        try:self.timestamp=datetime.fromisoformat(self.created_at.replace("Z","+00:00"))
        except:self.timestamp=datetime.now(timezone.utc)

@dataclass
class TemporalNode:
    node_id:str;symbol:str;timeframe:int;tf_label:str;node_type:str
    interest:str;score:int;window_start:datetime;window_end:datetime
    duration_minutes:float;has_convergence:bool=False;has_cross:bool=False
    has_kiss_reject:bool=False;has_squeeze:bool=False;has_slingshot:bool=False
    has_repulsion:bool=False;energy:int=0
    raw_signals:List[RawSignal]=field(default_factory=list)
    description:str="";action:str="";cockpit_tag:str=""
    def to_dict(self):
        return {"id":self.node_id,"type":self.node_type,"interest":self.interest,"score":self.score,"energy":self.energy,
                "duration_min":round(self.duration_minutes,1),"tf":self.tf_label,
                "window":f"{self.window_start.strftime('%H:%M')}->{self.window_end.strftime('%H:%M')}",
                "has_convergence":self.has_convergence,"has_cross":self.has_cross,"has_kiss_reject":self.has_kiss_reject,
                "has_repulsion":self.has_repulsion,"description":self.description,"action":self.action,"cockpit_tag":self.cockpit_tag}

@dataclass
class TemporalNodeResult:
    symbol:str;mode:str;analyzed_at:datetime
    nodes_by_tf:Dict[str,List[TemporalNode]]=field(default_factory=dict)
    fractal_alignment:List[str]=field(default_factory=list)
    summary:Dict=field(default_factory=dict)
    def best_nodes(self):
        result=[]
        for nodes in self.nodes_by_tf.values():
            for n in nodes:
                if n.node_type in("NODE_COMPLET_FULL","NODE_COMPLET","NODE_REPULSION"):result.append(n)
        return sorted(result,key=lambda n:n.score,reverse=True)
    def to_dict(self):
        return {"symbol":self.symbol,"mode":self.mode,"analyzed_at":self.analyzed_at.isoformat(),
                "nodes_by_tf":{tf:[n.to_dict() for n in nodes] for tf,nodes in self.nodes_by_tf.items()},
                "fractal_alignment":self.fractal_alignment,"summary":self.summary}

class TemporalNodeDetector:
    def __init__(self,db_path:str):
        self.db_path=db_path;self.conn=sqlite3.connect(db_path);self.conn.row_factory=sqlite3.Row
    def _get_signals(self,symbol:str,timeframe:int,limit:int=500)->List[RawSignal]:
        cursor=self.conn.cursor()
        cursor.execute("""SELECT created_at,symbol,timeframe,signal_type,score FROM signals
            WHERE symbol=? AND timeframe=? AND signal_type IN
            ('COMPRESSION','COMPRESSION_BREAK','CONVERGENCE','CROSS','KISS_REJECT','COMPRESSION_SQUEEZE','SLINGSHOT','REPULSION')
            ORDER BY created_at DESC LIMIT ?""",(symbol,timeframe,limit))
        signals=[]
        for r in cursor.fetchall():
            try:signals.append(RawSignal(r["created_at"],r["symbol"],r["timeframe"],r["signal_type"],r["score"]))
            except:pass
        return list(reversed(signals))
    def _score_window(self,signals:List[RawSignal])->int:
        seen=set();score=0
        for sig in signals:
            if sig.signal_type not in seen:score+=SIGNAL_WEIGHTS.get(sig.signal_type,1);seen.add(sig.signal_type)
        return min(10,score)
    def _classify(self,hv:bool,hb:bool,hx:bool,hk:bool,hr:bool)->str:
        if hv and hb and hk:return"NODE_COMPLET_FULL"
        if hv and hb:return"NODE_COMPLET"
        if hr and hb:return"NODE_REPULSION"
        if hb and hx:return"NODE_CROSS"
        return"NODE_SIMPLE"
    def _build_description(self,node:TemporalNode)->str:
        parts=[]
        if node.has_convergence:parts.append("CONVERGENCE maximale")
        if node.has_repulsion:parts.append("REPULSION forte")
        if node.has_cross:parts.append("croisement confirmé")
        if node.has_kiss_reject:parts.append("rejet validé")
        if node.has_squeeze:parts.append("squeeze actif")
        if node.has_slingshot:parts.append("énergie fronde")
        suffix=", ".join(parts) if parts else"compression libérée"
        return f"{node.node_type} {node.tf_label} ({node.duration_minutes:.0f}min) -- {suffix}"
    def _build_action(self,node_type:str)->str:
        return {"NODE_COMPLET_FULL":"!! ALERTE -- Surveiller direction de libération",
                "NODE_COMPLET":"WATCH   -- CONVERGENCE active, confirmer direction",
                "NODE_REPULSION":"WATCH   -- REPULSION détectée, énergie forte",
                "NODE_CROSS":"OBSERVE -- Structure confirmée par croisement",
                "NODE_SIMPLE":"FILTER  -- Attendre confirmation multi-TF"}.get(node_type,"OBSERVE")
    def _build_cockpit_tag(self,node:TemporalNode)->str:
        icon={"NODE_COMPLET_FULL":"⚡⚡","NODE_COMPLET":"⚡","NODE_REPULSION":"↔","NODE_CROSS":"✕","NODE_SIMPLE":"·"}.get(node.node_type,"·")
        t=node.window_start.strftime("%H:%M")
        return f"{icon} {t} {node.tf_label} {node.node_type} {node.score}/10"
    def detect_nodes(self,symbol:str,timeframe:int,mode:str="live")->List[TemporalNode]:
        signals=self._get_signals(symbol,timeframe)
        if len(signals)<2:return[]
        win_min=TF_WINDOWS.get(timeframe,20);window=timedelta(minutes=win_min);tf_label=TF_LABELS.get(timeframe,f"TF{timeframe}")
        if mode=="live":
            now=signals[-1].timestamp;start_from=now-window
            compressions=[s for s in signals if s.signal_type=="COMPRESSION" and s.timestamp>=start_from]
        else:
            compressions=[s for s in signals if s.signal_type=="COMPRESSION"]
        nodes=[];seen_keys=set()
        for comp in compressions:
            key=comp.timestamp.strftime("%H%M")
            if key in seen_keys:continue
            seen_keys.add(key)
            win_end=comp.timestamp+window
            win_signals=[s for s in signals if comp.timestamp<=s.timestamp<=win_end]
            if len(win_signals)<2:continue
            types={s.signal_type for s in win_signals}
            hc="COMPRESSION" in types;hv="CONVERGENCE" in types;hb="COMPRESSION_BREAK" in types;hx="CROSS" in types
            hk="KISS_REJECT" in types;hs="COMPRESSION_SQUEEZE" in types;hl="SLINGSHOT" in types;hr="REPULSION" in types
            if not(hc and hb):continue
            score=self._score_window(win_signals);ntype=self._classify(hv,hb,hx,hk,hr)
            t0=min(s.timestamp for s in win_signals);t1=max(s.timestamp for s in win_signals);dur=(t1-t0).total_seconds()/60
            node=TemporalNode(f"NODE_{symbol}_{timeframe}_{comp.timestamp.strftime('%H%M%S')}",symbol,timeframe,tf_label,ntype,
                              NODE_INTEREST.get(ntype,"WATCH_ZONE"),score,t0,t1,dur,hv,hx,hk,hs,hl,hr,len(win_signals),win_signals)
            node.description=self._build_description(node);node.action=self._build_action(ntype);node.cockpit_tag=self._build_cockpit_tag(node)
            nodes.append(node)
        final=[]
        for node in nodes:
            is_dup=any(abs((node.window_start-prev.window_start).total_seconds())<DEDUP_GAP_SECONDS and node.node_type==prev.node_type for prev in final)
            if not is_dup:final.append(node)
        return final
    def analyze(self, symbol:str, timeframes:List[int], mode:str="live") -> TemporalNodeResult:
        interest_rank = {"WATCH_ZONE":1,"STRUCTURE_BUILDING":2,"TACTICAL_READY":3,"SIGNAL_VALIDATED":4}
        
        # ✅ Instanciation propre — summary vide, rempli ensuite
        result = TemporalNodeResult(symbol, mode, datetime.now(timezone.utc))
        result.summary = {
            "total_nodes":0,"NODE_COMPLET_FULL":0,"NODE_COMPLET":0,
            "NODE_REPULSION":0,"NODE_CROSS":0,"NODE_SIMPLE":0,
            "highest_score":0,"has_convergence":False,"has_repulsion":False,
            "best_interest":"WATCH_ZONE","fractal_score":0,"alert_nodes":[]
        }
        active_tfs = []
        for tf in timeframes:
            tf_label=TF_LABELS.get(tf,f"TF{tf}");nodes=self.detect_nodes(symbol,tf,mode)
            if nodes:
                result.nodes_by_tf[tf_label]=nodes;active_tfs.append(tf_label)
                for n in nodes:
                    s=result.summary;s["total_nodes"]+=1;s[n.node_type]=s.get(n.node_type,0)+1
                    s["highest_score"]=max(s["highest_score"],n.score)
                    if n.has_convergence:s["has_convergence"]=True
                    if n.has_repulsion:s["has_repulsion"]=True
                    if interest_rank.get(n.interest,0)>interest_rank.get(s["best_interest"],0):s["best_interest"]=n.interest
                    if n.node_type in("NODE_COMPLET_FULL","NODE_COMPLET","NODE_REPULSION"):s["alert_nodes"].append(n.cockpit_tag)
        n_active=len(active_tfs);result.fractal_alignment=active_tfs
        if n_active == 0:
            result.summary["fractal_score"] = 0
        else:
            quality_score = 0
            for tf_label, nodes in result.nodes_by_tf.items():
                best = max(nodes, key=lambda n: n.score)
                if best.node_type == "NODE_COMPLET_FULL": quality_score += 4
                elif best.node_type in ("NODE_COMPLET", "NODE_REPULSION"): quality_score += 3
                elif best.node_type == "NODE_CROSS":      quality_score += 2
                else:                                      quality_score += 1
            result.summary["fractal_score"] = min(10, quality_score)
        if n_active == 0:
            result.summary["fractal_score"] = 0
        else:
            quality_score = 0
            for tf_label, nodes in result.nodes_by_tf.items():
                best = max(nodes, key=lambda n: n.score)
                if best.node_type == "NODE_COMPLET_FULL": quality_score += 4
                elif best.node_type in ("NODE_COMPLET","NODE_REPULSION"): quality_score += 3
                elif best.node_type == "NODE_CROSS":      quality_score += 2
                else:                                      quality_score += 1
            result.summary["fractal_score"] = min(10, quality_score)
        return result
    def _validate_repulsion(self, signals:List[RawSignal])->bool:
        """Verifier si c'est une REPULSION (divergence continue)."""
        if len(signals)<5:
            return False

        # Placeholder propre: RawSignal ne contient pas encore dev_a/dev_b.
        # Quand les ecarts reels seront disponibles, remplacer cette ligne
        # par: gap = abs(sig.dev_a - sig.dev_b)
        gaps=[0.0 for sig in signals]

        prev_gap=gaps[0]
        gap_trend=0
        for current_gap in gaps[1:]:
            if current_gap>=prev_gap*0.95:
                gap_trend+=1
            else:
                gap_trend-=1
            prev_gap=current_gap

        divergence_ratio=gap_trend/len(gaps)
        if divergence_ratio<0.6:
            return False
        if gaps[-1]<=gaps[0]*1.05:
            return False

        variance=sum(abs(gaps[i]-gaps[i-1]) for i in range(1,len(gaps)))/len(gaps)
        if variance>3.0:
            return False
        return True

    def _score_repulsion(self, signals:List[RawSignal])->int:
        """Scorer la REPULSION (1-10)."""
        if len(signals)<2:
            return 1

        # Placeholder tant que RawSignal ne porte pas encore l'ecart reel.
        gaps=[5.0 for s in signals]
        initial_gap=gaps[0]
        final_gap=gaps[-1]

        if initial_gap>0:
            gap_ratio=final_gap/initial_gap
            score_gap_ratio=min(8,2+(gap_ratio-1.0)*8)
        else:
            score_gap_ratio=4

        variance=sum(abs(gaps[i]-gaps[i-1]) for i in range(1,len(gaps)))/len(gaps)
        score_constance=max(3,10-variance*2)
        duration=len(signals)
        score_duration=min(10,2+duration*0.3)
        score_force=min(10,final_gap*1.2)

        final_score=(
            score_gap_ratio*0.35+
            score_constance*0.25+
            score_duration*0.20+
            score_force*0.20
        )
        return int(min(10,max(1,final_score)))

    def _build_repulsion_description(self,node)->str:
        """Description REPULSION pour cockpit."""
        parts=[f"REPULSION ({node.duration_minutes:.0f}min)"]
        if node.score>=8:
            parts.append("force tres elevee")
        return " -- ".join(parts)

    def close(self):
        if self.conn:self.conn.close()

def get_temporal_nodes_for_engine(db_path:str,symbol:str,timeframes:List[int]=None,mode:str="live")->Dict:
    if timeframes is None:timeframes=[1,5,15,30,60]
    detector=TemporalNodeDetector(db_path);result=detector.analyze(symbol,timeframes,mode);detector.close()
    return result.to_dict()

def _print_result(result:TemporalNodeResult):
    s=result.summary
    print("\n"+"="*85)
    print(f"  TEMPORAL NODE -- {result.symbol}  [{result.mode.upper()}]  {result.analyzed_at.strftime('%H:%M:%S')}")
    print("="*85)
    print(f"\n  SUMMARY")
    print(f"  NODE_COMPLET !!: {s.get('NODE_COMPLET_FULL',0)}  <- CONVERGENCE + KISS (RARE!)")
    print(f"  NODE_COMPLET   : {s.get('NODE_COMPLET',0)}  <- CONVERGENCE active")
    print(f"  NODE_REPULSION : {s.get('NODE_REPULSION',0)}  <- Répulsion forte (D)")
    print(f"  NODE_CROSS     : {s.get('NODE_CROSS',0)}  <- Croisement confirmé")
    print(f"  NODE_SIMPLE    : {s.get('NODE_SIMPLE',0)}  <- Filtrable")
    print(f"  Score max      : {s['highest_score']}")
    print(f"  CONVERGENCE    : {'!!! OUI' if s['has_convergence'] else 'non'}")
    print(f"  REPULSION      : {'!!! OUI' if s['has_repulsion'] else 'non'}")
    print(f"  Best interest  : {s['best_interest']}")
    print(f"  Fractal score  : {s['fractal_score']}/10  TF: {', '.join(result.fractal_alignment) or 'aucun'}")
    if s.get("alert_nodes"):
        print(f"\n  !! ALERTES IMPORTANTES:")
        for tag in s["alert_nodes"]:print(f"     {tag}")
    if result.nodes_by_tf:
        print(f"\n  NODES PAR TIMEFRAME")
        for tf_lbl,nodes in result.nodes_by_tf.items():
            print(f"\n  [{tf_lbl}]")
            for n in nodes:
                flags=""
                if n.has_convergence:flags+=" !! CONV"
                if n.has_repulsion:flags+=" !! REP"
                if n.has_cross:flags+=" CROSS"
                if n.has_kiss_reject:flags+=" KISS"
                print(f"    {n.node_type:20} Score:{n.score:2} | {n.window_start.strftime('%H:%M')}->{n.window_end.strftime('%H:%M')} | {n.duration_minutes:.0f}min{flags}")
                print(f"    -> {n.action}")
    else:print("\n  Aucun node détecté")
    print("\n"+"="*85+"\n")

def main():
    import argparse
    p=argparse.ArgumentParser(description="PowerFlow V6 -- pf_temporal_nodes")
    p.add_argument("symbol");p.add_argument("--db",default="powerflow.db")
    p.add_argument("--timeframes",default="1,5,15,30,60");p.add_argument("--mode",default="live",choices=["live","full"])
    p.add_argument("--json",action="store_true")
    args=p.parse_args()
    tfs=[int(t.strip()) for t in args.timeframes.split(",")]
    detector=TemporalNodeDetector(args.db);result=detector.analyze(args.symbol,tfs,mode=args.mode)
    print(json.dumps(result.to_dict(),indent=2,default=str)) if args.json else _print_result(result)
    detector.close()

if __name__=="__main__":
    main()
