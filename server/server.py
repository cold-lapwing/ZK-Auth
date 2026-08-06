"""Network server that runs the Schnorr protocol over TCP.

The server owns the public parameters and the user database. It listens on
a socket and speaks the JSON-lines protocol defined in shared/serialization,
using the pure verifier math from server/verifier.py to issue challenges and
check responses.

This is the *network adaptation* layer: it knows about sockets, connections
and per-connection round state, but never touches secret keys. Every event
is emitted through a stdlib logger so any frontend -- a file, a terminal,
or the TUI's live log panel -- can observe the workflow.
"""

import asyncio
import json
import logging
from pathlib import Path

from crypto.parameters import generate_parameters
from server.database import Database
from server.verifier import Verifier
from shared import serialization


class Server:
    """Asyncio TCP server for Schnorr registration and authentication."""

    def __init__(
        self,
        host="127.0.0.1",
        port=7777,
        params=None,
        params_file=None,
        database=None,
        logger=None,
        bits=12,
    ):
        self.host = host
        self.port = port
        if params is not None:
            self.params = params
        elif params_file is not None and Path(params_file).exists():
            self.params = self._load_params(params_file)
        else:
            self.params = generate_parameters(bits=bits)
            if params_file is not None:
                self._save_params(params_file, self.params)
        self.params_file = params_file
        self.database = database or Database()
        self.logger = logger or logging.getLogger("zk.server")
        self._server = None
        self._connections = set()

    @staticmethod
    def _load_params(path):
        with open(path) as fh:
            return serialization.deserialize_parameters(json.load(fh))

    @staticmethod
    def _save_params(path, params):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as fh:
            json.dump(serialization.serialize_parameters(params), fh)

    @property
    def running(self):
        return self._server is not None

    @property
    def bound_port(self):
        """The actual listening port (useful when started on port 0)."""
        if self._server is None:
            return None
        return self._server.sockets[0].getsockname()[1]

    async def start(self):
        if self._server is not None:
            raise RuntimeError("server is already running")
        self._server = await asyncio.start_server(
            self._handle_client, self.host, self.port
        )
        self.logger.info("listening on %s:%s", self.host, self.port)
        self.logger.info(
            "public parameters  p=%d  q=%d  g=%d",
            self.params.p,
            self.params.q,
            self.params.g,
        )

    async def serve(self):
        """Run until :meth:`stop` closes the listening socket."""
        async with self._server:
            await self._server.serve_forever()

    async def stop(self):
        if self._server is None:
            return
        self.logger.info("stopping server")
        self._server.close()
        await self._server.wait_closed()
        self._server = None
        for writer in list(self._connections):
            writer.close()
        self.logger.info("server stopped")

    # --- per-connection session --------------------------------------

    async def _handle_client(self, reader, writer):
        peer = writer.get_extra_info("peername")
        self._connections.add(writer)
        self.logger.info("client connected from %s", peer)
        try:
            await self._send(writer, serialization.encode_parameters_message(self.params))
            await self._run_session(reader, writer, peer)
        except (json.JSONDecodeError, UnicodeDecodeError) as err:
            self.logger.warning("malformed message from %s: %s", peer, err)
        except (ConnectionError, asyncio.IncompleteReadError) as err:
            self.logger.info("connection from %s ended: %s", peer, err)
        except Exception as err:
            self.logger.error("error serving %s: %s", peer, err)
        finally:
            self._connections.discard(writer)
            writer.close()
            try:
                await writer.wait_closed()
            except (ConnectionError, asyncio.CancelledError):
                pass
            self.logger.info("client disconnected from %s", peer)

    async def _run_session(self, reader, writer, peer):
        """Serve one connection: read lines and answer each message."""
        session = {}  # per-connection round state (username, commitment, ...)
        while True:
            line = await reader.readline()
            if not line:
                return  # client closed the connection
            message = json.loads(line.decode())
            await self._handle_message(writer, session, message)

    async def _handle_message(self, writer, session, message):
        msg_type = message.get("type")

        if msg_type == "REGISTER":
            username, public_key = serialization.decode_register(message)
            if self.database.has_user(username):
                self.logger.warning("register refused: %s already exists", username)
                await self._send(
                    writer, serialization.encode_error(f"{username!r} already registered")
                )
                return
            self.database.register(username, public_key)
            self.logger.info(
                "registered %s  (public key y=%d)", username, public_key
            )
            await self._send(writer, serialization.encode_ok())

        elif msg_type == "COMMITMENT":
            username, commitment = serialization.decode_commitment(message)
            try:
                public_key = self.database.get_public_key(username)
            except KeyError:
                self.logger.warning("commitment from unknown user %s", username)
                await self._send(
                    writer, serialization.encode_error(f"unknown user {username!r}")
                )
                return
            verifier = Verifier(self.params, public_key)
            challenge = verifier.issue_challenge()
            session.update(
                verifier=verifier,
                username=username,
                commitment=commitment,
                challenge=challenge,
            )
            self.logger.info(
                "round for %s: commitment t=%d, issuing challenge c=%d",
                username,
                commitment,
                challenge,
            )
            await self._send(writer, serialization.encode_challenge(challenge))

        elif msg_type == "RESPONSE":
            response = serialization.decode_response(message)
            if not session:
                self.logger.warning("response with no open round")
                await self._send(writer, serialization.encode_error("no open round"))
                return
            accepted = session["verifier"].verify(
                session["commitment"], session["challenge"], response
            )
            verdict = "accepted" if accepted else "rejected"
            self.logger.info(
                "round for %s: response s=%d -> %s",
                session["username"],
                response,
                verdict,
            )
            await self._send(writer, serialization.encode_result(accepted))
            session.clear()

        else:
            self.logger.warning("unknown message type %r", msg_type)
            await self._send(
                writer, serialization.encode_error(f"unknown type {msg_type!r}")
            )

    @staticmethod
    async def _send(writer, message):
        writer.write((json.dumps(message) + "\n").encode())
        await writer.drain()