import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import asyncio

import numpy as np

from utils import PLOTS_DIR, default_batch_items, median_reduction, plot_latency_distribution, running_bjp_server, save_json

from client import BJPClient
from sequential import SequentialClient


async def run_e1(n_trials=100, k=8, host="127.0.0.1", port=9000):
    results = {"sequential": [], "bjp": []}
    batch_items = default_batch_items(k)

    async with running_bjp_server(host=host, port=port):
        for _ in range(n_trials):
            seq_client = SequentialClient(server_host=host, server_port=port)
            seq_total_ms = 0.0
            for item in batch_items:
                timing = await seq_client.single_pre_sign(item)
                seq_total_ms += timing["total_ms"]
            results["sequential"].append(seq_total_ms)

            bjp_client = BJPClient(server_host=host, server_port=port)
            _, timing = await bjp_client.batch_pre_sign(batch_items)
            results["bjp"].append(timing["total_ms"])

    return results


if __name__ == "__main__":
    results = asyncio.run(run_e1())
    seq_median = float(np.median(results["sequential"]))
    bjp_median = float(np.median(results["bjp"]))
    reduction = median_reduction(seq_median, bjp_median)

    save_json(
        "e1_latency.json",
        {
            "sequential": results["sequential"],
            "bjp": results["bjp"],
            "seq_median": seq_median,
            "bjp_median": bjp_median,
            "reduction_pct": reduction,
        },
    )
    plot_latency_distribution(
        results["sequential"], results["bjp"], PLOTS_DIR / "e1_latency_distribution.png"
    )

    print(f"Sequential: {seq_median:.3f} ms")
    print(f"BJP: {bjp_median:.3f} ms")
    print(f"Reduction: {reduction:.1f}%")
