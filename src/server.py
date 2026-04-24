"""TCP server endpoint for BJP."""

from __future__ import annotations

import argparse
import asyncio
import time

from adaptor_sig import keygen, pre_sign
from bjp import deserialize_batch, serialize_pre_sigs


class BJPServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 9000, counter=None):
        self.host = host
        self.port = port
        self.counter = counter
        self.sk, self.pk = keygen()

    async def handle_batch(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Xử lý một phiên BJP hoàn chỉnh."""

        try:
            raw = await reader.read(65536)
            if self.counter is not None:
                self.counter.log_recv(raw)
            if not raw:
                return 0.0

            batch_items = self._deserialize_batch(raw)
            t_crypto_start = time.perf_counter()
            pre_sigs = []
            for msg, Y_bytes in batch_items:
                pre_sig = pre_sign(self.sk, msg, Y_bytes)
                pre_sigs.append(pre_sig)
            t_crypto = time.perf_counter() - t_crypto_start

            response = self._serialize_pre_sigs(pre_sigs)
            writer.write(response)
            if self.counter is not None:
                self.counter.log_send(response)
            await writer.drain()

            ack = await reader.read(1024)
            if self.counter is not None:
                self.counter.log_recv(ack)

            final_ack = b"\x01"
            writer.write(final_ack)
            if self.counter is not None:
                self.counter.log_send(final_ack)
            await writer.drain()
            return t_crypto
        finally:
            writer.close()
            await writer.wait_closed()

    def _deserialize_batch(self, raw: bytes):
        return deserialize_batch(raw)

    def _serialize_pre_sigs(self, pre_sigs):
        return serialize_pre_sigs(pre_sigs)

    async def run(self):
        server = await asyncio.start_server(self.handle_batch, self.host, self.port)
        async with server:
            await server.serve_forever()


def main():
    parser = argparse.ArgumentParser(description="Run BJP TCP server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)
    args = parser.parse_args()
    asyncio.run(BJPServer(host=args.host, port=args.port).run())


if __name__ == "__main__":
    main()
