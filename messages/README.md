# Complete CHAMP-512 collision messages

All four files contain the complete binary messages. They are ordinary binary inputs and can be passed directly to the submitted CHAMP-512 implementations. No message-generation program is required.

| File | Meaningful input bits | File bytes | Unused low bits in final byte |
| --- | ---: | ---: | ---: |
| [short_a.bin](short_a.bin) | 334,400 | 41,800 | 0 |
| [short_b.bin](short_b.bin) | 334,400 | 41,800 | 0 |
| [long_a.bin](long_a.bin) | 427,262,006 | 53,407,751 | 2 |
| [long_b.bin](long_b.bin) | 427,262,006 | 53,407,751 | 2 |

Bits are packed most significant bit first within each byte. The two unused low bits in the last byte of each long file are zero. Pass **427262006**, in bits, as the input length for the reported long collision.

The file sizes total 106,899,102 bytes. Long repeated runs make the files highly compressible without losing any input data.

## Expected full digests

`short_a.bin` and `short_b.bin`, each hashed at 334,400 bits:

```text
571fecc332116f68581aa805285a92c52d57a908eca17d83f5ed59d1629c751137a0dc498f73881e2bdb8533f24a63379b2a75d8cd23ab7aff47e37cb89f7c80
```

`long_a.bin` and `long_b.bin`, each hashed at 427,262,006 bits:

```text
000b22e782f26fc7661ba1f86860ebd5696196f41a938e73aebbf1c1a0b08c6d0abbdc034608630f3328e87a6867851083654aa2e843cae3560dcbed2c4bca93
```

Hashing the complete long files at 427,262,008 bits includes the two trailing zero bits. Those byte-aligned messages also collide, with the following different common digest:

```text
4c90d93b2edb83eb1b0567c2ed5594c4ca7570be2e1dfd88ed5ddeb7cbd1f8171b77b216b31827f650fba3df7f1df3a8a6f82519b147cbf24e62c1567c525456
```

## File integrity

| File | SHA-256 of the complete packed file |
| --- | --- |
| `short_a.bin` | `34bb30a62e04298b5d97cd608840afdb7084b2c0f848a90d4b5ff99a546dd805` |
| `short_b.bin` | `fd34962528513e9044880943b106b81188ff0526b1c7d7bbbb987505ef42c822` |
| `long_a.bin` | `134d03ca44c6507b708edae44765fc17fb6efe2e901244d2bce954fcb1d23b23` |
| `long_b.bin` | `02248d2c3e398c13e65c678f084ed220f88399c9a6ee4abe58d784ced5b3e82e` |

These SHA-256 values identify the files. The collision criterion is equality of the complete CHAMP-512 digests at the stated input lengths.

See [message_manifest.json](../message_manifest.json) for machine-readable metadata, [VERIFY_OFFICIAL.md](../VERIFY_OFFICIAL.md) for direct C verification, and [METHODS.md](../METHODS.md) for the constructions.
