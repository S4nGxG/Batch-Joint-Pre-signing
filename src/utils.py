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


def experiment_path_setup():
    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))


@asynccontextmanager
async def running_bjp_server(host: str = "127.0.0.1", port: int = 9000):
    from server import BJPServer

    server = BJPServer(host=host, port=port)
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
    except ImportError:  # pragma: no cover - optional
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
