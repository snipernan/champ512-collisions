# Construction of two full CHAMP-512 collisions

## Model and output convention

All modular identities below use the official prime `p = 2^128 - 15449`. For a bitstring `w`, let `H(w)` be the left-to-right product of the submitted generators

```text
A = [-2  1]       B = [-5  2]
    [ 4 -3]           [-6  2].
```

The empty word has product I. Concatenation corresponds to matrix multiplication in the same order. For an original product `[[a,b],[c,d]]`, the submitted C implementations invert each nonzero entry modulo p, encode zero as zero, and serialize entries in order `a,c,b,d`, using 16 little-endian bytes per entry. The witnesses below have equal original products, before this encoding.

Use the invertible integer change of basis

```text
P = [1 -2]       P^-1 = [-3  2]
    [2 -3]              [-2  1].

P^-1 A P = -C,   C = [4 1]
                     [2 1]

P^-1 B P = -D,   D = [1 0]
                     [0 2].
```

Write `G(w)` for the product using C and D. Thus `H(w) = (-1)^|w| P G(w) P^-1`. Equal-length collisions in G give exact collisions in H, including the scalar sign.

## Short collision from a bridge and a weighted relation

Let `x = 011011`, `y = 101101`, and define

```text
G(x) = 8X,       X = [3 4]
                     [2 3]

G(y) = 8Y,       Y = [3 2]
                     [4 3]

N = [1 -1],      N^2 = 0,      U(z) = I + zN.
    [1 -1]
```

Direct integer multiplication gives `X = -U(6)Y`. The line spanned by `v = (1,1)^T` is both the kernel and image of N.

Choose a bridge word s such that the sum of the four entries of `G(s)` is zero modulo p. If `G(s) = [[a,b],[c,d]]`, set `t = a+b` and `M = YG(s)`. Then `G(s)v = t(1,-1)^T` and `Y(1,-1)^T = v`, so `Mv = tv`. Invertibility implies `t != 0`. Since `det Y = 1` and `det G(s) = 2^|s|`,

```text
M N M^-1 = rho N,       rho = t^2 / 2^|s| mod p.
```

This follows by comparing M's eigenvalue t on the line with its eigenvalue `2^|s|/t` on the one-dimensional quotient. It also follows from direct multiplication, which the verifier checks.

Define equal-length blocks `b0 = ys` and `b1 = xs`. Their products are `8M` and `-8U(6)M`. For a sequence of choices `epsilon_0,...,epsilon_(m-1)` concatenated from left to right,

```text
G(b_epsilon_0 ... b_epsilon_(m-1))
  = 8^m (-1)^sum(epsilon_i)
    U(6 sum(epsilon_i rho^i)) M^m.
```

The identity follows by moving each U factor to the left using conjugation by M. Two different binary choice sequences therefore collide exactly when their weighted sums agree modulo p and their Hamming weights have the same parity. The parity condition preserves the full scalar, rather than merely producing equality of projective matrices.

The distributed bridge has 269 bits. It is found by the following bounded integer construction, implemented in `tools/find_bridge.py`. For `j = 64-r`, consider positive integers

```text
alpha = k 2^j - 15449,
beta  = 2^(128-j) - k,
alpha + 2^j beta = p.
```

The reference rational decoder attempts to find a word u and an exponent h with `G(u)v = 2^h(alpha,beta)^T`. On success, the bridge `s = 1^j u` satisfies `G(s)v = 2^h(alpha,2^j beta)^T`, whose coordinate sum is a multiple of p. Every successful endpoint is checked by exact integer multiplication. The saved search returns `r = 7`, `j = 57`, `k = 20499`, `h = 128` after 30,325 candidate pairs. Its field weight is

```text
rho = 5670903413253385409477775768128925117.
```

The 64-list search partitions 1,216 positions into 64 groups of 19. Each leaf enumerates its nonempty subset sums. Half the groups have positive sign and half have negative sign. A generalized birthday merge retains sums in progressively smaller centered integer intervals, then matches an exact zero and equal parity at the root. The result is a nonzero vector `z_i in {-1,0,1}` with

```text
sum(z_i rho^i) = 0 mod p,
number of +1 entries = number of -1 entries mod 2.
```

The certificate has 311 positive, 293 negative, and 612 zero coefficients. Use `epsilon_i = 1` exactly when `z_i = 1`, and `eta_i = 1` exactly when `z_i = -1`. The two products coincide. Distinct blocks and a nonzero coefficient vector make the messages distinct. Each message contains `1216 * (269 + 6) = 334400` bits, or 41,800 bytes.

The list search is a concrete generalized birthday implementation in the tradition of Wagner's algorithm [6]. Its behavior for this structured sequence of weights is an empirical construction result here; no general random-list distribution theorem or asymptotic running-time claim is asserted.

## Long collision from a directed integer lift

The saved rational decoding endpoint is an exact integer identity

```text
G(w) v = 2^h (p,d)^T,
d = (-2^-j mod p) + p,
j = 71210188,
h = 232,
|w| = 377,
d = 552084908677899503626868810117526858734.
```

