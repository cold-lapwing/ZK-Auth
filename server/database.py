"""Server-side registry mapping usernames to their public keys.

The server never stores secret keys; it only needs each user's public key
to verify Schnorr proofs. Storing only public data is exactly what makes
the system "non-interactive registration": even if the file leaks, no
secret is exposed (the discrete-log problem still hides x).
"""

import json
from pathlib import Path


class Database:
    """JSON-backed store of username -> public_key."""

    def __init__(self, path="data/database.json"):
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

    def register(self, username, public_key):
        self._users[username] = public_key
        self._save()

    def has_user(self, username):
        return username in self._users

    def get_public_key(self, username):
        return self._users[username]