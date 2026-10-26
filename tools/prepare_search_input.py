#!/usr/bin/env python3
"""Write the finite-field weights consumed by multilist_search.cpp."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from model import PRIME, C, D, require, word_matrix


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bridge", type=Path, default=ROOT/"data/short_collision.json")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--group-exponent", type=int, default=6)
    parser.add_argument("--list-bits", type=int, default=19)
    args = parser.parse_args()
    record = json.loads(args.bridge.read_text())
    require(int(record["prime"]) == PRIME, "Incorrect prime")
    s = record["bridge_bits"]
    G = word_matrix(s, (C, D))
    require(sum(G) % PRIME == 0, "Incorrect bridge")
    rho = (G[0]+G[1])**2*pow(pow(2, len(s), PRIME), -1, PRIME) % PRIME
    require(rho == int(record["rho"]), "Incorrect rho")
    require(2 <= args.group_exponent <= 9 and 2 <= args.list_bits <= 22, "Bad list sizes")
    positions = (1 << args.group_exponent)*args.list_bits
    weights, value = [], 1
    for _ in range(positions):
        weights.append(format(value, "x"))
        value = value*rho % PRIME
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        format(PRIME, "x")+"\n"+f"{args.group_exponent} {args.list_bits}\n"+
        "\n".join(weights)+"\n")
    print(f"Wrote {positions} weights to {args.output}")


if __name__ == "__main__":
    main()
