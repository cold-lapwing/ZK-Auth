"""Asyncio client the TUI uses to talk to the Schnorr server.

This class encapsulates the socket conversation. It connects to the server,
receives the shared public parameters, and then performs registration and
authentication rounds using the wallet (which holds the secret key) and the
schnorr math. It knows nothing about the UI: it exposes plain async methods
and raises plain exceptions the UI can surface.

The wire contract it speaks is defined in shared/serialization.py.
"""

import asyncio
import json

from client.wallet import Wallet
from crypto import schnorr
from shared import serialization


class ProtocolError(Exception):
    """The peer replied with something this protocol never sends."""


class ServerConnection:
    def __init__(self, host="127.0.0.1", port=7777, wallet=None):
        self.host = host
        self.port = port
        self.wallet = wallet or Wallet()
        self.params = None
        self._reader = None
        self._writer = None

    @property
    def connected(self):
        return self._writer is not None and not self._writer.is_closing()

    async def connect(self):
        """Open the socket and receive the server's public parameters."""
        self._reader, self._writer = await asyncio.open_connection(self.host, self.port)
        message = await self._recv()
        if message.get("type") != "PARAMS":
            raise ProtocolError(f"expected PARAMS, got {message.get('type')!r}")
        self.params = serialization.deserialize_parameters(message)
        return self.params

    async def close(self):
        if self._writer is not None:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except (ConnectionError, asyncio.CancelledError):
                pass
        self._reader = None
        self._writer = None
        self.params = None

    async def register(self, username):
        """Create a keypair locally, then register the public key server-side."""
        if self.params is None:
            raise RuntimeError("not connected to a server")
        if self.wallet.has_user(username):
            raise ValueError(f"a local key for {username!r} already exists")

        secret_key = schnorr.generate_secret_key(self.params)
        public_key = schnorr.generate_public_key(self.params, secret_key)

        await self._send(serialization.encode_register(username, public_key))
        reply = await self._recv()
        if reply.get("type") == "ERROR":
            raise ValueError(reply["message"])
        if reply.get("type") != "OK":
            raise ProtocolError(f"expected OK, got {reply.get('type')!r}")

        self.wallet.add_user(username, secret_key, public_key)
        return public_key

    async def authenticate(self, username, rounds=1):
        """Run ``rounds`` Schnorr exchanges; return how many were accepted."""
        if self.params is None:
            raise RuntimeError("not connected to a server")
        if not self.wallet.has_user(username):
            raise ValueError(f"no local key for {username!r}")

        secret_key = self.wallet.get_secret_key(username)
        accepted = 0
        for _ in range(rounds):
            nonce = schnorr.generate_nonce(self.params)
            commitment = schnorr.generate_commitment(self.params, nonce)
            await self._send(serialization.encode_commitment(username, commitment))

            reply = await self._recv()
            if reply.get("type") == "ERROR":
                raise ValueError(reply["message"])
            if reply.get("type") != "CHALLENGE":
                raise ProtocolError(f"expected CHALLENGE, got {reply.get('type')!r}")

            response = schnorr.generate_response(
                self.params, nonce, reply["challenge"], secret_key
            )
            await self._send(serialization.encode_response(response))

            reply = await self._recv()
            if reply.get("type") == "ERROR":
                raise ValueError(reply["message"])
            if reply.get("type") != "RESULT":
                raise ProtocolError(f"expected RESULT, got {reply.get('type')!r}")
            if reply["accepted"]:
                accepted += 1
        return accepted

    # --- low-level framing -------------------------------------------

    async def _send(self, message):
        self._writer.write((json.dumps(message) + "\n").encode())
        await self._writer.drain()

    async def _recv(self):
        line = await self._reader.readline()
        if not line:
            raise ConnectionError("server closed the connection")
        return json.loads(line.decode())