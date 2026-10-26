# Verify both collisions with the submitted C implementations

Compile the original CHAMP-512 reference and optimized implementations, hash the supplied binary files, and compare the complete digests. Start with the 41,800-byte short pair, then verify the 53,407,751-byte long pair.

The hash computation is performed by the original C sources from the official archive. The supplied `tools/hash_file.c` adapter only reads a file, accepts its meaningful bit length, calls `CryptHash(512, data, nbits, output)`, and prints 64 output bytes. It contains no CHAMP algorithm, matrix operations, construction certificates, or expected digests. This procedure does not use `verify.py` or `model.py` to calculate the hashes.

## 1. Requirements and working directory

The commands work on macOS and Linux. A C compiler, Python 3.9 or later, and unzip are required. Check the tools:

```sh
cc --version
python3 --version
unzip -v
```

On macOS, install the command-line developer tools with `xcode-select --install` if a compiler is unavailable.

Change to the repository root, replacing the example path:

```sh
cd "/path/to/champ512-collisions"
mkdir -p generated/official
```

Run all subsequent commands from this directory. The four complete messages are already in `messages/`.

## 2. Obtain and identify the official implementation

Download the original archive:

```sh
curl --fail --location 'https://www.niccs.org.cn/niccs/Proposal/Cryptographic%20Hash%20Algorithms/Round%201%20candidates/CHAMP.zip' --output generated/CHAMP.zip
```

Alternatively, copy an existing official archive, replacing the example path:

```sh
cp "/path/to/CHAMP.zip" generated/CHAMP.zip
```

Check its SHA-256:

```sh
python3 -B - <<'PY'
from pathlib import Path
import hashlib
actual = hashlib.sha256(Path('generated/CHAMP.zip').read_bytes()).hexdigest()
print(actual)
assert actual == '8953f95618236d8d86191992b10e3580ae74520c28a36a715c2fc8bea2a9e8c1', 'Official archive version mismatch'
print('Official archive checksum verified')
PY
```

Extract the archive and set the two source-directory variables. Keep the quotes because the paths contain spaces:

```sh
unzip -q -o generated/CHAMP.zip -d generated/official
champ_ref_dir="generated/official/CHAMP/Implementations and Test_Vectors/API_CryptHash/Implementations/Reference_Implementation/CHAMP-512"
champ_opt_dir="generated/official/CHAMP/Implementations and Test_Vectors/API_CryptHash/Implementations/Optimized_Implementation/CHAMP-512"
```

Both directories contain `CryptHash_AlgorithmInstance.c` and `CryptHash_AlgorithmInstance.h`. Use those files unchanged. The C source checksums are:

| Implementation | SHA-256 of `CryptHash_AlgorithmInstance.c` |
| --- | --- |
| Reference | `4e0aea74105cc7f519ed89f0c746ec69c37fd7c1833fbfaeb62f71a2b6b1fa9e` |
| Optimized | `5395ee52a5b9b602caff51b85ebdb7a3b28b979d996f8e2e7942d101e0078420` |

## 3. Compile the file-hashing programs

Reference implementation:

```sh
cc -std=c99 -O2 -I "$champ_ref_dir" tools/hash_file.c "$champ_ref_dir/CryptHash_AlgorithmInstance.c" -o generated/champ512_reference
```

Optimized implementation:

```sh
cc -std=c99 -O2 -I "$champ_opt_dir" tools/hash_file.c "$champ_opt_dir/CryptHash_AlgorithmInstance.c" -o generated/champ512_optimized
```

Each program accepts `FILE MEANINGFUL_BITS` and prints 128 hexadecimal characters, representing the complete 512-bit digest. The adapter checks that the file size equals the bit length rounded up to whole bytes.

## 4. Verify the short pair

Each short message has 334,400 meaningful bits and occupies 41,800 bytes. Check the file sizes, distinctness, and SHA-256 values:

```sh
python3 -B - <<'PY'
from pathlib import Path
import hashlib
a = Path('messages/short_a.bin').read_bytes()
b = Path('messages/short_b.bin').read_bytes()
assert len(a) == len(b) == 41800
assert a != b, 'The two messages are identical'
expected = [
    '34bb30a62e04298b5d97cd608840afdb7084b2c0f848a90d4b5ff99a546dd805',
    'fd34962528513e9044880943b106b81188ff0526b1c7d7bbbb987505ef42c822',
]
for label, data, sha in zip(('short_a', 'short_b'), (a, b), expected):
    actual = hashlib.sha256(data).hexdigest()
    print(label, len(data), actual)
    assert actual == sha
print('Short files verified: equal lengths and different contents')
PY
```

SHA-256 identifies the files. The following calls to the official CHAMP implementations verify the collision:

```sh
./generated/champ512_reference messages/short_a.bin 334400 > generated/short_a.ref.hex
./generated/champ512_reference messages/short_b.bin 334400 > generated/short_b.ref.hex
./generated/champ512_optimized messages/short_a.bin 334400 > generated/short_a.opt.hex
./generated/champ512_optimized messages/short_b.bin 334400 > generated/short_b.opt.hex
cat generated/short_a.ref.hex generated/short_b.ref.hex generated/short_a.opt.hex generated/short_b.opt.hex
```

All four lines should be identical:

