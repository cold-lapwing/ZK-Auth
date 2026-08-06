"""Public system parameters: the finite field that everyone shares.

Schnorr needs a large prime p (the modulus), a generator g of the group
Z*_p, and the order q of g. In this educational finite-field variant we use
the full multiplicative group, so the order is simply ``q = p - 1``.

These parameters are *public*: both the prover (client) and the verifier
(server) must agree on the same triple, otherwise a proof means nothing.
They are deliberately renewed at startup here; a production system would
publish a fixed, audited parameter set.
"""

from dataclasses import dataclass

from crypto.generator_function import find_g
from crypto.math_file import generate_prime, is_probable_prime


@dataclass(frozen=True)
class PublicParameters:
    """The triple (p, g, q) that both parties share."""

    p: int  # modulus, a large prime
    g: int  # generator of the multiplicative group Z*_p
    q: int  # order of g; here q = p - 1

    def __post_init__(self) -> None:
        if not is_probable_prime(self.p):
            raise ValueError(f"modulus p={self.p} is not prime")
        if not (1 < self.g < self.p):
            raise ValueError("generator g must satisfy 1 < g < p")


def generate_parameters(bits=12):
    """Generate a fresh PublicParameters triple.

    The default size is intentionally tiny so the brute-force generator
    search finishes in a lecture's lifetime and the protocol can be
    inspected end to end. Increase ``bits`` for a more expensive, real
    field (see the note in generator_function.py).
    """
    p = generate_prime(bits)
    g = find_g(p)
    return PublicParameters(p=p, g=g, q=p - 1)