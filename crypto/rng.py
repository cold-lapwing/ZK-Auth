"""Cryptographically secure random sampling within the group order.

Secrets are chosen uniformly from the secret-key space, which is the set
of integers 1 .. q-1. The security of Schnorr relies on these being truly
unpredictable, so we use Python's ``secrets`` module rather than the
``random`` module (which is not cryptographically secure).

This module must remain stateless: every function takes its bounds
explicitly instead of reaching for a module-level prime, so the caller
(in practice schnorr.py) always passes the genuine parameters.
"""

from secrets import randbelow


def random_below(q):
    """Uniform integer in [1, q - 1].

    ``randbelow(n)`` draws uniformly from 0 .. n-1; adding one shifts the
    range to 1 .. n. This excludes 0 and q, which is exactly the non-zero
    exponent space we need.
    """
    return randbelow(q) + 1


def generate_secret_key(q):
    """The prover's ephemeral long-term secret x."""
    return random_below(q)


def generate_nonce(q):
    """A fresh ephemeral value r used for a single commitment."""
    return random_below(q)


def generate_challenge(q):
    """A random challenge c issued by the verifier."""
    return random_below(q)