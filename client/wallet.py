"""Client-side wallet: the prover's private key store.

The wallet keeps the only copy of a user's secret key, scoped to their
username. In a real system this would live in encrypted storage; here a
plain JSON file makes the educational unmasking explicit.

This module knows about JSON persistence but nothing about cryptography:
it is handed complete (secret_key, public_key) pairs by the protocol layer.
"""

import json
from pathlib import Path


class Wallet:
    """JSON-backed store mapping usernames to keypairs."""

    def __init__(self, path="data/wallet.json"):
        self.path = Path(path)
        self._users = self._load()

    def _load(self):
        if not self.path.exists():
            return {}
        content = self.path.read_text()
        if not content.strip():
            return {}
        return json.loads(content)

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._users, indent=2))

    def add_user(self, username, secret_key, public_key):
        self._users[username] = {
            "secret_key": secret_key,
            "public_key": public_key,
        }
        self._save()

    def has_user(self, username):
        return username in self._users

    def get_secret_key(self, username):
        return self._users[username]["secret_key"]

    def get_public_key(self, username):
        return self._users[username]["public_key"]