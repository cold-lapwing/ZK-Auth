# ZK-Auth

A Python demo of **zero-knowledge authentication** using the Schnorr Sigma protocol.  
The project includes a TCP server, an asyncio client, a local wallet/database, and a Textual TUI to run registration and login flows.

## What it demonstrates

- Registering users by storing only a public key on the server.
- Proving knowledge of a secret key without revealing it.
- Multi-round challenge/response authentication over a socket protocol.

## Project structure

- `/home/runner/work/ZK-Auth/ZK-Auth/crypto` — Schnorr math, randomness, and public parameter generation.
- `/home/runner/work/ZK-Auth/ZK-Auth/server` — verifier, user database, and asyncio TCP server.
- `/home/runner/work/ZK-Auth/ZK-Auth/client` — wallet and client network protocol.
- `/home/runner/work/ZK-Auth/ZK-Auth/shared` — protocol orchestration and message serialization.
- `/home/runner/work/ZK-Auth/ZK-Auth/main.py` — Textual UI entry point.
- `/home/runner/work/ZK-Auth/ZK-Auth/test.py` — end-to-end and network-flow test script.

## Requirements

- Python 3.10+
- `textual` package

Install dependency:

```bash
pip install textual
```

## Run the app

From `/home/runner/work/ZK-Auth/ZK-Auth`:

```bash
python main.py
```

In the UI:
1. Start Server
2. Register User
3. Login

Server events are streamed in the bottom log panel.

## Run tests

From `/home/runner/work/ZK-Auth/ZK-Auth`:

```bash
python test.py
```

The test script validates:
- Local (in-process) protocol behavior
- TCP registration/authentication flow
- Rejection of invalid or tampered proofs

## Notes

- This is an educational implementation with small default parameter sizes (`bits=12`) for readability and speed.
- Do not use these defaults in production cryptographic systems.
