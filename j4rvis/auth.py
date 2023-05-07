import bcrypt


def hash_password(password: str) -> bytes:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())


def verify_password(password: str, password_hash: bytes()) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash)
