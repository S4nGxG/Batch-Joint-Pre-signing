"""TCP client endpoint for BJP."""

from __future__ import annotations

import argparse
import asyncio
import time

from adaptor_sig import keygen, pre_verify
from bjp import deserialize_pre_sigs, serialize_batch


class BJPClient:
    def __init__(self, server_host: str = "127.0.0.1", server_port: int = 9000):
        self.server_host = server_host
        self.server_port = server_port
        self.sk, self.pk = keygen()

    async def batch_pre_sign(self, batch_items, counter=None, verify=True):
        """
        Thực hiện BJP cho k items.
        batch_items: list of (msg, Y_bytes)
        Trả về: list of pre-signatures, timing info
        """

        t_start = time.perf_counter()
        reader, writer = await asyncio.open_connection(self.server_host, self.server_port)

        init_payload = self._serialize_batch(batch_items)
        t_send = time.perf_counter()
        writer.write(init_payload)
        if counter is not None:
            counter.log_send(init_payload)
        await writer.drain()

        raw_response = await reader.read(65536)
        if counter is not None:
            counter.log_recv(raw_response)
        t_recv = time.perf_counter()
        pre_sigs = self._deserialize_pre_sigs(raw_response)

        t_verify_start = time.perf_counter()
        failed_index = None
        verify_ok = True
        if verify:
            for i, (pre_sig, (msg, Y_bytes)) in enumerate(zip(pre_sigs, batch_items)):
                if not pre_verify(self.pk.format(compressed=True), msg, Y_bytes, pre_sig):
                    verify_ok = False
                    failed_index = i
                    break
            if verify_ok and len(pre_sigs) != len(batch_items):
                verify_ok = False
                failed_index = min(len(pre_sigs), len(batch_items))
            assert verify_ok, f"Pre-signature item {failed_index} failed verification"
        t_verify = time.perf_counter() - t_verify_start

        ack_payload = b"\x01" * len(batch_items)
        writer.write(ack_payload)
        if counter is not None:
            counter.log_send(ack_payload)
        await writer.drain()

        final_ack = await reader.read(1)
        if counter is not None:
            counter.log_recv(final_ack)
        t_end = time.perf_counter()

        writer.close()
        await writer.wait_closed()

        timing = {
            "total_ms": (t_end - t_start) * 1000,
            "transport_ms": (t_recv - t_send) * 1000,
            "verify_ms": t_verify * 1000,
            "sent_bytes": len(init_payload) + len(ack_payload),
            "recv_bytes": len(raw_response) + len(final_ack),
            "messages_sent": 2,
            "messages_recv": 2,
            "verify_ok": verify_ok,
            "failed_index": failed_index,
        }
        return pre_sigs, timing

    def _serialize_batch(self, batch_items):
        return serialize_batch(batch_items)

    def _deserialize_pre_sigs(self, raw_response: bytes):
        return deserialize_pre_sigs(raw_response)


async def _demo(server_host: str, server_port: int, k: int):
    client = BJPClient(server_host=server_host, server_port=server_port)
    batch_items = [(f"tx_{i}".encode(), bytes([i % 251]) * 33) for i in range(k)]
    _, timing = await client.batch_pre_sign(batch_items)
    print(timing)


def main():
    parser = argparse.ArgumentParser(description="Run a BJP client demo.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--k", type=int, default=8)
    args = parser.parse_args()
    asyncio.run(_demo(args.host, args.port, args.k))


if __name__ == "__main__":
    main()
