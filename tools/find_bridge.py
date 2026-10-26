#!/usr/bin/env python3
"""Bounded CHAMP-512 bridge search for p = 2**128 - 15449."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from model import PRIME, C, D, decode_rational, require, word_matrix


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-r", type=int, default=10)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(0 <= args.max_r <= 63, "max-r must be between 0 and 63")
    trials = 0
    for r in range(args.max_r+1):
        j = 64-r
        lower = 15449//(1 << j)+1
        upper = (9*(1 << (128-j))+5*15449-1)//(5*(1 << j)+9)
        for k in range(lower, upper+1):
            a, b = (k << j)-15449, (1 << (128-j))-k
            trials += 1
            decoded = decode_rational(a, b, 1024-j)
            if decoded is None:
                continue
            tail, h = decoded
            s = "1"*j+tail
            G = word_matrix(s, (C, D), None)
            require((G[0]+G[1], G[2]+G[3]) == (2**h*a, 2**h*(b << j)),
                    "Integer endpoint reconstruction")
            require(a+(b << j) == PRIME, "Endpoint sum is not p")
            require(sum(G) % PRIME == 0, "Bridge condition")
            t = (G[0]+G[1]) % PRIME
            rho = t*t*pow(pow(2, len(s), PRIME), -1, PRIME) % PRIME
            record = {"prime": str(PRIME), "bridge_bits": s, "rho": str(rho),
                      "j": j, "k": k, "r": r, "scale_exponent": h,
                      "trials": trials, "bridge_length_bits": len(s)}
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(record, indent=2)+"\n")
            print(f"Verified bridge: {len(s)} bits, {trials} candidates; {args.output}")
            return
    raise SystemExit("No bridge in the requested bounded search")


if __name__ == "__main__":
    main()
