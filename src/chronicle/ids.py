"""ID generation with type prefixes."""

from uuid import uuid4

PREFIXES = {
    "chronicle": "chr_",
    "event": "evt_",
    "context": "ctx_",
    "artifact": "art_",
    "version": "ver_",
    "decision": "dec_",
    "rde": "rde_",
    "source": "src_",
}


def generate_id(kind: str) -> str:
    prefix = PREFIXES[kind]
    return f"{prefix}{uuid4().hex}"
