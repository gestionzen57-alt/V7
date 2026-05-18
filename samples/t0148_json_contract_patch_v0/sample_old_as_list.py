def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in ("matches", "rows", "items", "candidates", "moments", "false_positive_rows"):
            if isinstance(value.get(key), list):
                return value[key]
    return []
