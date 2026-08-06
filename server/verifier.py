"""Server-side verifier: issues challenges and checks proofs.

The verifier knows only public information: the shared parameters and the
claimant's registered public key. It is deliberately kept ignorant of the
secret key, which is the whole point of zero-knowledge.

The symmetry with schnorr.py is intentional: the prover's arithmetic lives
in schnorr.py while the verifier's responsibilities (challenge + check) are
gathered here, so the two roles stay strictly separated.
"""

from dataclasses import dataclass

from crypto import schnorr


@dataclass
class Verifier:
    """Holds everything needed to run the verifier side of Schnorr."""

    params: object        # shared PublicParameters
    public_key: int       # the claimant's registered public key

    def issue_challenge(self):
        """Pick a fresh random challenge c for the prover to answer."""
        return schnorr.generate_challenge(self.params)

    def verify(self, commitment, challenge, response):
        """Return True iff the prover knows the matching secret key."""
        return schnorr.verify(
            self.params, commitment, challenge, response, self.public_key
        )