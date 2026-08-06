"""Wire format for the Schnorr protocol.

The transport is a TCP stream of newline-delimited JSON objects. Every
message is a single line of the form ``{"type": <NAME>, ...}``. All numbers
are plain JSON integers.

A typical conversation over one connection:

    server -> client : PARAMS       p, q, g      (sent immediately on connect)
    client -> server : REGISTER     username, public_key
    server -> client : OK | ERROR
    client -> server : COMMITMENT   username, commitment
    server -> client : CHALLENGE    challenge
    client -> server : RESPONSE     response
    server -> client : RESULT       accepted
    server -> client : ERROR        message      (any failure reply)

Keeping every message in this one module pins down the contract both sides
agree on; the socket framing (newline + JSON) lives in the server and
client adapters, not here.
"""


def serialize_parameters(params):
    """Break the shared PublicParameters into JSON-safe integers."""
    return {"p": params.p, "q": params.q, "g": params.g}


def deserialize_parameters(data):
    """Rebuild a PublicParameters object from :func:`serialize_parameters`."""
    from crypto.parameters import PublicParameters

    return PublicParameters(p=data["p"], q=data["q"], g=data["g"])


# --- server -> client -------------------------------------------------

def encode_parameters_message(params):
    """The greeting sent to a fresh client: the shared public parameters."""
    return {"type": "PARAMS", **serialize_parameters(params)}


def encode_ok():
    return {"type": "OK"}


def encode_error(message):
    return {"type": "ERROR", "message": message}


def encode_challenge(challenge):
    return {"type": "CHALLENGE", "challenge": challenge}


def encode_result(accepted):
    return {"type": "RESULT", "accepted": bool(accepted)}


def decode_challenge(message):
    return message["challenge"]


def decode_result(message):
    return message["accepted"]


# --- client -> server -------------------------------------------------

def encode_register(username, public_key):
    return {"type": "REGISTER", "username": username, "public_key": public_key}


def decode_register(message):
    return message["username"], message["public_key"]


def encode_commitment(username, commitment):
    return {"type": "COMMITMENT", "username": username, "commitment": commitment}


def decode_commitment(message):
    return message["username"], message["commitment"]


def encode_response(response):
    return {"type": "RESPONSE", "response": response}


def decode_response(message):
    return message["response"]