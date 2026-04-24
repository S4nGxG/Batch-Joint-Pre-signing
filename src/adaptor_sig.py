"""Schnorr adaptor signature over secp256k1.

This module follows the code sketch described in HD.pdf. The verification step
is intentionally simplified, matching the guide's note that it is a placeholder
for the full ECC relation check from the paper.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import Tuple

try:
    import coincurve
except ImportError:  # pragma: no cover - optional dependency
    coincurve = None


CURVE_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141


@dataclass(frozen=True)
class FallbackPublicKey:
    """Small stand-in when coincurve is unavailable."""

    data: bytes

    def format(self, compressed: bool = True) -> bytes:
        return self.data


def _ensure_32_bytes(value: int) -> bytes:
    return value.to_bytes(32, "big")


def _fake_pubkey_from_secret(secret: int) -> FallbackPublicKey:
    digest = hashlib.sha256(b"pk" + _ensure_32_bytes(secret)).digest()
    prefix = b"\x02" if digest[0] % 2 == 0 else b"\x03"
    return FallbackPublicKey(prefix + digest[:32])


def keygen() -> Tuple[int, object]:
    """Tao cặp khóa Schnorr."""

    sk_bytes = os.urandom(32)
    sk = int.from_bytes(sk_bytes, "big") % CURVE_ORDER
    if sk == 0:
        sk = 1

    if coincurve is not None:
        pk = coincurve.PublicKey.from_secret(_ensure_32_bytes(sk))
    else:
        pk = _fake_pubkey_from_secret(sk)
    return sk, pk


def hash_challenge(pk_bytes: bytes, R_bytes: bytes, msg: bytes) -> int:
    """Tính thách thức Fiat-Shamir e = H(pk || R || msg)."""

    h = hashlib.sha256()
    h.update(pk_bytes + R_bytes + msg)
    return int.from_bytes(h.digest(), "big") % CURVE_ORDER


def pre_sign(sk: int, msg: bytes, Y_bytes: bytes):
    """Tạo pre-signature (R, s_hat) cho msg với statement Y."""

    r_nonce = int.from_bytes(os.urandom(32), "big") % CURVE_ORDER
    if r_nonce == 0:
        r_nonce = 1

    if coincurve is not None:
        R = coincurve.PublicKey.from_secret(_ensure_32_bytes(r_nonce))
        pk_bytes = coincurve.PublicKey.from_secret(_ensure_32_bytes(sk)).format(
            compressed=True
        )
        R_bytes = R.format(compressed=True)
    else:
        R_bytes = _fake_pubkey_from_secret(r_nonce).format(compressed=True)
        pk_bytes = _fake_pubkey_from_secret(sk).format(compressed=True)

    e = hash_challenge(pk_bytes, R_bytes + Y_bytes, msg)
    s_hat = (r_nonce - e * sk) % CURVE_ORDER
    return (R_bytes, _ensure_32_bytes(s_hat))


def pre_verify(pk_bytes: bytes, msg: bytes, Y_bytes: bytes, pre_sig) -> bool:
    """Xác minh pre-signature."""

    R_bytes, s_hat_bytes = pre_sig
    if len(R_bytes) != 33 or len(s_hat_bytes) != 32 or len(Y_bytes) != 33:
        return False

    _ = int.from_bytes(s_hat_bytes, "big")
    _ = hash_challenge(pk_bytes, R_bytes + Y_bytes, msg)
    return True


def adapt(pre_sig, witness: bytes):
    """Adapt pre-signature thành signature hợp lệ bằng cách thêm witness."""

    R_bytes, s_hat_bytes = pre_sig
    s_hat = int.from_bytes(s_hat_bytes, "big")
    w = int.from_bytes(witness, "big")
    s = (s_hat + w) % CURVE_ORDER
    return (R_bytes, _ensure_32_bytes(s))


def extract_witness(pre_sig, sig, Y_bytes: bytes) -> bytes:
    """Trích xuất witness từ cặp pre-signature và signature."""

    del Y_bytes
    _, s_hat_bytes = pre_sig
    _, s_bytes = sig
    s_hat = int.from_bytes(s_hat_bytes, "big")
    s = int.from_bytes(s_bytes, "big")
    w = (s - s_hat) % CURVE_ORDER
    return _ensure_32_bytes(w)
