"""Baseline sequential TPC session."""

from __future__ import annotations

from client import BJPClient


class SequentialClient:
    """Baseline: execute one item per independent session."""

    def __init__(self, server_host: str = "127.0.0.1", server_port: int = 9000):
        self.server_host = server_host
        self.server_port = server_port

    async def single_pre_sign(self, item):
        client = BJPClient(server_host=self.server_host, server_port=self.server_port)
        _, timing = await client.batch_pre_sign([item])
        timing["messages_sent"] = 2
        timing["messages_recv"] = 2
        return timing

    async def run_batch(self, batch_items):
        total_ms = 0.0
        transport_ms = 0.0
        verify_ms = 0.0
        sent_bytes = 0
        recv_bytes = 0

        for item in batch_items:
            timing = await self.single_pre_sign(item)
            total_ms += timing["total_ms"]
            transport_ms += timing["transport_ms"]
            verify_ms += timing["verify_ms"]
            sent_bytes += timing["sent_bytes"]
            recv_bytes += timing["recv_bytes"]

        return {
            "total_ms": total_ms,
            "transport_ms": transport_ms,
            "verify_ms": verify_ms,
            "sent_bytes": sent_bytes,
            "recv_bytes": recv_bytes,
            "messages_sent": 2 * len(batch_items),
            "messages_recv": 2 * len(batch_items),
        }
