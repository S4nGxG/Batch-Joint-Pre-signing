import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import asyncio

from client import BJPClient
from sequential import SequentialClient
from utils import PLOTS_DIR, default_batch_items, plot_e2_communication, running_bjp_server, save_json


class MessageCounter:
    def __init__(self):
        self.send_count = 0
        self.recv_count = 0
        self.sent_bytes = 0
        self.recv_bytes = 0

    def log_send(self, data):
        self.send_count += 1
        self.sent_bytes += len(data)

    def log_recv(self, data):
        self.recv_count += 1
        self.recv_bytes += len(data)


def pct_reduction(old_value, new_value):
    if old_value == 0:
        return 0.0
    return (1 - new_value / old_value) * 100


def snapshot(counter):
    return {
        "messages_bidirectional": counter.send_count + counter.recv_count,
        "sent_bytes": counter.sent_bytes,
        "received_bytes": counter.recv_bytes,
    }


async def run_e2(k=8, host="127.0.0.1", port=9000):
    batch_items = default_batch_items(k)

    seq_client_counter = MessageCounter()
    seq_server_counter = MessageCounter()
    async with running_bjp_server(host=host, port=port, counter=seq_server_counter):
        seq_client = SequentialClient(server_host=host, server_port=port)
        await seq_client.run_batch(batch_items, counter=seq_client_counter)

    bjp_client_counter = MessageCounter()
    bjp_server_counter = MessageCounter()
    async with running_bjp_server(host=host, port=port, counter=bjp_server_counter):
        bjp_client = BJPClient(server_host=host, server_port=port)
        await bjp_client.batch_pre_sign(batch_items, counter=bjp_client_counter)

    sequential_payload = snapshot(seq_client_counter)
    bjp_payload = snapshot(bjp_client_counter)
    reduction = {
        "message_pct": pct_reduction(
            sequential_payload["messages_bidirectional"],
            bjp_payload["messages_bidirectional"],
        ),
        "sent_bytes_pct": pct_reduction(
            sequential_payload["sent_bytes"], bjp_payload["sent_bytes"]
        ),
        "received_bytes_pct": pct_reduction(
            sequential_payload["received_bytes"], bjp_payload["received_bytes"]
        ),
    }
    return {
        "k": k,
        "sequential": sequential_payload,
        "bjp": bjp_payload,
        "reduction": reduction,
        "consistency_check": {
            "sequential_client_sent_eq_server_recv": sequential_payload["sent_bytes"]
            == seq_server_counter.recv_bytes,
            "sequential_client_recv_eq_server_sent": sequential_payload["received_bytes"]
            == seq_server_counter.sent_bytes,
            "bjp_client_sent_eq_server_recv": bjp_payload["sent_bytes"]
            == bjp_server_counter.recv_bytes,
            "bjp_client_recv_eq_server_sent": bjp_payload["received_bytes"]
            == bjp_server_counter.sent_bytes,
        },
    }


if __name__ == "__main__":
    payload = asyncio.run(run_e2())
    save_json("e2_messages.json", payload)
    plot_e2_communication(payload, PLOTS_DIR / "e2_communication.png")
    print(payload)
