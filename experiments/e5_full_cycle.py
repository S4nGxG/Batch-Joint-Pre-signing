import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import asyncio

import numpy as np

from utils import default_batch_items, running_bjp_server, save_json

from client import BJPClient
from sequential import SequentialClient


async def simulate_sequential_arc(k, host="127.0.0.1", port=9000):
    client = SequentialClient(server_host=host, server_port=port)
    batch_items = default_batch_items(k)
    total = 0.0
    for item in batch_items:
        timing = await client.single_pre_sign(item)
        total += timing["total_ms"]
    return total


async def simulate_bjp_arc(k, host="127.0.0.1", port=9000):
    client = BJPClient(server_host=host, server_port=port)
    batch_items = default_batch_items(k)
    _, timing = await client.batch_pre_sign(batch_items)
    return timing["total_ms"]


async def simulate_preswap(n, n_trials=30, host="127.0.0.1", port=9000):
    """
    Mô phỏng giai đoạn Pre-swap cho n participants.
    p = n arcs, k = 2n-1 items mỗi arc.
    """

    k = 2 * n - 1
    p = n

    seq_times = []
    bjp_times = []

    async with running_bjp_server(host=host, port=port):
        for _ in range(n_trials):
            seq_arc_tasks = [simulate_sequential_arc(k, host, port) for _ in range(p)]
            arc_times_seq = await asyncio.gather(*seq_arc_tasks)
            seq_times.append(max(arc_times_seq))

            bjp_arc_tasks = [simulate_bjp_arc(k, host, port) for _ in range(p)]
            arc_times_bjp = await asyncio.gather(*bjp_arc_tasks)
            bjp_times.append(max(arc_times_bjp))

    return {
        "n": n,
        "k": k,
        "p": p,
        "seq_median": float(np.median(seq_times)),
        "bjp_median": float(np.median(bjp_times)),
        "reduction_pct": float((1 - np.median(bjp_times) / np.median(seq_times)) * 100),
    }


if __name__ == "__main__":
    results = []
    for n in [3, 5, 8]:
        result = asyncio.run(simulate_preswap(n))
        results.append(result)
        print(
            f"n={result['n']}, k={result['k']}, p={result['p']}: "
            f"Seq={result['seq_median']:.1f}ms, BJP={result['bjp_median']:.1f}ms, "
            f"Reduction={result['reduction_pct']:.1f}%"
        )

    save_json("e5_full_cycle.json", results)
