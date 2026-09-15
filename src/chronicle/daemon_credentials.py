"""Exclusive, ephemeral credential files for the foreground daemon."""

from collections import Counter
from contextlib import contextmanager
import math
import os
from pathlib import Path
import re
import secrets
import stat

from chronicle.errors import ChronicleError


def validate_daemon_token(token: str) -> str:
    counts = Counter(token)
    entropy = sum(count * math.log2(len(token) / count) for count in counts.values())
    if (not re.fullmatch(r"[A-Za-z0-9_-]{43,128}", token)
            or len(counts) < 16 or entropy < 192):
        raise ChronicleError(
            "DAEMON_WEAK_TOKEN", "Daemon token does not meet credential strength requirements.",
            "Use a cryptographically generated token with at least 32 random bytes.",
        )
    return token


@contextmanager
def daemon_token_file(path: Path):
    path = path.absolute()
    identity = None
    try:
        if any(parent.is_symlink() for parent in path.parents):
            raise ChronicleError("DAEMON_TOKEN_FILE", "Token file parents must not be symlinks.")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
        fd = os.open(path, flags, 0o600)
        try:
            info = os.fstat(fd)
            identity = (info.st_dev, info.st_ino)
            if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o600:
                raise ChronicleError("DAEMON_TOKEN_FILE", "Token file must have mode 0600.")
            token = validate_daemon_token(secrets.token_urlsafe(32))
            with os.fdopen(fd, "w", encoding="ascii") as stream:
                fd = -1
                stream.write(token + "\n")
                stream.flush()
                os.fsync(stream.fileno())
        finally:
            if fd != -1:
                os.close(fd)
        yield token
    except OSError as exc:
        raise ChronicleError(
            "DAEMON_TOKEN_FILE", "Cannot create or use the exclusive daemon credential file.",
            "Use a new path in a private directory; check for an active daemon or stale file.",
        ) from exc
    finally:
        if identity is not None:
            try:
                info = path.lstat()
                if (info.st_dev, info.st_ino) == identity:
                    path.unlink()
            except FileNotFoundError:
                pass
            except OSError as exc:
                raise ChronicleError(
                    "DAEMON_TOKEN_CLEANUP", "Cannot remove the daemon credential file.",
                    "Verify the daemon has stopped and remove the stale file before restarting.",
                ) from exc
