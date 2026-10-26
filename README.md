# Two full CHAMP-512 collisions

**Sunan Wang**  
Symmetric Cryptography Laboratory, Shandong University  
Contact: sunan.wang@mail.sdu.edu.cn

This package contains two distinct-message collision pairs for the submitted CHAMP-512 construction at its official prime

`p = 2^128 - 15449 = 340282366920938463463374607431768196007`.

Both pairs collide in the complete 64-byte digest. The original matrix products also agree, so the result is independent of an accidental collision introduced by the output encoding. Each pair has equal message lengths and uses ordinary binary inputs.

| Pair | Meaningful bits per message | Bytes per file | Construction |
| --- | ---: | ---: | --- |
| Short | 334,400 | 41,800 | A 269-bit bridge and a 64-list weighted-sum relation |
| Long | 427,262,006 | 53,407,751 | Directed integer lifting and a scalar lower-shear identity |

The four complete inputs are [short_a.bin](messages/short_a.bin), [short_b.bin](messages/short_b.bin), [long_a.bin](messages/long_a.bin), and [long_b.bin](messages/long_b.bin). They can be used directly; reconstruction is optional. [message_manifest.json](message_manifest.json) records the effective input lengths, file sizes, SHA-256 values, and expected CHAMP-512 digests. [messages/README.md](messages/README.md) explains the file format.

Each message in our second collision pair is 427,262,006 bits long, and the reported digest is for these two messages. Since this length is not a multiple of eight, the binary files are generated with trailing zero bits to complete the final byte. The zero-padded messages still form a collision pair, but their common digest differs from the one reported here. Reproducing the reported result therefore requires explicitly passing an input length of 427,262,006 bits to the hash interface.

For a step-by-step procedure that compiles the official C sources into standalone file-hashing programs, see [VERIFY_OFFICIAL.md](VERIFY_OFFICIAL.md). It covers both message pairs without using the Python model for hash computation.

## Repository contents

| Path | Contents |
| --- | --- |
| `messages/` | All four complete binary input files and their format description |
| `message_manifest.json` | Input lengths, file sizes, expected CHAMP-512 digests, and file SHA-256 values |
| [METHODS.md](METHODS.md) | Derivations of both constructions and references to related work |
| [VERIFY_OFFICIAL.md](VERIFY_OFFICIAL.md) | Direct verification using the unchanged submitted C implementations |
| `data/` | Compact construction certificates and pinned official-source checksums |
| `model.py`, `verify.py` | Standard-library Python model and certificate verifier |
| `tools/` | Bridge search, relation search, directed-lift search, message expansion, and C file adapter |
| `verification/` | Recorded construction replay and official C verification results |
| `SHA256SUMS` | Checksums for the distributed repository files, excluding this checksum file itself |

## Verify the saved collisions

Requirements: Python 3.9 or later, with no third-party Python packages. Run from this directory:

```sh
python3 -B verify.py
```

This verifies the algebraic certificates, equality of the original A/B matrix products, the complete digest, the exact packed-message SHA-256 values, message distinctness, and a control that changes the first meaningful bit. It reconstructs both long messages in memory, without writing them to disk. All four complete binary message files are included under `messages/` and compared byte for byte. This command uses the included model; it does not run the submitters' C implementations.

For independent checks against both submitted C implementations, download the official archive without modifying it:

```sh
mkdir -p generated
curl --fail --location 'https://www.niccs.org.cn/niccs/Proposal/Cryptographic%20Hash%20Algorithms/Round%201%20candidates/CHAMP.zip' --output generated/CHAMP.zip
python3 -B verify.py --official-zip generated/CHAMP.zip
```

The C build requires Clang or another compatible C compiler on macOS or Linux. The verifier checks the archive and C source hashes before compiling. The expected archive SHA-256 is:

```text
8953f95618236d8d86191992b10e3580ae74520c28a36a715c2fc8bea2a9e8c1
```

