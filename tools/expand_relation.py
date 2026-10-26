#!/usr/bin/env python3
"""Expand and verify a multilist candidate into complete short messages."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from model import pack, segments_matrix, digest, require, PRIME
from verify import load_case


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bridge", type=Path, default=ROOT/"data/short_collision.json")
    parser.add_argument("--relation", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True,
                        help="New directory for data/short_collision.json and messages/")
    args = parser.parse_args()
    bridge = json.loads(args.bridge.read_text())
    relation = json.loads(args.relation.read_text())
    coeff = relation.get("coefficients")
    require(coeff is not None, "Search did not return coefficients")
    cert = json.loads((ROOT/"data/short_collision.json").read_text())
    cert.update(bridge_bits=bridge["bridge_bits"], rho=bridge["rho"], coefficients=coeff,
                block_count=len(coeff), block_length_bits=len(bridge["bridge_bits"])+6)
    cert["bit_length"] = cert["block_count"]*cert["block_length_bits"]
    cert["packed_bytes"] = (cert["bit_length"]+7)//8
    require(cert["bit_length"] % 8 == 0, "This exporter requires byte-aligned short messages")
    blocks = (cert["block_prefixes"][0]+cert["bridge_bits"],
              cert["block_prefixes"][1]+cert["bridge_bits"])
    segments = [["".join(blocks[int(z == sign)] for z in coeff)] for sign in (1, -1)]
    products = [segments_matrix(m) for m in segments]
    require(products[0] == products[1], "Candidate is not a full original-matrix collision")
    cert["digest_hex"] = digest(products[0]).hex()
    buffers = [pack(m) for m in segments]
    require(buffers[0] != buffers[1], "Trivial relation")
    for info, data in zip(cert["messages"], buffers):
        info["sha256"] = hashlib.sha256(data).hexdigest()
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output/"data").mkdir()
    (args.output/"messages").mkdir()
    (args.output/"data/short_collision.json").write_text(json.dumps(cert, indent=2)+"\n")
    load_case("short", args.output/"data")
    for info, data in zip(cert["messages"], buffers):
        (args.output/"messages"/info["file"]).write_bytes(data)
    print(f"Verified full CHAMP-512 collision; output: {args.output}")


if __name__ == "__main__":
    main()
