from pathlib import Path
import yaml

CONFIG = yaml.safe_load((Path(__file__).resolve().parents[1] / "config/scoring.yaml").read_text())

def score(module, factors):
    weights = CONFIG[module]
    total_weight = sum(weights.values())
    total = sum(float(factors.get(k, 0)) * w for k, w in weights.items()) / total_weight
    decision = "reject" if total < 60 else "selective" if total < 80 else "include" if total < 90 else "priority"
    return round(total, 2), decision