```text
571fecc332116f68581aa805285a92c52d57a908eca17d83f5ed59d1629c751137a0dc498f73881e2bdb8533f24a63379b2a75d8cd23ab7aff47e37cb89f7c80
```

Compare them automatically:

```sh
python3 -B - <<'PY'
from pathlib import Path
names = ['short_a.ref', 'short_b.ref', 'short_a.opt', 'short_b.opt']
values = [Path('generated/' + name + '.hex').read_text().strip() for name in names]
expected = '571fecc332116f68581aa805285a92c52d57a908eca17d83f5ed59d1629c751137a0dc498f73881e2bdb8533f24a63379b2a75d8cd23ab7aff47e37cb89f7c80'
assert all(value == expected for value in values), 'Short digest mismatch: check the files, bit length, and implementation version'
print('Full short collision verified with both official implementations')
PY
```

## 5. Optional changed-bit control

Change the first meaningful bit of `short_a.bin` and hash the changed message with both programs:

```sh
python3 -B - <<'PY'
from pathlib import Path
data = bytearray(Path('messages/short_a.bin').read_bytes())
data[0] ^= 0x80
Path('generated/short_a_changed.bin').write_bytes(data)
PY
./generated/champ512_reference generated/short_a_changed.bin 334400 > generated/short_a_changed.ref.hex
./generated/champ512_optimized generated/short_a_changed.bin 334400 > generated/short_a_changed.opt.hex
python3 -B - <<'PY'
from pathlib import Path
original = Path('generated/short_a.ref.hex').read_text().strip()
reference = Path('generated/short_a_changed.ref.hex').read_text().strip()
optimized = Path('generated/short_a_changed.opt.hex').read_text().strip()
assert reference == optimized and reference != original
print('Changing an input bit changes the digest; both implementations agree')
print(reference)
PY
```

## 6. Verify the long pair

The complete long files are already in `messages/`. Each has **427,262,006 meaningful bits**, packed into **53,407,751 bytes**. Check their sizes, file checksums, and distinctness within the declared input length:

```sh
python3 -B - <<'PY'
from pathlib import Path
import hashlib
a = Path('messages/long_a.bin').read_bytes()
b = Path('messages/long_b.bin').read_bytes()
assert len(a) == len(b) == 53407751
assert a != b
# Compare meaningful bits, excluding the two unused low bits.
assert a[:-1] != b[:-1] or (a[-1] & 0xfc) != (b[-1] & 0xfc)
assert (a[-1] & 3) == (b[-1] & 3) == 0
expected = [
    '134d03ca44c6507b708edae44765fc17fb6efe2e901244d2bce954fcb1d23b23',
    '02248d2c3e398c13e65c678f084ed220f88399c9a6ee4abe58d784ced5b3e82e',
]
for label, data, sha in zip(('long_a', 'long_b'), (a, b), expected):
    actual = hashlib.sha256(data).hexdigest()
    print(label, len(data), actual)
    assert actual == sha
print('Long files verified and distinct within the meaningful input bits')
PY
```

The reported digest uses 427,262,006 bits. Each packed file ends with two zero bits that complete the last byte. Including those bits gives a 427,262,008-bit message: the padded pair still collides, but with a different common digest. Pass the exact original length to reproduce the reported result:

```sh
./generated/champ512_reference messages/long_a.bin 427262006 > generated/long_a.ref.hex
./generated/champ512_reference messages/long_b.bin 427262006 > generated/long_b.ref.hex
./generated/champ512_optimized messages/long_a.bin 427262006 > generated/long_a.opt.hex
./generated/champ512_optimized messages/long_b.bin 427262006 > generated/long_b.opt.hex
cat generated/long_a.ref.hex generated/long_b.ref.hex generated/long_a.opt.hex generated/long_b.opt.hex
```

All four lines should equal:

```text
000b22e782f26fc7661ba1f86860ebd5696196f41a938e73aebbf1c1a0b08c6d0abbdc034608630f3328e87a6867851083654aa2e843cae3560dcbed2c4bca93
```

Compare them automatically:

```sh
python3 -B - <<'PY'
from pathlib import Path
names = ['long_a.ref', 'long_b.ref', 'long_a.opt', 'long_b.opt']
values = [Path('generated/' + name + '.hex').read_text().strip() for name in names]
expected = '000b22e782f26fc7661ba1f86860ebd5696196f41a938e73aebbf1c1a0b08c6d0abbdc034608630f3328e87a6867851083654aa2e843cae3560dcbed2c4bca93'
assert all(value == expected for value in values), 'Long digest mismatch'
print('Full long collision verified with both official implementations')
PY
```

The expected digest for the byte-aligned padded pair is listed in [messages/README.md](messages/README.md).

## 7. Troubleshooting

- Header not found: run from the repository root and set `champ_ref_dir` and `champ_opt_dir` again. Shell variables do not survive opening a new terminal.
- File-size mismatch: use `334400` for the short files and `427262006` for the long files. Both values are in bits.
- Unexpected long digest: check the meaningful bit length and file SHA-256 values, then confirm that the source is from the official CHAMP-512 directory.
- Equal output alone is insufficient: also confirm different meaningful inputs, the exact input length, and the pinned official source archive.

Sunan Wang  
Symmetric Cryptography Laboratory, Shandong University  
sunan.wang@mail.sdu.edu.cn
