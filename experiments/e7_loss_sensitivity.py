import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import argparse
import asyncio
import os
import subprocess

import numpy as np

from client import BJPClient
from sequential import SequentialClient
from utils import (
    PLOTS_DIR,
    default_batch_items,
    median_reduction,
    plot_e7_loss_sensitivity,
    running_bjp_server,
    save_json,
)


def tc_replace_netem(interface: str, delay_ms: float, loss_pct: float):
    subprocess.run(
        [
            "tc",
            "qdisc",
            "replace",
            "dev",
            interface,
            "root",
            "netem",
            "delay",
            f"{delay_ms}ms",
            "loss",
            f"{loss_pct}%",
        ],
        check=True,
    )


def tc_clear(interface: str):
    subprocess.run(
        ["tc", "qdisc", "del", "dev", interface, "root"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


async def run_loss_point(loss_pct, n_trials=30, k=8, host="127.0.0.1", port=9000):
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

    seq_median = float(np.median(results["sequential"]))
    bjp_median = float(np.median(results["bjp"]))
    return {
        "loss_pct": float(loss_pct),
        "seq_median": seq_median,
        "bjp_median": bjp_median,
        "reduction_pct": float(median_reduction(seq_median, bjp_median)),
        "seq_std": float(np.std(results["sequential"])),
        "bjp_std": float(np.std(results["bjp"])),
    }


async def run_e7(
    loss_values,
    interface="lo",
    delay_ms=5.0,
    n_trials=30,
    k=8,
    host="127.0.0.1",
    port=9000,
):
    if os.name != "posix":
        raise SystemExit("E7 requires Linux tc netem support.")
    if os.geteuid() != 0:
        raise SystemExit("Run E7 with sudo so tc netem can modify the interface qdisc.")

    results = []
    try:
        for loss_pct in loss_values:
            tc_replace_netem(interface, delay_ms, loss_pct)
            result = await run_loss_point(
                loss_pct=loss_pct,
                n_trials=n_trials,
                k=k,
                host=host,
                port=port,
            )
            results.append(result)
    finally:
        tc_clear(interface)

    return {
        "interface": interface,
        "delay_ms_one_way": float(delay_ms),
        "k": k,
        "n_trials": n_trials,
        "loss_results": results,
    }


def parse_args():
    parser = argparse.ArgumentParser(description="Packet loss sensitivity experiment.")
    parser.add_argument("--iface", default="lo")
    parser.add_argument("--delay-ms", type=float, default=5.0)
    parser.add_argument("--k", type=int, default=8)
    parser.add_argument("--n-trials", type=int, default=30)
    parser.add_argument(
        "--loss-values",
        nargs="+",
        type=float,
        default=[0.1, 1.0, 2.0, 5.0],
        help="Packet loss percentages to test.",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    payload = asyncio.run(
        run_e7(
            loss_values=args.loss_values,
            interface=args.iface,
            delay_ms=args.delay_ms,
            n_trials=args.n_trials,
            k=args.k,
            host=args.host,
            port=args.port,
        )
    )
    save_json("e7_loss_sensitivity.json", payload)
    plot_e7_loss_sensitivity(payload["loss_results"], PLOTS_DIR / "e7_loss_sensitivity.png")

    for item in payload["loss_results"]:
        print(
            f"loss={item['loss_pct']:.1f}%: "
            f"Seq={item['seq_median']:.3f}ms, "
            f"BJP={item['bjp_median']:.3f}ms, "
            f"Reduction={item['reduction_pct']:.1f}%"
        )
