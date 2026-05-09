from pf_zone_dynamics_v022_context_tags import analyze_zone_dynamics

series = [-1.2, -1.46, -1.63, -1.80, -1.92]
diag = analyze_zone_dynamics(series, timeframe=5, currency="GBP", session_phase="PRE_US")
data = diag.to_dict()

assert "contextual_tags" in data
assert "context_tags" in data
assert data["context_tags"] == data["contextual_tags"]
assert data["state"] in ("PRE_EXTREME", "ACCUMULATING", "LEAKING", "RUPTURE", "DISORDER_FIELD", "NEUTRAL")

print("OK alias context_tags:", data["context_tags"])
print("state:", data["state"])
print("zone_level:", data["zone_level"])
print("context_score:", data["context_score"])
