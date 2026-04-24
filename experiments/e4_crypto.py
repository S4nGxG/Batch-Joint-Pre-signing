import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import time

import numpy as np

from utils import default_batch_items, save_json

from adaptor_sig import keygen, pre_sign, pre_verify


def measure_crypto_cost(k, n_trials=100):
    """Đo chi phí thuần túy của k lần PreSig + PreVf."""

    sk, pk = keygen()
    times = []

    for _ in range(n_trials):
        items = default_batch_items(k)
        t_start = time.perf_counter()
        sigs = [pre_sign(sk, msg, Y) for msg, Y in items]
        _ = [
            pre_verify(pk.format(compressed=True), msg, Y, sig)
            for (msg, Y), sig in zip(items, sigs)
        ]
        times.append((time.perf_counter() - t_start) * 1000)

    return float(np.median(times))


if __name__ == "__main__":
    payload = {str(k): measure_crypto_cost(k) for k in [1, 2, 4, 8, 16]}
    save_json("e4_crypto.json", payload)
    print(payload)
