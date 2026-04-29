"""Serialization, timing, plotting, and experiment utilities."""

from __future__ import annotations

import asyncio
import json
import sys
from contextlib import asynccontextmanager, suppress
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = BASE_DIR / "results"
PLOTS_DIR = BASE_DIR / "plots"
SRC_DIR = BASE_DIR / "src"


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def default_batch_items(k: int):
    return [(f"tx_{i}".encode(), bytes([i % 251]) * 33) for i in range(k)]


def median_reduction(seq_median: float, bjp_median: float) -> float:
    if seq_median == 0:
        return 0.0
    return (seq_median - bjp_median) / seq_median * 100.0


def save_json(filename: str, payload) -> Path:
    ensure_dir(RESULTS_DIR)
    path = RESULTS_DIR / filename
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return path


def load_json(filename: str):
    path = RESULTS_DIR / filename
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def experiment_path_setup():
    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))


@asynccontextmanager
async def running_bjp_server(host: str = "127.0.0.1", port: int = 9000, **server_kwargs):
    from server import BJPServer

    server = BJPServer(host=host, port=port, **server_kwargs)
    task = asyncio.create_task(server.run())
    await asyncio.sleep(0.05)
    try:
        yield server
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


def plot_latency_distribution(seq_times, bjp_times, output_path):
    import matplotlib.pyplot as plt

    try:
        import seaborn as sns  # noqa: F401
    except Exception:  # pragma: no cover - optional
        sns = None

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))

    axes[0].violinplot([seq_times, bjp_times], positions=[0, 1])
    axes[0].set_xticks([0, 1])
    axes[0].set_xticklabels(["Sequential", "BJP"])
    axes[0].set_ylabel("Latency (ms)")
    axes[0].set_title("Session Latency Distribution")

    axes[1].boxplot([seq_times, bjp_times], labels=["Sequential", "BJP"])
    axes[1].set_ylabel("Latency (ms)")
    axes[1].set_title("Latency Comparison")

    plt.tight_layout()
    ensure_dir(Path(output_path).parent)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_hd_63_summary(seq_times, bjp_times, scalability_results, output_path):
    import matplotlib.pyplot as plt

    try:
        import seaborn as sns  # noqa: F401
    except Exception:  # pragma: no cover - optional
        sns = None

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))

    axes[0].violinplot([seq_times, bjp_times], positions=[0, 1])
    axes[0].set_xticks([0, 1])
    axes[0].set_xticklabels(["Sequential", "BJP"])
    axes[0].set_ylabel("Latency (ms)")
    axes[0].set_title("Session Latency Distribution")

    normalized = {int(k): value for k, value in scalability_results.items()}
    k_values = sorted(normalized.keys())
    seq = [normalized[k]["seq_median"] for k in k_values]
    bjp = [normalized[k]["bjp_median"] for k in k_values]
    axes[1].plot(k_values, seq, marker="o", label="Sequential")
    axes[1].plot(k_values, bjp, marker="s", label="BJP")
    axes[1].set_xlabel("k")
    axes[1].set_ylabel("Median Latency (ms)")
    axes[1].set_title("Scalability Plot")
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()

    plt.tight_layout()
    ensure_dir(Path(output_path).parent)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_e2_communication(payload, output_path):
    import matplotlib.pyplot as plt

    labels = ["Messages", "Sent Bytes", "Received Bytes"]
    sequential = [
        payload["sequential"]["messages_bidirectional"],
        payload["sequential"]["sent_bytes"],
        payload["sequential"]["received_bytes"],
    ]
    bjp = [
        payload["bjp"]["messages_bidirectional"],
        payload["bjp"]["sent_bytes"],
        payload["bjp"]["received_bytes"],
    ]

    fig, ax = plt.subplots(figsize=(8, 4))
    x = range(len(labels))
    width = 0.35
    ax.bar([i - width / 2 for i in x], sequential, width=width, label="Sequential")
    ax.bar([i + width / 2 for i in x], bjp, width=width, label="BJP")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_ylabel("Count")
    ax.set_title(f"Communication Overhead (k={payload['k']})")
    ax.legend()

    plt.tight_layout()
    ensure_dir(Path(output_path).parent)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_e3_scalability(results, output_path):
    import matplotlib.pyplot as plt

    k_values = sorted(int(k) for k in results.keys())
    seq = [results[k]["seq_median"] for k in k_values]
    bjp = [results[k]["bjp_median"] for k in k_values]

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(k_values, seq, marker="o", label="Sequential")
    ax.plot(k_values, bjp, marker="s", label="BJP")
    ax.set_xlabel("k")
    ax.set_ylabel("Median Latency (ms)")
    ax.set_title("Scalability by Batch Size")
    ax.grid(True, alpha=0.3)
    ax.legend()

    plt.tight_layout()
    ensure_dir(Path(output_path).parent)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_e4_crypto(payload, output_path):
    import matplotlib.pyplot as plt

    k_values = [int(k) for k in payload.keys()]
    values = [payload[str(k)] for k in k_values]

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(k_values, values, width=0.8)
    ax.set_xlabel("k")
    ax.set_ylabel("Median Crypto Cost (ms)")
    ax.set_title("Cryptographic Cost by Batch Size")
    ax.grid(True, axis="y", alpha=0.3)

    plt.tight_layout()
    ensure_dir(Path(output_path).parent)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_e5_full_cycle(results, output_path):
    import matplotlib.pyplot as plt

    n_values = [item["n"] for item in results]
    seq = [item["seq_median"] for item in results]
    bjp = [item["bjp_median"] for item in results]

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(n_values, seq, marker="o", label="Sequential")
    ax.plot(n_values, bjp, marker="s", label="BJP")
    ax.set_xlabel("n Participants")
    ax.set_ylabel("Median Pre-swap Time (ms)")
    ax.set_title("Full Pre-swap Cycle Simulation")
    ax.grid(True, alpha=0.3)
    ax.legend()

    plt.tight_layout()
    ensure_dir(Path(output_path).parent)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_e7_loss_sensitivity(results, output_path):
    import matplotlib.pyplot as plt

    loss_values = [item["loss_pct"] for item in results]
    seq = [item["seq_median"] for item in results]
    bjp = [item["bjp_median"] for item in results]
    reduction = [item["reduction_pct"] for item in results]

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))

    axes[0].plot(loss_values, seq, marker="o", label="Sequential")
    axes[0].plot(loss_values, bjp, marker="s", label="BJP")
    axes[0].set_xlabel("Packet Loss (%)")
    axes[0].set_ylabel("Median Latency (ms)")
    axes[0].set_title("Latency Under Packet Loss")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    axes[1].plot(loss_values, reduction, marker="d", color="tab:green")
    axes[1].set_xlabel("Packet Loss (%)")
    axes[1].set_ylabel("Latency Reduction (%)")
    axes[1].set_title("BJP Reduction vs Packet Loss")
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    ensure_dir(Path(output_path).parent)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_e8_batch_failure(payload, output_path):
    import matplotlib.pyplot as plt

    labels = ["Clean", "Fault+Retry", "Retry Only", "Detect Only"]
    sequential = [
        payload["sequential"]["clean_median_ms"],
        payload["sequential"]["fault_total_median_ms"],
        payload["sequential"]["retry_median_ms"],
        payload["sequential"]["detect_median_ms"],
    ]
    bjp = [
        payload["bjp"]["clean_median_ms"],
        payload["bjp"]["fault_total_median_ms"],
        payload["bjp"]["retry_median_ms"],
        payload["bjp"]["detect_median_ms"],
    ]

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))

    x = range(len(labels))
    width = 0.35
    axes[0].bar([i - width / 2 for i in x], sequential, width=width, label="Sequential")
    axes[0].bar([i + width / 2 for i in x], bjp, width=width, label="BJP")
    axes[0].set_xticks(list(x))
    axes[0].set_xticklabels(labels, rotation=15)
    axes[0].set_ylabel("Median Time (ms)")
    axes[0].set_title("Batch Failure Recovery Cost")
    axes[0].legend()

    overheads = [
        payload["sequential"]["overhead_pct"],
        payload["bjp"]["overhead_pct"],
    ]
    axes[1].bar(["Sequential", "BJP"], overheads, color=["tab:blue", "tab:orange"])
    axes[1].set_ylabel("Overhead (%)")
    axes[1].set_title("Recovery Overhead vs Clean Run")
    axes[1].grid(True, axis="y", alpha=0.3)

    plt.tight_layout()
    ensure_dir(Path(output_path).parent)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
