"""Brute-force search for a primitive root (generator) modulo p.

A generator g of Z*_p is an element whose powers g, g**2, ..., g**(p-1)
cycle through every non-zero residue, i.e. it produces exactly p - 1
distinct values. That is precisely the property checked below.

The search is intentionally naive (educational). Its cost grows roughly as
``p**2`` modular exponentiations, so it is only feasible for small p. This
is fine for a research demo but would be unacceptable for real parameters,
which is why production deployments use the prime-factorisation criterion:

    g is a generator  <=>  g**((p-1)/r) != 1 mod p for every prime r | p-1
"""


def find_g(p):
    for g in range(2, p):
        powers = set()
        for exponent in range(1, p):
            powers.add(pow(g, exponent, p))
        if len(powers) == p - 1:
            return g
    raise ValueError(f"no generator exists modulo p={p}")