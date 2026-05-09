import sqlite3
import os

DB_PATH = "powerflow.db"  
SYMBOL = "GBPUSD"         
TIMEFRAME = 1            
LOOKBACK = 14200            

try:
    from pf_personalities import behavioral_index, behavioral_state, DEVISE_PROFILES
    from pf_zone_dynamics import analyze_zone_dynamics
except ImportError as e:
    print(f"ERREUR D'IMPORT: {e}")
    print(f"ERREUR D'IMPORT: {e}")
    exit(1)

def main():
    if not os.path.exists(DB_PATH):
        print(f"ERREUR: La base de données {DB_PATH} n'existe pas.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Recherche automatique de la colonne de temps
    cursor.execute("PRAGMA table_info(force_snapshots)")
    columns = [col[1] for col in cursor.fetchall()]
    
    time_col = "timestamp"
    if "time" in columns: time_col = "time"
    elif "bar_time" in columns: time_col = "bar_time"
    elif "created_at" in columns: time_col = "created_at"
    
    if time_col not in columns:
        print(f"ERREUR: Impossible de trouver une colonne de temps. Colonnes dispo: {columns}")
        return
    
    devise_cols = []
    for devise in DEVISE_PROFILES.keys():
        col_name = f"force_{devise.lower()}"
        if col_name in columns:
            devise_cols.append((devise.lower(), col_name))
    
    if not devise_cols:
        return
        
    print(f"Devises détectées: {[d[0].upper() for d in devise_cols]}")
    print(f"Colonne de temps utilisée: {time_col}")
    
    cols_sql = ", ".join([d[1] for d in devise_cols])
    query = f"""
        SELECT {time_col}, {cols_sql}
        FROM force_snapshots
        WHERE symbol = ? AND timeframe = ?
        ORDER BY {time_col} DESC
        LIMIT ?
    """
    
    cursor.execute(query, (SYMBOL, TIMEFRAME, LOOKBACK + 30)) 
    results = cursor.fetchall()
    
    if not results:
        print(f"Aucune donnée trouvée pour {SYMBOL} M{TIMEFRAME}.")
        return
        
    results.reverse()
    
    print(f"\nAnalyse de {len(results)} barres historiques sur {SYMBOL} M{TIMEFRAME}...")
    
    target_devises = ["EUR", "JPY", "GBP"]
    
    for devise in target_devises:
        if devise.lower() not in [d[0] for d in devise_cols]:
            continue
            
        print(f"\n>>> ANALYSE DE LA DYNAMIQUE : {devise} <<<")
        print("-" * 80)
        
        z_series = []
        timestamps = []
        
        start_idx = 20
        for i in range(start_idx, len(results)):
            z = behavioral_index(devise, results, i, devise_cols, lookback=20)
            z_series.append(z)
            timestamps.append(results[i][0])
            
        diag = analyze_zone_dynamics(z_series)
        
        print(f"État actuel         : {diag.state}")
        print(f"Z-score courant     : {diag.z_current:+.3f} ({behavioral_state(diag.z_current)})")
        print(f"Barres en extrême   : {diag.bars_in_extreme} ({diag.z_extreme_dir})")
        print(f"Tension accumulée   : {diag.tension_score:.3f}")
        print(f"Note diagnostique   : {diag.note}")
                
    conn.close()

if __name__ == "__main__":
    main()
