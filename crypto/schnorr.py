"""The Schnorr identification (Sigma) protocol.

The goal: a prover convinces a verifier that it knows the secret key x
belonging to a public key y = g**x mod p, without ever revealing x.

A single round, in cryptographic terms:

    Prover                                    Verifier
    -------                                   --------
    x = secret key        y = g**x known      y = public key
    r = random nonce
    t = g**r mod p        --commitment-->     (holds t)
                                                 c = random challenge
    s = (r + c*x) mod q   <--challenge--      (holds c)
                          --response-->       accepts iff g**s == t * y**c mod p

Soundness and zero-knowledge follow from the fact that (t, c, s) form a
sigma protocol, but this file only concerns itself with the arithmetic.
Every function receives the shared PublicParameters explicitly, so there is
no hidden global state and the code reads the way the math is written.
"""

from crypto import math_file, rng


def generate_keypair(params):
    """Return the pair (secret_key, public_key)."""
    secret_key = generate_secret_key(params)
    public_key = generate_public_key(params, secret_key)
    return secret_key, public_key


def generate_secret_key(params):
    """Draw the prover's long-term secret x in 1..q-1."""
    return rng.generate_secret_key(params.q)


def generate_public_key(params, secret_key):
    """y = g**x mod p."""
    return math_file.mod_pow(params.g, secret_key, params.p)


def generate_nonce(params):
    """Draw a fresh per-round nonce r in 1..q-1 (prover only)."""
    return rng.generate_nonce(params.q)


def generate_commitment(params, nonce):
    """t = g**r mod p (prover sends this as its commitment)."""
    return math_file.mod_pow(params.g, nonce, params.p)


def generate_challenge(params):
    """Draw the verifier's random challenge c in 1..q-1."""
    return rng.generate_challenge(params.q)


def generate_response(params, nonce, challenge, secret_key):
    """s = (r + c*x) mod q (prover's answer to the challenge)."""
    return (nonce + challenge * secret_key) % params.q


def verify(params, commitment, challenge, response, public_key):
    """Accept iff g**s == t * (y**c) mod p.

    Why is this a valid check? Because an honest prover computes
    s = (r + c*x) mod q, and therefore

        g**s = g**(r + c*x)
             = g**r * (g**x)**c
             = t      * y**c        (all mod p)

    The verifier only needs the public values t, c, s, y and the shared
    parameters -- never the secret key or the nonce.
    """
    lhs = math_file.mod_pow(params.g, response, params.p)
    rhs = (commitment * math_file.mod_pow(public_key, challenge, params.p)) % params.p
    return lhs == rhs