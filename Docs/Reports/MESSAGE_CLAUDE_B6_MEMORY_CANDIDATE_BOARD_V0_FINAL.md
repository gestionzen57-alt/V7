# MESSAGE CLAUDE / ARCHITECTE - B6 Memory Candidate Board V0

B6 Memory Candidate Board V0 est produit depuis les ZIPs uploades, sans lecture directe des chemins Windows.

Doctrine respectee :

```text
B9 ne cherche pas le signal.
B9 cherche la trace laissee par l'effort.
B6 ne predit pas.
B6 compare des films.
```

Outputs :

```text
B6_MEMORY_CANDIDATE_BOARD_V0.md
B6_MEMORY_CANDIDATE_BOARD_V0.csv
B6_MEMORY_CANDIDATE_KEEP.csv
B6_MEMORY_CANDIDATE_REVIEW.csv
B6_MEMORY_CANDIDATE_LOW_TRUST.csv
B6_MEMORY_REJECTED_RAW_UNAVAILABLE.csv
B6_MEMORY_CANDIDATE_BOARD_V0.zip
```

Counts :

```text
total=174
KEEP=138
REVIEW=13
LOW_TRUST=2
REJECTED_RAW_UNAVAILABLE=21
```

Sources :

```text
source_family={'FORCE_SNAPSHOT_DERIVED': 122, 'RECOVERED_EXISTING_B9_SUMMARY': 52}
proxy_vs_raw_verdict={'NUANCED_BY_RAW': 113, 'RAW_UNAVAILABLE': 21, 'CONFIRMED_BY_RAW': 40}
```

Notes techniques :

```text
- FORCE_SNAPSHOT_DERIVED reste separe de RECOVERED_EXISTING_B9_SUMMARY.
- RAW_UNAVAILABLE est exclu de la memoire active.
- LOW_TRUST est conserve pour audit dans un CSV separe.
- NUANCED_BY_RAW n'est jamais presente comme CONFIRMED_BY_RAW.
- Aucun powerflow.db/tick_archive.db write, aucun dashboard, aucun Telegram.
```
