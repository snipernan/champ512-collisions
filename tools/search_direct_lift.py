#!/usr/bin/env python3
"""Bounded reference search for the directed-lift family.

Python prioritizes clarity here. This is not the historical optimized scanner.
Use --start-j 71210188 --stop-j 71210188 to replay the saved hit immediately.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from model import PRIME, decode_rational, require


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-j", type=int, default=0)
    parser.add_argument("--stop-j", type=int, default=1000)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(0 <= args.start_j <= args.stop_j, "Invalid index range")
    residue = pow(2, -args.start_j, PRIME)
    for j in range(args.start_j, args.stop_j+1):
        for sign in (1, -1):
            base = (sign*residue) % PRIME
            for lift in (0, 1):
                d = base+lift*PRIME
                found = decode_rational(PRIME, d)
                if found is None:
                    continue
                w, h = found
                r = len(w)+1-2*h+2*j
                if r < 0:
                    continue
                result = {"prime": str(PRIME), "j": j, "sign": sign, "lift": lift,
                          "denominator": str(d), "decoded_word": w,
                          "scale_exponent": h, "append_ones": r,
                          "message_bits": 3*(len(w)+1+r)+2}
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps(result, indent=2)+"\n")
                print(f"Found directed-lift endpoint at j={j}; {args.output}")
                return
        residue = residue//2 if residue % 2 == 0 else (residue+PRIME)//2
    raise SystemExit("No directed-lift endpoint in this bounded interval")


if __name__ == "__main__":
    main()
