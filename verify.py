#!/usr/bin/env python3
"""Verify both fixed witnesses, optionally using the official C implementations."""

import argparse
import ctypes
import hashlib
import json
import platform
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from zipfile import ZipFile

from model import (
    PRIME, I, A, B, C, D, P, P_INV, require, multiply, power, inverse,
    word_matrix, segments_matrix, bit_length, pack, digest, mutate_first_bit,
)

ROOT = Path(__file__).resolve().parent


def load_case(name, data_dir=ROOT/"data"):
    cert = json.loads((data_dir/f"{name}_collision.json").read_text())
    require(int(cert["prime"]) == PRIME, "Not the official CHAMP-512 prime")
    require(cert["generators"] == {"0": [[-2, 1], [4, -3]],
                                   "1": [[-5, 2], [-6, 2]]}, "Wrong generators")
    if name == "short":
        s = cert["bridge_bits"]
        bridge = word_matrix(s, (C, D))
        require(sum(bridge) % PRIME == 0, "Bridge does not preserve the required line")
        t = (bridge[0]+bridge[1]) % PRIME
        require(t != 0, "Zero line eigenvalue")
        rho = t*t*pow(pow(2, len(s), PRIME), -1, PRIME) % PRIME
        require(rho == int(cert["rho"]), "Incorrect rho")
        x, y = "011011", "101101"
        X, Y, N = (3, 4, 2, 3), (3, 2, 4, 3), (1, -1, 1, -1)
        require(multiply(N, N) == (0, 0, 0, 0), "N is not nilpotent")
        require(word_matrix(x, (C, D)) == tuple(8*z for z in X), "Switch x")
        require(word_matrix(y, (C, D)) == tuple(8*z for z in Y), "Switch y")
        unipotent = tuple((I[k]+6*N[k]) % PRIME for k in range(4))
        require(tuple(-z % PRIME for z in multiply(unipotent, Y)) == X,
                "Incorrect switch identity")
        M = multiply(Y, bridge)
        require(multiply(multiply(M, N), inverse(M)) ==
                tuple(rho*z % PRIME for z in N), "Conjugation identity")
        coeff = cert["coefficients"]
        require(len(coeff) == cert["block_count"], "Wrong block count")
        require(all(z in (-1, 0, 1) for z in coeff) and any(coeff), "Bad coefficients")
        weighted, weight = 0, 1
        for z in coeff:
            weighted = (weighted+z*weight) % PRIME
            weight = weight*rho % PRIME
        require(weighted == 0, "Weighted relation does not vanish")
        require(sum(z == 1 for z in coeff) % 2 == sum(z == -1 for z in coeff) % 2,
                "Scalar parity mismatch")
        require(cert["block_prefixes"] == [y, x], "Incorrect block prefixes")
        blocks = (y+s, x+s)
        messages = [
            ["".join(blocks[int(z == sign)] for z in coeff)] for sign in (1, -1)
        ]
    else:
        w, j, h = cert["decoded_word"], cert["j"], cert["scale_exponent"]
        denominator = int(cert["denominator"])
        require(denominator == (cert["sign"]*pow(2, -j, PRIME)) % PRIME
                + cert["lift"]*PRIME, "Incorrect lifted denominator")
        a, b, c, d = word_matrix(w, (C, D), None)
        require((a+b, c+d) == (2**h*PRIME, 2**h*denominator),
                "Incorrect exact integer endpoint")
        r = len(w)+1-2*h+2*j
        require(r >= 0 and r == cert["append_ones"], "Incorrect diagonal adjustment")
        prefix = w+"0"
        require(len(prefix)+r == cert["shear_length_bits"], "Incorrect shear length")
        S = multiply(word_matrix(prefix, (C, D)), power(D, r))
        require(S[1] == 0 and S[0] == S[3] and S[0] != 0, "Not a scalar lower shear")
        require(multiply(multiply(power(S, 2), power(D, 2)), S) ==
                multiply(multiply(D, power(S, 3)), D), "Shear identity")
        messages = [
            [prefix, r, prefix, r, 2, prefix, r],
            [1, prefix, r, prefix, r, prefix, r, 1],
        ]
    require(all(bit_length(m) == cert["bit_length"] for m in messages),
            "Incorrect meaningful message length")
    return cert, messages


def compile_official(archive, directory, compiler):
    pins = json.loads((ROOT/"data/official_sources.json").read_text())
    require(hashlib.sha256(archive.read_bytes()).hexdigest() == pins["archive_sha256"],
            "Official ZIP checksum mismatch")
    require(platform.system() in ("Darwin", "Linux"),
            "Automatic C build supports macOS and Linux; the Python model is portable")
    libraries, sources = {}, {}
    with ZipFile(archive) as zipped:
        for family, info in pins["sources"].items():
            member = info["source"].removeprefix("vendor/")
            contents = zipped.read(member)
            require(hashlib.sha256(contents).hexdigest() == info["source_sha256"],
                    f"{family} source checksum mismatch")
            build = directory/family.lower()
            build.mkdir()
            source = build/"CryptHash_AlgorithmInstance.c"
            source.write_bytes(contents)
            header_member = member.rsplit("/", 1)[0]+"/CryptHash_AlgorithmInstance.h"
            header = zipped.read(header_member)
            (build/"CryptHash_AlgorithmInstance.h").write_bytes(header)
            library = build/f"{family.lower()}.so"
            flags = ["-dynamiclib"] if platform.system() == "Darwin" else ["-shared", "-fPIC"]
            compiled = subprocess.run(
                [compiler, "-std=c99", "-O3", "-DNDEBUG", *flags,
                 str(source), "-o", str(library)], capture_output=True, text=True)
            require(compiled.returncode == 0, f"{family} C compilation failed:\n{compiled.stderr}")
            libraries[family] = ctypes.CDLL(str(library))
            sources[family] = {"archive_member": member, "sha256": info["source_sha256"],
                               "header_sha256": hashlib.sha256(header).hexdigest()}
    return libraries, {"archive_sha256": pins["archive_sha256"], "sources": sources}


