# PATCH LEXIQUE — Session Agentic Core / Dashboard V06 / Telegram Nodes

**Date :** 2026-05-04  
**Statut :** À intégrer au lexique officiel PowerFlow V6

---

## TELEGRAM_AGENTIC_NODE_WATCH

Définition :

```text
Alerte Telegram issue du JSON agentic, envoyée lorsqu’un node ou une fenêtre active est détectée par les agents runtime.
```

Règles :

```text
ne lit pas la DB
ne calcule pas
n’écrit rien
ne produit pas BUY/SELL
transmet seulement WATCH / IMPORTANT / HOT
```

---

## TELEGRAM_NODE_HOT

Définition :

```text
Niveau d’alerte Telegram lorsque la scène, la fractalité, le next_watch et la microstructure sont simultanément actifs.
```

Exemple :

```text
RAW_NODE_BIRTH
+ LTF_BIRTH_INSIDE_VISUAL_HTF_STORY
+ WATCH_M5_CONFIRMATION
+ MICRO_WINDOW_ACTIVE_WEAK/STRONG
```

---

## MICRO_WINDOW_ACTIVE_WEAK

Définition :

```text
Micro-window détectée avec naissance M1/M5 et price lag ou pression partielle,
mais sans confirmation forte volume/pips.
```

Usage :

```text
DB jeune
premier node détecté
surveillance confirmation M5
```

---

## MICRO_WINDOW_ACTIVE_STRONG

Définition :

```text
Micro-window détectée avec naissance M1/M5, price lag, et confirmation de pression par volume ou expansion pips.
```

Usage :

```text
node plus mature
microstructure plus forte
alerte Telegram HOT plus robuste
```

---

## DB_VISUAL_FRACTAL_GAP

Définition :

```text
Écart assumé entre une DB HTF silencieuse/jeune et une histoire HTF confirmée visuellement par screens.
```

Lecture :

```text
DB_HTF_SILENT_OR_FLAT
≠
absence d’histoire HTF
```

---

## LTF_BIRTH_INSIDE_VISUAL_HTF_STORY

Définition :

```text
Naissance LTF détectée dans une histoire HTF confirmée visuellement mais pas encore confirmée par la DB HTF.
```

Rôle :

```text
permettre à PowerFlow de lire une structure fractale malgré une DB jeune.
```

---

## DASHBOARD_AGENTIC_FOCUS_MODE

Définition :

```text
Mode dashboard qui masque ou repousse les éléments secondaires pour donner la priorité à la lecture Agentic Core.
```

---

## AGENTIC_STICKY_SCENE_BAR

Définition :

```text
Barre sticky en haut du dashboard qui garde visible la scène active et le next_watch.
```

---

## EXTENDED_MICROSTRUCTURE_LAYER

Définition :

```text
Couche issue de force_snapshots_v2 qui ajoute tick_volume, pips, spread, OHLC et NZD au film agentic.
```

---

Fin patch lexique.
