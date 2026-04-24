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


async def run_scalability(k_values=None, n_trials=50, host="127.0.0.1", port=9000):
    if k_values is None:
        k_values = [1, 2, 4, 6, 8, 10, 12, 14, 16]

    results = {}
    async with running_bjp_server(host=host, port=port):
        for k in k_values:
            batch_items = default_batch_items(k)
            seq_times = []
            bjp_times = []

            for _ in range(n_trials):
                seq_client = SequentialClient(server_host=host, server_port=port)
                seq_total = 0.0
                for item in batch_items:
                    timing = await seq_client.single_pre_sign(item)
                    seq_total += timing["total_ms"]
                seq_times.append(seq_total)

                bjp_client = BJPClient(server_host=host, server_port=port)
                _, timing = await bjp_client.batch_pre_sign(batch_items)
                bjp_times.append(timing["total_ms"])

            results[k] = {
                "seq_median": float(np.median(seq_times)),
                "bjp_median": float(np.median(bjp_times)),
            }
    return results


if __name__ == "__main__":
    payload = asyncio.run(run_scalability())
    save_json("e3_scalability.json", payload)
    print(payload)
