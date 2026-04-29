import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import json

import numpy as np
from scipy import stats

from utils import save_json


def cohen_d(seq_times, bjp_times):
    seq_mean = np.mean(seq_times)
    bjp_mean = np.mean(bjp_times)
    seq_std = np.std(seq_times)
    bjp_std = np.std(bjp_times)
    pooled_std = np.sqrt((seq_std**2 + bjp_std**2) / 2)
    if pooled_std == 0:
        return 0.0
    return float((seq_mean - bjp_mean) / pooled_std)


def statistical_test(seq_times, bjp_times, alpha=0.05):
    statistic, p_value = stats.mannwhitneyu(
        bjp_times, seq_times, alternative="less"
    )
    d_value = cohen_d(seq_times, bjp_times)
    reject_h0 = bool(p_value < alpha)
    medium_effect = bool(d_value > 0.5)

    return {
        "alpha": float(alpha),
        "mann_whitney_u": float(statistic),
        "p_value_one_tailed": float(p_value),
        "reject_h0": reject_h0,
        "cohens_d": float(d_value),
        "medium_effect_or_better": medium_effect,
        "conclusion": (
            "Bac bo H0 - BJP cai thien dang ke"
            if reject_h0
            else "Khong du bang chung de bac bo H0"
        ),
    }


def metric_payload(seq_times, bjp_times, alpha=0.05):
    result = statistical_test(seq_times, bjp_times, alpha=alpha)
    seq_median = float(np.median(seq_times))
    bjp_median = float(np.median(bjp_times))
    result.update(
        {
            "seq_median_ms": seq_median,
            "bjp_median_ms": bjp_median,
            "reduction_pct": (
                0.0
                if seq_median == 0
                else float((seq_median - bjp_median) / seq_median * 100.0)
            ),
            "n_sequential": len(seq_times),
            "n_bjp": len(bjp_times),
        }
    )
    return result


def load_latency_results(path):
    with Path(path).open("r", encoding="utf-8") as f:
        payload = json.load(f)

    metrics = {
        "client_latency": (payload["sequential"], payload["bjp"]),
    }
    if "sequential_transport" not in payload or "bjp_transport" not in payload:
        raise KeyError(
            "Missing transport latency samples. Re-run experiments/e1_latency.py "
            "to generate sequential_transport and bjp_transport."
        )
    metrics["transport_latency"] = (
        payload["sequential_transport"],
        payload["bjp_transport"],
    )
    return metrics


if __name__ == "__main__":
    input_path = ROOT / "results" / "e1_latency.json"
    latency_metrics = load_latency_results(input_path)
    payload = {
        "input_file": str(input_path),
        "metrics": {
            name: metric_payload(seq_times, bjp_times, alpha=0.05)
            for name, (seq_times, bjp_times) in latency_metrics.items()
        },
    }
    save_json("e6_stats.json", payload)

    for name, result in payload["metrics"].items():
        print(f"{name}:")
        print(f"  Mann-Whitney U statistic: {result['mann_whitney_u']:.1f}")
        print(f"  p-value (one-tailed): {result['p_value_one_tailed']:.6f}")
        print(f"  Cohen's d (effect size): {result['cohens_d']:.3f}")
        print(f"  Sequential median: {result['seq_median_ms']:.3f} ms")
        print(f"  BJP median: {result['bjp_median_ms']:.3f} ms")
        print(f"  Reduction: {result['reduction_pct']:.1f}%")
        print(f"  Conclusion: {result['conclusion']}")
