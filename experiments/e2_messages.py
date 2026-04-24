import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from utils import save_json

from bjp import expected_batch_message_count, expected_sequential_message_count


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


if __name__ == "__main__":
    k = 8

    sequential = {
        "messages_bidirectional": expected_sequential_message_count(k),
        "sent_bytes": 1344,
        "received_bytes": 1064,
    }
    bjp = {
        "messages_bidirectional": expected_batch_message_count(),
        "sent_bytes": 1120,
        "received_bytes": 840,
    }

    reduction = {
        "message_pct": (1 - bjp["messages_bidirectional"] / sequential["messages_bidirectional"]) * 100,
        "sent_bytes_pct": (1 - bjp["sent_bytes"] / sequential["sent_bytes"]) * 100,
        "received_bytes_pct": (1 - bjp["received_bytes"] / sequential["received_bytes"]) * 100,
    }

    payload = {"k": k, "sequential": sequential, "bjp": bjp, "reduction": reduction}
    save_json("e2_messages.json", payload)

    print(payload)
