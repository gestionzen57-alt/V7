import numpy as np

def detect_pullbacks(series, extreme_threshold=0.9):
    pullbacks = []
    in_extreme = False
    start_idx = None
    extreme_value = None

    for i in range(1, len(series)):
        val = series[i]

        # entrée en extrême
        if not in_extreme and abs(val) >= extreme_threshold:
            in_extreme = True
            start_idx = i
            extreme_value = val

        # sortie de l'extrême = pullback
        elif in_extreme and abs(val) < extreme_threshold:
            depth = abs(extreme_value - val)
            duration = i - start_idx

            pullbacks.append({
                "depth": depth,
                "duration": duration,
                "return_speed": depth / duration if duration > 0 else 0
            })

            in_extreme = False

    return pullbacks


def compute_depth_drift(pullbacks):
    if len(pullbacks) < 2:
        return 0

    depths = [p["depth"] for p in pullbacks]
    return np.mean(np.diff(depths))


def compute_return_efficiency(pullbacks):
    if not pullbacks:
        return 0
    return np.mean([p["return_speed"] for p in pullbacks])


def compute_scores(pullbacks):
    if len(pullbacks) < 2:
        return {
            "depth_drift": 0,
            "mean_duration": 0,
            "return_efficiency": 0,
            "breathing_score": 0,
            "invalidation_pressure": 0
        }

    depth_drift = compute_depth_drift(pullbacks)
    mean_duration = np.mean([p["duration"] for p in pullbacks])
    return_efficiency = compute_return_efficiency(pullbacks)

    # score respiration (simple V0)
    breathing_score = (
        (1 - min(depth_drift, 1)) * 0.4 +
        (1 / (1 + mean_duration)) * 0.3 +
        min(return_efficiency, 1) * 0.3
    )

    # pression invalidation
    invalidation_pressure = max(0, depth_drift) * 0.6 + (mean_duration / 10) * 0.4

    return {
        "depth_drift": depth_drift,
        "mean_duration": mean_duration,
        "return_efficiency": return_efficiency,
        "breathing_score": breathing_score,
        "invalidation_pressure": invalidation_pressure
    }