The saved result in `verification/verified_with_official_C.json` records successful checks of both pairs with the reference and optimized implementations, including the changed-bit controls. A fresh run writes `generated/verification.json`.

All four messages are already available in `messages/`. To independently reconstruct another copy from the construction data:

```sh
python3 -B verify.py --materialize generated/messages
```

The two long files occupy about 106.8 MB together after extraction. They contain long repeated runs and therefore compress well in the ZIP archive. Compact construction data are also included. Verification allocates additional memory for buffers and the C interface.

## Reproduce the construction

Verifying a saved witness and searching for a witness are separate operations. [METHODS.md](METHODS.md) gives the identities and the certificate interpretation.

### Short pair

The following commands find the bridge, generate the field weights, search for a relation, expand it into full messages, and verify the result. A C++17 compiler with 128-bit integer support is required for the search.

```sh
mkdir -p generated
python3 -B tools/find_bridge.py --output generated/bridge.json
python3 -B tools/prepare_search_input.py --bridge generated/bridge.json --output generated/search_input.txt
c++ -O3 -std=c++17 tools/multilist_search.cpp -o generated/multilist_search
generated/multilist_search generated/search_input.txt generated/relation.json 2026101407
python3 -B tools/expand_relation.py --bridge generated/bridge.json --relation generated/relation.json --output generated/replayed
python3 -B verify.py --only short --certificate-dir generated/replayed/data --report generated/replayed_verification.json
```

To verify a newly expanded pair with the official implementations, append `--official-zip generated/CHAMP.zip` to the final command. The output directory passed to `expand_relation.py` must be new.

The search uses 64 groups, 19 positions per group and leaf lists with up to `2^19 - 1` nonempty subset sums. A search can return no relation for a seed. In that case use another seed and rerun the search. The fixed seed above reproduced the distributed coefficients on the tested macOS Clang/libc++ environment; `std::shuffle` is not specified identically across C++ standard libraries. Certificate verification does not depend on a seed or shuffle implementation. `verification/search_replay.json` records the local replay.

### Long pair

```sh
python3 -B tools/search_direct_lift.py --start-j 71210188 --stop-j 71210188 --output generated/direct_lift_hit.json
python3 -B verify.py --only long --materialize generated/long_messages --report generated/long_verification.json
```

The first command replays the saved successful endpoint. It is not a search from the beginning, or a measurement of the original discovery cost. The second command checks and expands the distributed long certificate; compare the hit's `j`, `sign`, `lift`, `denominator`, `decoded_word`, `scale_exponent`, `append_ones`, and `message_bits` with `data/long_collision.json` (`bit_length` there). The included Python scanner is a bounded reference implementation, not the historical optimized scanner.

## Digest values

Short pair:

```text
571fecc332116f68581aa805285a92c52d57a908eca17d83f5ed59d1629c751137a0dc498f73881e2bdb8533f24a63379b2a75d8cd23ab7aff47e37cb89f7c80
```

Long pair:

```text
000b22e782f26fc7661ba1f86860ebd5696196f41a938e73aebbf1c1a0b08c6d0abbdc034608630f3328e87a6867851083654aa2e843cae3560dcbed2c4bca93
```

Message SHA-256 values identify the exact files, rather than serving as the CHAMP collision criterion; they are in `data/short_collision.json` and `data/long_collision.json`. `SHA256SUMS` covers the distributed package files other than itself.

## Scope and related work

These are explicit full-parameter CHAMP-512 collision witnesses and reproducible constructions.

CHAMP already has public work on determinant constraints, palindromes, matrix subgroups, commuting products, and integer lifting. The positive-generator viewpoint and subgroup route should be read in that context. The contribution documented here is the two concrete constructions and their verified full-parameter witnesses; it does not assign novelty to every ingredient. References and the relationship to the constructions appear in [METHODS.md](METHODS.md).

The submitters' implementation sources are not redistributed. Their public archive is fetched separately and identified by checksums in `data/official_sources.json`. This prepared package does not yet specify an open-source license; public availability alone should not be described as an open-source license grant.
