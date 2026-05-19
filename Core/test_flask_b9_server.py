import json
import urllib.request
import urllib.error

BASE_URL = "http://localhost:8880"

def get_json(path):
    url = BASE_URL + path
    with urllib.request.urlopen(url, timeout=5) as response:
        body = response.read().decode("utf-8")
        data = json.loads(body)
        print("[PASS] GET " + path + " -> " + str(response.status))
        print(json.dumps(data, ensure_ascii=False, indent=2)[:1200])
        return data

def main():
    errors = []

    checks = [
        "/api/health",
        "/api/b9-nodes-live?symbol=GBPUSD&limit=10",
        "/api/b8-coalition-context?symbol=GBPUSD",
    ]

    for path in checks:
        try:
            data = get_json(path)
            if not isinstance(data, dict):
                errors.append(path + " returned non-dict JSON")
        except Exception as exc:
            errors.append(path + " failed: " + str(exc))

    if errors:
        print("")
        print("[FAIL] HTTP validation failed")
        for err in errors:
            print("  - " + err)
        raise SystemExit(1)

    print("")
    print("[OK] B9 Flask HTTP validation passed: 3/3 endpoints reachable")

if __name__ == "__main__":
    main()
