import json
from pf_cascade_engine import evaluate_cascade

if __name__ == '__main__':
    print(json.dumps(evaluate_cascade(), ensure_ascii=False, indent=2))
