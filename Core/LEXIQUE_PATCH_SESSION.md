# LEXIQUE PATCH SESSION - PowerFlow V7.2.1

**Patch :** Session Overlay V2 + Dashboard Dual Display
**Date :** 2026-05-11
**Statut :** A commiter dans Git

## Termes a integrer

### SESSION_CONTEXT
Contexte temporel injecte dans chaque alerte comportementale. Il qualifie l'environnement horaire du flux sans filtrer l'alerte.

Champs :
- session
- session_phase
- minutes_since_open
- session_bias
- timestamp_utc
- method
- status
- technical_risks

### SESSION
Session UTC active du flux.

Valeurs :
- ASIAN
- LONDON
- NY
- OVERLAP
- DEAD_ZONE

### ASIAN
Session 22:00-08:00 UTC. Flux souvent plus lent, compression progressive, respiration range.

### LONDON
Session 07:00-16:00 UTC. Fenetre d'ignition et premiere acceleration.

### NY
Session 12:00-21:00 UTC. Fenetre de confirmation, continuation ou contre-respiration.

### OVERLAP
Fenetre 12:00-16:00 UTC. Superposition London / NY. Bataille de velocite maximale.

### DEAD_ZONE
Fenetre 20:00-22:00 UTC. Zone de faible lisibilite temporelle. Etat de session, pas une panne.

### SESSION_PHASE
Phase interne de la session.

Valeurs :
- IGNITION
- MID_SESSION
- CLOSING

### IGNITION
Premiers 45 minutes d'une session. Moment ou les detachments et impulsions apparaissent souvent.

### MID_SESSION
Coeur de session. Lecture plus structuree, moins liee a l'ouverture brute.

### CLOSING
Derniers 45 minutes d'une session. Friction de cloture et repositionnements.

### SESSION_BIAS
Biais comportemental de session. Ce n'est pas une direction de trade.

Valeurs :
- EXPANSION_EXPECTED
- MAX_VELOCITY_BATTLEFIELD
- COMPRESSION_EXPECTED
- DEAD_ZONE
- ROTATION_EXPECTED

### EXPANSION_EXPECTED
Biais de London/NY ignition. Le flux peut s'etendre rapidement.

### MAX_VELOCITY_BATTLEFIELD
Biais de l'overlap London/NY. Zone de bataille multi-participants.

### COMPRESSION_EXPECTED
Biais typique de l'Asian mid-session. Compression et respiration plus lente.

### ROTATION_EXPECTED
Biais neutre de rotation intraday.

### MINUTES_SINCE_OPEN
Minutes ecoulees depuis l'ouverture de la session active.

### LONDON_IGNITION
Combinaison session=LONDON et session_phase=IGNITION.

### NY_IGNITION
Combinaison session=NY et session_phase=IGNITION.

### ASIAN_TO_LONDON_HANDOVER
Transition entre fin Asian et debut London.

### LONDON_CLOSING_FRICTION
Phase de cloture London. Risque technique de friction temporelle.

### FRESHNESS
Etat de fraicheur d'un bloc dashboard.

Valeurs :
- FRESH
- AGING
- STALE
- MISSING

### FRESH
Donnee age < 300 secondes.

### AGING
Donnee 300 <= age < 600 secondes.

### STALE
Donnee age >= 600 secondes. Bloc rouge / grise.

### MISSING
Donnee absente, vide ou non parseable. Le dashboard doit afficher MISSING DATA.

### DATA_BRICK
Attribut HTML tracant la brique source. Exemple : data-brick="session".

### DATA_METHOD
Attribut HTML tracant la methode. Exemple : data-method="B1_HMM".

### DATA_SYMBOL
Attribut HTML tracant le symbole affiche. Exemple : data-symbol="GBPUSD".

### DUAL_DISPLAY
Affichage cote a cote de deux methodes duales. Jamais de fusion, jamais de moyenne.

### REGIME_DUAL_DISPLAY
Affichage cote a cote B1 Legacy et B1+ HMM.

### DENSITY_DUAL_DISPLAY
Affichage cote a cote B4 Rolling et B4+ Wavelet.

### STALE_DISPLAY_GUARD
Garde visuel dashboard rendant les donnees stale visibles.

### MISSING_DATA_STATE
Etat explicite lorsque le JSON attendu est absent ou vide.

### TIMESTAMP_UTC_VISIBLE
Regle dashboard : chaque bloc doit rendre visible timestamp UTC.

### AGE_SECONDS
Age en secondes depuis le timestamp du bloc.

### FRESHNESS_COLOR
Couleur associee a freshness : vert / orange / rouge.

### SESSION_OVERLAY_V2_UTC
Methode du moteur Session Overlay V2.

### SESSION_CONTEXT_IMPORT_FAILED
Risque technique si le mapper ne peut pas importer pf_session_overlay.

### SESSION_CONTEXT_INJECTION
Action du mapper consistant a ajouter session_context a chaque alerte.

### DASHBOARD_SESSION_CARD
Carte dashboard dediee a la session active.

### MAX_VELOCITY_WINDOW
Synonyme comportemental de l'overlap London/NY.

## Regle doctrinale

Session context qualifie. Session context ne filtre pas. Session context ne decide pas. Le trader arbitre.