def official_hash(library, data, nbits):
    function = library.CryptHash
    function.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_ulonglong, ctypes.c_void_p]
    function.restype = ctypes.c_int
    message = (ctypes.c_ubyte*len(data)).from_buffer(data)
    out = (ctypes.c_ubyte*80)(*([0xa5]*80))
    started = time.perf_counter()
    code = function(512, message, nbits, out)
    elapsed = time.perf_counter()-started
    require(code == 0, f"Official implementation returned {code}")
    require(bytes(out[64:]) == b"\xa5"*16, "Output guard modified")
    return bytes(out[:64]), elapsed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--official-zip", type=Path)
    parser.add_argument("--cc", default=shutil.which("clang") or shutil.which("cc"))
    parser.add_argument("--only", choices=("short", "long", "all"), default="all")
    parser.add_argument("--certificate-dir", type=Path, default=ROOT/"data")
    parser.add_argument("--materialize", type=Path,
                        help="Optional output directory for exact packed messages")
    parser.add_argument("--report", type=Path, default=ROOT/"generated/verification.json")
    args = parser.parse_args()
    report = {"instance": "CHAMP-512", "prime": str(PRIME),
              "python": platform.python_version(), "system": platform.system(),
              "matrix_checks_passed": False, "official_C_checks_performed": False,
              "cases": []}
    for original, transformed in ((A, C), (B, D)):
        require(multiply(multiply(P_INV, original), P) ==
                tuple(-z % PRIME for z in transformed), "Change of basis")
    with tempfile.TemporaryDirectory(prefix="champ512-verify-") as scratch:
        libraries = {}
        if args.official_zip:
            require(args.cc is not None, "C compiler not found")
            libraries, report["official_sources"] = compile_official(
                args.official_zip, Path(scratch), args.cc)
        names = ("short", "long") if args.only == "all" else (args.only,)
        for name in names:
            cert, messages = load_case(name, args.certificate_dir)
            matrices = [segments_matrix(m) for m in messages]
            require(matrices[0] == matrices[1], f"{name}: original matrices differ")
            expected = digest(matrices[0])
            require(expected.hex() == cert["digest_hex"], f"{name}: digest mismatch")
            row = {"method": name, "meaningful_bits": cert["bit_length"],
                   "packed_bytes": cert["packed_bytes"], "digest_hex": expected.hex(),
                   "matrix_original_A_B": [str(x) for x in matrices[0]], "messages": []}
            first_data = None
            for index, (segments, info) in enumerate(zip(messages, cert["messages"])):
                data = pack(segments)
                require(len(data) == cert["packed_bytes"], "Packed size mismatch")
                sha = hashlib.sha256(data).hexdigest()
                require(sha == info["sha256"], f"{name}: file SHA-256 mismatch")
                if index == 0:
                    first_data = data
                else:
                    require(data != first_data, "Messages are identical")
                stored = args.certificate_dir.parent/"messages"/info["file"]
                if stored.exists():
                    require(stored.read_bytes() == data, "Included file differs from certificate")
                if args.materialize:
                    args.materialize.mkdir(parents=True, exist_ok=True)
                    target = args.materialize/info["file"]
                    if target.exists():
                        require(hashlib.sha256(target.read_bytes()).hexdigest() == sha,
                                f"Refusing to overwrite a different file: {target}")
                    else:
                        target.write_bytes(data)
                entry = {"file": info["file"], "sha256": sha, "official_checks": {}}
                for family, library in libraries.items():
                    observed, seconds = official_hash(library, data, cert["bit_length"])
                    require(observed == expected, f"{family}: digest mismatch")
                    entry["official_checks"][family] = {"digest_hex": observed.hex(),
                                                       "verification_seconds": seconds}
                if index == 0:
                    mutated = digest(segments_matrix(mutate_first_bit(segments)))
                    require(mutated != expected, "Model failed the first-bit mutation control")
                    controls = {"model_passed": True, "official_checks": {}}
                    data[0] ^= 0x80
                    try:
                        for family, library in libraries.items():
                            observed, seconds = official_hash(library, data, cert["bit_length"])
                            require(observed == mutated and observed != expected,
                                    f"{family}: mutation control failed")
                            controls["official_checks"][family] = {
                                "passed": True, "verification_seconds": seconds}
                    finally:
                        data[0] ^= 0x80
                    row["first_bit_mutation_control"] = controls
                row["messages"].append(entry)
                print(f"{name}/{info['file']}: exact bytes and digest verified", flush=True)
            row["messages_distinct_within_declared_length"] = True
            report["cases"].append(row)
            first_data = None
        report["matrix_checks_passed"] = True
        report["official_C_checks_performed"] = bool(libraries)
        report["all_requested_checks_passed"] = True
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2)+"\n")
    print(f"All requested checks passed. Report: {args.report}", flush=True)


if __name__ == "__main__":
    main()
