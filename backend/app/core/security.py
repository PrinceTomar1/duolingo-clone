"""Password hashing for the one place this build has real credentials.

bcrypt directly, not a wrapper library: this app has exactly one thing to
hash, hashing/verifying are the only two operations it needs, and bcrypt's own
API is already that small.
"""

import bcrypt


def hash_password(password: str) -> str:
    """Salt and hash a password for storage. Never store the plain value."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Check a login attempt against the stored hash.

    Constant-time by construction -- ``bcrypt.checkpw`` does the comparison,
    never a plain ``==`` on the hash or the plaintext.
    """
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        # A malformed stored hash should read as "wrong password", not crash
        # the login attempt.
        return False
