"""Small standard-library model of the submitted CHAMP-512 construction."""

import math

PRIME = 2**128 - 15449
I = (1, 0, 0, 1)
A, B = (-2, 1, 4, -3), (-5, 2, -6, 2)
C, D = (4, 1, 2, 1), (1, 0, 0, 2)
P, P_INV = (1, -2, 2, -3), (-3, 2, -2, 1)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def multiply(x, y, modulus=PRIME):
    a, b, c, d = x
    e, f, g, h = y
    out = (a*e+b*g, a*f+b*h, c*e+d*g, c*f+d*h)
    return tuple(v % modulus for v in out) if modulus is not None else out


def power(matrix, exponent, modulus=PRIME):
    require(exponent >= 0, "Negative matrix exponent")
    out = I
    while exponent:
        if exponent & 1:
            out = multiply(out, matrix, modulus)
        matrix = multiply(matrix, matrix, modulus)
        exponent >>= 1
    return out


def inverse(matrix, modulus=PRIME):
    a, b, c, d = matrix
    scale = pow((a*d-b*c) % modulus, -1, modulus)
    return tuple(scale*v % modulus for v in (d, -b, -c, a))


def word_matrix(word, generators=(A, B), modulus=PRIME):
    out = I
    for bit in word:
        require(bit in "01", "Invalid bit")
        out = multiply(out, generators[int(bit)], modulus)
    return out


def segments_matrix(segments, generators=(A, B), modulus=PRIME):
    out = I
    for part in segments:
        factor = (power(generators[1], part, modulus) if isinstance(part, int)
                  else word_matrix(part, generators, modulus))
        out = multiply(out, factor, modulus)
    return out


def bit_length(segments):
    return sum(part if isinstance(part, int) else len(part) for part in segments)


def pack(segments):
    """Integer segments are runs of ones. Pack without expanding long runs."""
    nbits = bit_length(segments)
    require(nbits > 0, "Empty message")
    data = bytearray(b"\xff") * ((nbits+7)//8)
    position = 0
    for part in segments:
        if isinstance(part, int):
            require(part >= 0, "Negative run length")
            position += part
        else:
            for bit in part:
                require(bit in "01", "Invalid bit")
                if bit == "0":
                    data[position//8] &= ~(1 << (7-position % 8))
                position += 1
    require(position == nbits, "Packing length mismatch")
    padding = (-nbits) % 8
    if padding:
        data[-1] &= (0xff << padding) & 0xff
    return data


def digest(matrix, modulus=PRIME):
    """Submitted C encoding: entrywise inverses, a,c,b,d, little endian."""
    return b"".join(
        (pow(matrix[k], -1, modulus) if matrix[k] else 0).to_bytes(16, "little")
        for k in (0, 2, 1, 3)
    )


def mutate_first_bit(segments):
    parts = list(segments)
    first = parts.pop(0)
    if isinstance(first, int):
        require(first > 0, "Expected a nonempty initial segment")
        return ["0"] + ([first-1] if first > 1 else []) + parts
    require(bool(first), "Expected a nonempty initial segment")
    return [("1" if first[0] == "0" else "0") + first[1:]] + parts


def decode_rational(n, d, cap=8192):
    """Bounded reference decoder. Return (word, scale exponent), or None.

    The cap is a search budget, not a universal theorem about all inputs.
    Successful decoding reconstructs G(word)(1,1) = 2**h (n,d).
    """
    if n <= 0 or d <= 0 or math.gcd(n, d) != 1:
        return None
    bits, h = [], 0
    while n != d:
        if len(bits) >= cap:
            return None
        if n < d:
            bits.append("1")
            if d % 2 == 0:
                d //= 2
            else:
                n *= 2
                h += 1
        else:
            if 5*n >= 9*d:
                return None
            bits.append("0")
            n, d = n-d, 4*d-2*n
            if n % 2 == 0:
                n //= 2
                d //= 2
            else:
                h += 1
    return ("".join(bits), h) if n == 1 else None