The decoder works backward on a positive coprime pair `(n,d)`. If `n<d`, it removes a leading D step, dividing d by two when even, or replacing `(n,d)` by `(2n,d)` and increasing h when d is odd. Otherwise it attempts a leading C step, replacing the pair by `(n-d,4d-2n)`, dividing the pair by two when possible and otherwise increasing h. The implementation rejects that branch when `5n >= 9d` and has a finite step cap. Success terminates at `(1,1)`. The cap and rejection rule define a bounded search; they are not a completeness assertion about all positive rationals. The exact endpoint identity, rather than decoder success alone, is checked in `verify.py`.

The word `w0` has product `T = G(w)C`. Its upper-right entry is zero modulo p because the first coordinate of `G(w)v` is `2^h p`. Its lower-right entry is `2^h d`. Since `det T = 2^(|w|+1)` and `d^2 = 2^(-2j) mod p`, the diagonal ratio of T is

```text
T_00 / T_11 = 2^(|w|+1-2h+2j) mod p.
```

Set `r = |w|+1-2h+2j = 142420290` and `s = w0 1^r`. Right multiplication by `D^r` equalizes T's diagonal entries. Consequently

```text
G(s) = lambda [1 0]     with lambda != 0.
              [z 1]
```

For every such scalar lower shear S and `D = diag(1,2)`, direct multiplication gives

```text
S^2 D^2 S = D S^3 D
          = lambda^3 [1  0].
                     [6z 4]
```

This yields the distinct binary messages

```text
m1 = s || s || 11 || s
m2 = 1 || s || s || s || 1.
```

Here `|s| = 142420668`, so both messages have `3|s|+2 = 427262006` bits. The verifier checks the exact endpoint, the scalar lower-shear condition, original-product equality, distinct packed inputs, and the full digest. Both files occupy 53,407,751 bytes, with two trailing zero bits added to complete the final byte. The reported digest uses the original 427,262,006-bit messages. Hashing all 427,262,008 bits of each padded file also gives a collision, but with a different common digest. Explicitly pass 427,262,006 bits to reproduce the reported digest.

`tools/search_direct_lift.py` provides a bounded Python reference search over j, both signs, and lifts 0 and 1. Replaying the saved index reproduces the endpoint; it does not measure a fresh search from zero or imply a success-density theorem.

## Verification evidence

`verify.py` checks the original matrices and the submitted digest encoding. With `--official-zip`, it separately builds the unchanged submitted reference and optimized implementations after checking the archive and source checksums. For every message it compares the full digest, and for the first message in each pair it changes one meaningful bit and checks that both C implementations agree with the changed model output and differ from the collision digest. A guard after the output buffer checks that bytes beyond the 64-byte digest remain unchanged.

The report is `verification/verified_with_official_C.json`. The saved SHA-256 values identify each packed file. The long messages are reconstructed from their certificate and can optionally be materialized. The exact message lengths must be passed to `CryptHash`, especially for the non-byte-aligned long pair.

## Relationship to prior work

CHAMP uses matrix products and has an existing literature on algebraic attacks. Its specification and later paper are the definition of the target [1]. Determinant constraints and earlier collision bounds are covered by Yuan et al. [2] and the NGCC public assessment [3]. The public Tsinghua Hash Lab comment [4] already discusses commuting matrix products and a change of basis to nonnegative generators. Mullan and Tsaban [5] develop subgroup and short-collision techniques for matrix homomorphic hashes; applicability of individual theorems depends on their hypotheses. Idrassi's public package [7] gives a concrete CHAMP subgroup method and collision certificates at reduced primes.

These sources should be credited for the surrounding matrix, subgroup, and lifting context. The present package documents the explicit bridge/weighted-relation construction and the directed-lift/shear construction, together with their two verified witnesses at the official CHAMP-512 prime. It does not claim that the change of basis, integer lifting, subgroup methods, or generalized birthday search are new in themselves.

## References

1. Alexander Demin, Alexey Ovchinnikov, and Vladimir Shpilrain. CHAMP paper: <https://arxiv.org/abs/2610.04442>. The exact submitted implementation archive and its checksums are identified in `data/official_sources.json`.
2. Yufei Yuan, Ruichen Wu, Shanpeng Wei, Junxu Shen, Jinpeng Liu, and Yixin Zhang. *Structural Analysis of Seven Hash Functions Submitted to the NGCC*. <https://eprint.iacr.org/2026/2152>.
3. NGCC public assessment of CHAMP, including determinant, palindrome, and subgroup analyses: <https://ngcc.dev/reports/hash-04.html>.
4. Tsinghua Hash Lab. Public CHAMP comment, 22 September 2026: <https://list.niccs.org.cn/archives/list/crypthashforum@list.niccs.org.cn/message/QNMIAAKIPHG5FEK7QZEE2ZYBOWQHCZUE/>.
5. Ciaran Mullan and Boaz Tsaban. *SL2 Homomorphic Hash Functions: Worst Case to Average Case Reduction and Short Collision Search*. Designs, Codes and Cryptography 81 (2016), 83–107. <https://arxiv.org/abs/1306.5646>.
6. David Wagner. *A Generalized Birthday Problem*. CRYPTO 2002. The present implementation uses a centered-interval merge and an explicit parity check.
7. Mounir Idrassi. Public CHAMP cryptanalysis package: <https://github.com/amcrypto-jp/champ-cryptanalysis>.
