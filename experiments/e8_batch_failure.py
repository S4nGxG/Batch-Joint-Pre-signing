import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import argparse
import asyncio
import time

import numpy as np

from client import BJPClient
from sequential import SequentialClient
from utils import PLOTS_DIR, default_batch_items, plot_e8_batch_failure, running_bjp_server, save_json


def detect_fault(batch_items, pre_sigs):
    if len(pre_sigs) != len(batch_items):
        return min(len(pre_sigs), len(batch_items))

    for i, pre_sig in enumerate(pre_sigs):
        r_bytes, s_hat_bytes = pre_sig
        if r_bytes == b"\x00" * 33 or s_hat_bytes == b"\x00" * 32:
            return i
    return None


async def run_clean_sequential(k, host="127.0.0.1", port=9000):
    batch_items = default_batch_items(k)
    async with running_bjp_server(host=host, port=port):
        client = SequentialClient(server_host=host, server_port=port)
        total_ms = 0.0
        for item in batch_items:
            timing = await client.single_pre_sign(item)
            total_ms += timing["total_ms"]
    return total_ms


async def run_faulty_sequential(k, fault_item_index, host="127.0.0.1", port=9000):
    batch_items = default_batch_items(k)
    detect_ms = 0.0
    retry_ms = 0.0

    async with running_bjp_server(
        host=host,
        port=port,
        fault_session_index=fault_item_index + 1,
        fault_item_index=0,
        fault_mode="zero_signature",
    ):
        t_start = time.perf_counter()
        for i, item in enumerate(batch_items):
            client = BJPClient(server_host=host, server_port=port)
            pre_sigs, _ = await client.batch_pre_sign([item], verify=False)
            t_detect_start = time.perf_counter()
            failed_index = detect_fault([item], pre_sigs)
            detect_ms += (time.perf_counter() - t_detect_start) * 1000
            if failed_index is not None:
                retry_client = BJPClient(server_host=host, server_port=port)
                _, retry_timing = await retry_client.batch_pre_sign([item])
                retry_ms += retry_timing["total_ms"]
        total_ms = (time.perf_counter() - t_start) * 1000

    return {
        "detect_ms": detect_ms,
        "retry_ms": retry_ms,
        "total_ms": total_ms,
    }


async def run_clean_bjp(k, host="127.0.0.1", port=9000):
    batch_items = default_batch_items(k)
    async with running_bjp_server(host=host, port=port):
        client = BJPClient(server_host=host, server_port=port)
        _, timing = await client.batch_pre_sign(batch_items)
    return timing["total_ms"]


async def run_faulty_bjp(k, fault_item_index, host="127.0.0.1", port=9000):
    batch_items = default_batch_items(k)

    async with running_bjp_server(
        host=host,
        port=port,
        fault_session_index=1,
        fault_item_index=fault_item_index,
        fault_mode="zero_signature",
    ):
        client = BJPClient(server_host=host, server_port=port)
        t_start = time.perf_counter()
        pre_sigs, _ = await client.batch_pre_sign(batch_items, verify=False)
        t_detect_start = time.perf_counter()
        failed_index = detect_fault(batch_items, pre_sigs)
        detect_ms = (time.perf_counter() - t_detect_start) * 1000
        retry_ms = 0.0
        if failed_index is not None:
            retry_client = BJPClient(server_host=host, server_port=port)
            _, retry_timing = await retry_client.batch_pre_sign(batch_items)
            retry_ms = retry_timing["total_ms"]
        total_ms = (time.perf_counter() - t_start) * 1000

    return {
        "detect_ms": detect_ms,
        "retry_ms": retry_ms,
        "total_ms": total_ms,
    }


def summarize(clean_samples, fault_samples):
    clean_median = float(np.median(clean_samples))
    detect_median = float(np.median([item["detect_ms"] for item in fault_samples]))
    retry_median = float(np.median([item["retry_ms"] for item in fault_samples]))
    fault_total_median = float(np.median([item["total_ms"] for item in fault_samples]))
    overhead_pct = 0.0 if clean_median == 0 else float((fault_total_median - clean_median) / clean_median * 100)
    return {
        "clean_median_ms": clean_median,
        "detect_median_ms": detect_median,
        "retry_median_ms": retry_median,
        "fault_total_median_ms": fault_total_median,
        "overhead_pct": overhead_pct,
    }


async def run_e8(n_trials, k=8, fault_item_index=3, host="127.0.0.1", port=9000):
    seq_clean = []
    seq_fault = []
    bjp_clean = []
    bjp_fault = []

    for _ in range(n_trials):
        seq_clean.append(await run_clean_sequential(k, host=host, port=port))
        seq_fault.append(
            await run_faulty_sequential(
                k,
                fault_item_index=fault_item_index,
                host=host,
                port=port,
            )
        )
        bjp_clean.append(await run_clean_bjp(k, host=host, port=port))
        bjp_fault.append(
            await run_faulty_bjp(
                k,
                fault_item_index=fault_item_index,
                host=host,
                port=port,
            )
        )

    return {
        "k": k,
        "n_trials": n_trials,
        "fault_item_index": fault_item_index,
        "fault_mode": "zero_signature",
        "sequential": summarize(seq_clean, seq_fault),
        "bjp": summarize(bjp_clean, bjp_fault),
    }


def parse_args():
    parser = argparse.ArgumentParser(description="Batch failure recovery experiment.")
    parser.add_argument("--k", type=int, default=8)
    parser.add_argument("--n-trials", type=int, default=20)
    parser.add_argument("--fault-item-index", type=int, default=3)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    payload = asyncio.run(
        run_e8(
            n_trials=args.n_trials,
            k=args.k,
            fault_item_index=args.fault_item_index,
            host=args.host,
            port=args.port,
        )
    )
    save_json("e8_batch_failure.json", payload)
    plot_e8_batch_failure(payload, PLOTS_DIR / "e8_batch_failure.png")

    print(
        f"Sequential clean={payload['sequential']['clean_median_ms']:.3f}ms, "
        f"fault+retry={payload['sequential']['fault_total_median_ms']:.3f}ms, "
        f"overhead={payload['sequential']['overhead_pct']:.1f}%"
    )
    print(
        f"BJP clean={payload['bjp']['clean_median_ms']:.3f}ms, "
        f"fault+retry={payload['bjp']['fault_total_median_ms']:.3f}ms, "
        f"overhead={payload['bjp']['overhead_pct']:.1f}%"
    )
