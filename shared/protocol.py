"""Orchestrates the complete Schnorr protocol between client and server.

This is the only layer that knows how the two roles must interact. It wires
together the client's wallet, the server's database, the verifier, and the
low-level Schnorr arithmetic into the two lifecycle flows:

    register      -> prover creates a keypair and tells the server y
    authenticate  -> prover proves knowledge of x, verifier accepts/rejects

Each step inside is written as a discrete message between the roles (e.g.
"the prover sends its commitment"), mirroring what a network transport will
later do. Swapping these direct calls for a socket should only change this
file and shared/serialization.py.
"""

from crypto import schnorr
from server.database import Database
from server.verifier import Verifier


def register(params, database, wallet, username):
    """Register a new user and return their public key.

    The secret key stays in the wallet; only y = g**x mod p reaches the
    database. Registration must not be possible twice, so we refuse if the
    username is already known.
    """
    if database.has_user(username):
        raise ValueError(f"username {username!r} is already registered")

    secret_key = schnorr.generate_secret_key(params)
    public_key = schnorr.generate_public_key(params, secret_key)

    wallet.add_user(username, secret_key, public_key)
    database.register(username, public_key)
    return public_key


def authenticate(params, database, wallet, username, runs=1):
    """Run ``runs`` Schnorr rounds for a user; return acceptance count.

    A single round is:
        1. prover commits t = g**r (only the prover knows its nonce r)
        2. verifier issues challenge c
        3. prover answers s = (r + c*x) mod q
        4. verifier accepts iff g**s == t * y**c (mod p)

    We run several rounds to echo the "repeat to amplify certainty" idea of
    a statistical proof of knowledge, but even one acceptance is decisive
    here since x is chosen adversarially-safely large.
    """
    secret_key = wallet.get_secret_key(username)
    public_key = database.get_public_key(username)
    verifier = Verifier(params, public_key)

    accepted = 0
    for _ in range(runs):
        # 1: prover's commitment (sent to server)
        nonce = schnorr.generate_nonce(params)
        commitment = schnorr.generate_commitment(params, nonce)

        # 2: server's challenge (sent back to client)
        challenge = verifier.issue_challenge()

        # 3: prover's response (sent back to server)
        response = schnorr.generate_response(params, nonce, challenge, secret_key)

        # 4: server verifies
        if verifier.verify(commitment, challenge, response):
            accepted += 1

    return accepted


def is_authenticated(params, database, wallet, username, runs=1):
    """Boolean convenience wrapper around :func:`authenticate`."""
    accepted = authenticate(params, database, wallet, username, runs=runs)
    return accepted == runs