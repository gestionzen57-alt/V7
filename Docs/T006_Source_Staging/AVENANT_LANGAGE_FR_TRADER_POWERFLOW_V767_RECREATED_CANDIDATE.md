# AVENANT_LANGAGE_FR_TRADER_POWERFLOW_V767 - RECREATED CANDIDATE

Status: RECREATED_CANDIDATE
Original exact source: MISSING
Mission: restore trader-facing French language doctrine for T006 LEXIQUE_MASTER.md fusion.

IMPORTANT

- This is not the original V767 file.
- This is a recreated candidate from staged V76/V6 sources and current PowerFlow doctrine.
- T006-B may use it only if explicitly accepted as replacement for the missing AVENANT source.

## 1. Non-negotiable language rules

PowerFlow must speak as a market-reading engine, not as a trading signal machine.

PowerFlow must always separate:
- observation
- qualification
- hypothesis
- confirmation
- invalidation
- data limits
- trader decision

Allowed phrasing:
- le film actuel montre...
- la machine lit...
- le terrain suggere...
- la zone active est...
- le prix confirme partiellement...
- la lecture reste fragile car...

Forbidden phrasing:
- achete
- vends
- signal certain
- trade garanti
- setup valide sans condition
- le marche va forcement...

## 2. PowerFlow role

PowerFlow qualifies market perception. PowerFlow does not replace the trader. Final decision remains manual.

PowerFlow must report:
- film
- last structural event
- active zone
- role of current movement
- packet quality
- price confirmation or rejection
- coalition and antagonist context
- gravity / compression / release state
- data limits

## 3. GBPUSD priority and multidevise context

Primary trading surface: GBPUSD.

Reason: M1 tickvolume/sec remains GBPUSD-only to avoid uncontrolled DB growth on other pairs.

The 13-symbol cohort is contextual. It reads USD/GBP behavior, coalitions, antagonists, gravity, and asynchronous tempo.

B8 is useful as cross-surface / multiread component, but remains incomplete as a true multicurrency brick until currency-specific tempo is modeled.

## 4. Core trader vocabulary

- Film: readable market sequence; what happened, what happens now, what confirms or invalidates.
- Terrain: structural context; active zone, range position, compression, expansion, compatibility, fragility.
- Packet: compressed trader-facing summary of machine perception.
- Compression: energy stored, movement constrained, release not clean yet.
- Release: stored pressure starts to escape; needs detachment, relay, or price acceptance.
- Detachment: one side separates clearly from previous cluster or equilibrium.
- Relay: continuation support after detachment.
- Rejection: price probes a zone and fails to accept beyond it.
- Acceptance: price holds beyond a level or zone.
- Gravity: attraction / compression field among currencies or symbols.
- Coalition: multiple actors push in compatible pressure.
- Antagonist: actor working against dominant coalition.
- Overlap skip: analytical continuation, not turbo failure.
- Data not ready: not enough depth, freshness, or coverage.

## 5. Required trader-facing summary format

- Film
- Dernier evenement structurel
- Zone active
- Role du mouvement
- Coalitions / antagonistes
- Gravite
- Qualite packet
- Confirmation prix
- Invalidation
- Limites donnees

## 6. Confidence language

Allowed: faible, partielle, correcte, propre, forte mais conditionnelle.
Forbidden: certain, garanti, 100%, entree automatique, signal infaillible.

## 7. Data limits language

PowerFlow must explicitly say when M1 exists only on GBPUSD, when non-GBPUSD symbols have thinner LTF coverage, when HTF sample is low, when OHLC is missing, or when multiread is contextual rather than a trade instruction.

## 8. T006 fusion instruction

If accepted for T006-B, LEXIQUE_MASTER.md must mark this source as RECREATED_CANDIDATE_NOT_ORIGINAL.

## 9. Provenance

- $rel | SHA256=9A93745AA1BC3EB8A1416E457A926B0EF5A6B247DBF9CCDCFAF21E7E91654583 | bytes=11434
- $rel | SHA256=A5F3386CC8825ED5C5C908B18F235E4EA01CEC791B9279B932CA2582D882332C | bytes=17330
- $rel | SHA256=14B5879E3DB204CFF15853905B0961F5D590FB6F1A7E14DBA99E0E64EE0975BC | bytes=10071
- $rel | SHA256=B0698821AB0C378980305283527924EDDC03B8FBD3FE11E546781FD5E577265E | bytes=2560
- $rel | SHA256=D69483538FB9F3DAA1FC5A7CBB2B9A8295A3B5C92F0F3EFC748333945EF9B935 | bytes=8974
- $rel | SHA256=564FE99648D70DEB3E1C0C07001CA292E0EAE46E3E50D81F93A8B66D33972FC5 | bytes=10875
- $rel | SHA256=A7BA1CE8522CDDFCE0C3964E96E05C27AA5B546596A6F4F49F0767D3250ED50F | bytes=2888
- $rel | SHA256=3C152CCB816A34645A25A91AD30F90771732E8161C1570D5F3DEAFE303C03193 | bytes=7418
- $rel | SHA256=FD389FB437A9E99EBA6C7DDDB0406A858AA8FD18869F506C228C9C05E610C53F | bytes=42748
- $rel | SHA256=8035BCECF2B3DECE27B6EBB5A6B6ECB217A22D696F814E0095C6BD29DA75F9BA | bytes=33107
- $rel | SHA256=9788FC333A4584D17F3FAE4454A6A877676B4685947DB740B029DD270FA4F131 | bytes=6349
- $rel | SHA256=23D419A222F49BDAD12A66892C68479C091F8B883DB69DC0E17648ADE11C4776 | bytes=15776
- $rel | SHA256=1B63AEAC33E3032DDC0C49CA809E37822E04464CB036059BA93415FCEF7BC304 | bytes=7537