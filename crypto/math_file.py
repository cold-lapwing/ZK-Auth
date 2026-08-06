"""Pure modular arithmetic and primality helpers.

This module holds the raw mathematics only. It contains no protocol
logic and no randomness API of its own beyond what prime generation
needs, so every function here is easy to reason about in isolation.

Why this exists separately from schnorr.py:

    * schnorr.py        -> *what* the protocol computes (keygen, proof)
    * math_file.py      -> *how* the underlying number theory works

Keeping this layer free of protocol concepts makes it reusable and keeps
the Schnorr steps readable.
"""

from secrets import randbelow

# Small primes. Used to reject composites cheaply before the expensive
# Miller-Rabin rounds run, and reused as a deterministic base set.
_SMALL_PRIMES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)


def mod_pow(base, exponent, modulus):
    """Return ``base ** exponent mod modulus``.

    Python's built-in ``pow`` performs fast modular exponentiation, so we
    wrap it under one name to make the intent of every Schnorr step visible
    without accidentally re-raising the exponent (huge intermediates).
    """
    return pow(base, exponent, modulus)


def is_probable_prime(n, rounds=64):
    """Probabilistic Miller-Rabin primality test.

    Returns True if ``n`` is very likely prime and False if it is composite.
    For a d-bit odd number this errs (if at all) with probability < 2**-rounds,
    which is far beyond what an educational Schnorr demo needs.

    Idea: for a prime n it holds that n-1 = d * 2**s with d odd, and for any
    base ``a`` not divisible by n either ``a**d == 1`` or one of the squarings
    reaches ``n - 1``. A composite that passes several bases is a "strong
    pseudoprime", so inductionally we test many random bases and only accept
    if every one passes.
    """
    if n < 2:
        return False

    for small in _SMALL_PRIMES:
        if n % small == 0:
            return n == small

    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1

    for _ in range(rounds):
        # Random base in [2, n - 2]. ``randbelow`` never returns n-1 so the
        # range is symmetric enough for our purposes.
        base = randbelow(n - 3) + 2
        x = mod_pow(base, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = mod_pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def generate_prime(bits):
    """Return a random ``bits``-bit probable prime.

    We start with a random ``bits``-bit odd candidate and reject it, pulling
    a fresh one, until it passes Miller-Rabin. The prime index theorem says
    about one in ``ln(2**bits)`` odd integers is prime, so this loop is short.
    """
    while True:
        candidate = randbelow(1 << bits)
        candidate |= (1 << (bits - 1)) | 1  # force top bit (size) and oddness
        if is_probable_prime(candidate):
            return candidate