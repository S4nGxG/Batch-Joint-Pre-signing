"""Batch Joint Pre-signing protocol helpers."""

from __future__ import annotations

import struct
from typing import List, Sequence, Tuple

STATEMENT_BYTES = 33
PRE_SIG_BYTES = 65

BatchItem = Tuple[bytes, bytes]
PreSignature = Tuple[bytes, bytes]


def serialize_batch(batch_items: Sequence[BatchItem]) -> bytes:
    parts = [struct.pack("!H", len(batch_items))]
    for msg, Y_bytes in batch_items:
        if len(Y_bytes) != STATEMENT_BYTES:
            raise ValueError("Each statement must be exactly 33 bytes.")
        parts.append(struct.pack("!H", len(msg)))
        parts.append(msg)
        parts.append(Y_bytes)
    return b"".join(parts)


def deserialize_batch(raw: bytes) -> List[BatchItem]:
    items: List[BatchItem] = []
    offset = 0
    if len(raw) < 2:
        raise ValueError("Batch payload too short.")

    k = struct.unpack_from("!H", raw, offset)[0]
    offset += 2
    for _ in range(k):
        msg_len = struct.unpack_from("!H", raw, offset)[0]
        offset += 2
        msg = raw[offset : offset + msg_len]
        offset += msg_len
        Y = raw[offset : offset + STATEMENT_BYTES]
        offset += STATEMENT_BYTES
        items.append((msg, Y))
    return items


def serialize_pre_sigs(pre_sigs: Sequence[PreSignature]) -> bytes:
    parts = [struct.pack("!H", len(pre_sigs))]
    for R_bytes, s_hat_bytes in pre_sigs:
        parts.append(R_bytes + s_hat_bytes)
    return b"".join(parts)


def deserialize_pre_sigs(raw: bytes) -> List[PreSignature]:
    if len(raw) < 2:
        raise ValueError("Pre-signature payload too short.")

    offset = 0
    k = struct.unpack_from("!H", raw, offset)[0]
    offset += 2
    items: List[PreSignature] = []
    for _ in range(k):
        R_bytes = raw[offset : offset + 33]
        offset += 33
        s_hat_bytes = raw[offset : offset + 32]
        offset += 32
        items.append((R_bytes, s_hat_bytes))
    return items


def expected_batch_message_count() -> int:
    return 4


def expected_sequential_message_count(k: int) -> int:
    return 4 * k
