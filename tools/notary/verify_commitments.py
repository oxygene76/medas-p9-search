#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Check notary entries against their commitments (protocol version 1, docs/notary-spec.md of medasdigital-2).

  python3 -I tools/notary/verify_commitments.py ENTRY=MANIFEST=RECEIPT [...] [--register docs/notary.md]

Per entry:
- the SHA-256 of the manifest file equals the receipt's content.sha256;
- the commitment SHA-256("medas-notary/v1" || uint8(len(creator)) || creator || salt || content_sha256), with the
  creator bech32-decoded (prefix medas), equals the receipt's hash;
- with --register: that hash and the manifest SHA-256 appear in the register (docs/notary.md), as the commitment and
  the manifest sha256 of the entry.
The receipts are read from decrypted files that the caller provides and removes afterwards. Nothing secret is
printed: no salt, only the first 12 hex digits of each hash.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"


def bech32_decode(addr, hrp="medas"):
    addr = addr.strip().lower()
    pos = addr.rfind("1")
    if addr[:pos] != hrp:
        raise ValueError(f"prefix is not {hrp}")
    data = [CHARSET.index(c) for c in addr[pos + 1:]]
    values = [ord(c) >> 5 for c in hrp] + [0] + [ord(c) & 31 for c in hrp] + data
    gen = [0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3]
    chk = 1
    for v in values:
        top = chk >> 25
        chk = (chk & 0x1FFFFFF) << 5 ^ v
        for i in range(5):
            chk ^= gen[i] if (top >> i) & 1 else 0
    if chk != 1:
        raise ValueError("bech32 checksum wrong")
    acc, bits, out = 0, 0, []
    for v in data[:-6]:
        acc = (acc << 5) | v
        bits += 5
        while bits >= 8:
            bits -= 8
            out.append((acc >> bits) & 0xFF)
    if bits >= 5 or (acc << (8 - bits)) & 0xFF:
        raise ValueError("bech32 padding wrong")
    return bytes(out)


def commitment(creator, salt_hex, content_sha256_hex):
    cb = bech32_decode(creator)
    if len(cb) not in (20, 32):
        raise ValueError(f"creator has {len(cb)} bytes")
    salt, digest = bytes.fromhex(salt_hex), bytes.fromhex(content_sha256_hex)
    if len(salt) != 32 or len(digest) != 32:
        raise ValueError("salt and content digest must be 32 bytes")
    return hashlib.sha256(b"medas-notary/v1" + bytes([len(cb)]) + cb + salt + digest).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("entries", nargs="+", metavar="ENTRY=MANIFEST=RECEIPT")
    ap.add_argument("--register", default=None)
    a = ap.parse_args()
    register = Path(a.register).read_text() if a.register else None
    bad = 0
    for spec in a.entries:
        name, mpath, rpath = spec.split("=", 2)
        msha = hashlib.sha256(Path(mpath).read_bytes()).hexdigest()
        r = json.loads(Path(rpath).read_text())
        checks = [("manifest = receipt content", msha == r["content"]["sha256"])]
        try:
            h = commitment(r["creator"], r["salt"], r["content"]["sha256"])
            checks.append(("commitment = receipt hash", h == r["hash"].lower()))
        except (ValueError, KeyError) as e:
            h = ""
            checks.append((f"commitment ({e})", False))
        if register is not None:
            checks.append(("hash in register", r["hash"].lower() in register.lower()))
            checks.append(("manifest sha256 in register", msha in register))
        ok = all(c for _, c in checks)
        bad += not ok
        print(f"{'OK ' if ok else 'BAD'} {name}: manifest {msha[:12]}…, commitment {h[:12]}… "
              + "; ".join(f"{t}: {'yes' if c else 'NO'}" for t, c in checks))
    print(f"{len(a.entries) - bad} of {len(a.entries)} entries match")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
