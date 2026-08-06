"""End-to-end tests for the Schnorr protocol.

Section 1 exercises the mathematics and the in-process orchestration
(shared/protocol.py) with no sockets.

Section 2 starts the real TCP server and drives it over the wire with the
asyncio client (client/network.py): registration, honest authentication,
double-registration refusal, and soundness against a corrupted secret.

Run from the project root:
    python test.py
"""

import asyncio
import tempfile
from pathlib import Path

from crypto import schnorr
from crypto.parameters import generate_parameters
from server.database import Database
from server.verifier import Verifier
from client.wallet import Wallet
from shared import protocol, serialization

from server.server import Server
from client.network import ServerConnection

BITS = 12
RUNS = 3
USERNAME = "alice"


def local_flow():
    """Section 1: pure in-process protocol."""
    params = generate_parameters(bits=BITS)
    print(f"public parameters  p={params.p}  q={params.q}  g={params.g}")

    wire = serialization.serialize_parameters(params)
    assert serialization.deserialize_parameters(wire) == params
    print("parameter serialization round-trip  OK")

    with tempfile.TemporaryDirectory() as tmp:
        database = Database(Path(tmp) / "database.json")
        wallet = Wallet(Path(tmp) / "wallet.json")

        public_key = protocol.register(params, database, wallet, USERNAME)
        print(f"registered {USERNAME!r}  public key y={public_key}")
        assert database.get_public_key(USERNAME) == public_key
        assert wallet.has_user(USERNAME)
        print("registration stored correctly        OK")

        accepted = protocol.authenticate(params, database, wallet, USERNAME, runs=RUNS)
        print(f"authenticated {USERNAME!r}  ({accepted}/{RUNS} rounds)")
        assert accepted == RUNS
        print("honest prover accepted                OK")

        # Imposter: answers with a different secret than alice's.
        verifier = Verifier(params, public_key)
        imposter_key = schnorr.generate_secret_key(params)
        impostor_accepted = 0
        for _ in range(RUNS):
            nonce = schnorr.generate_nonce(params)
            commitment = schnorr.generate_commitment(params, nonce)
            challenge = verifier.issue_challenge()
            response = schnorr.generate_response(params, nonce, challenge, imposter_key)
            if verifier.verify(commitment, challenge, response):
                impostor_accepted += 1
        print(f"imposter accepted {impostor_accepted}/{RUNS} rounds")
        assert impostor_accepted == 0
        print("imposter rejected                     OK")


async def network_flow():
    """Section 2: the real TCP server driven by the asyncio client."""
    with tempfile.TemporaryDirectory() as tmp:
        server = Server(
            port=0, database=Database(Path(tmp) / "database.json")
        )
        await server.start()
        try:
            connection = ServerConnection(
                port=server.bound_port, wallet=Wallet(Path(tmp) / "wallet.json")
            )
            try:
                received = await connection.connect()
                assert received == server.params
                print("connected; received server parameters OK")

                public_key = await connection.register("bob")
                assert server.database.has_user("bob")
                print(f"registered 'bob' over TCP  y={public_key}")

                accepted = await connection.authenticate("bob", rounds=RUNS)
                print(f"authenticated 'bob' over TCP  ({accepted}/{RUNS})")
                assert accepted == RUNS

                # A corrupted wallet secret must never convince the server.
                await connection.register("eve")
                secret = connection.wallet.get_secret_key("eve")
                tampered = (
                    secret + 1
                    if secret < server.params.q - 1
                    else secret - 1
                )
                connection.wallet._users["eve"]["secret_key"] = tampered
                accepted = await connection.authenticate("eve", rounds=RUNS)
                print(f"corrupted-secret 'eve'  ({accepted}/{RUNS} accepted)")
                assert accepted == 0

                try:
                    await connection.register("bob")
                    raise AssertionError("double registration must be refused")
                except ValueError as err:
                    print(f"double registration refused: {err}")
            finally:
                await connection.close()
        finally:
            await server.stop()
        print("network flow complete                 OK")


def main():
    local_flow()
    print()
    asyncio.run(network_flow())
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()