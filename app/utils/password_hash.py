import os
import hashlib


def set_password(password: str) -> bytes:
    """Хеширование пароля пользователя, для хранения в базе данных."""

    salt = os.urandom(32)

    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000
    )

    return salt + key


def password_check(pass_hash: bytes, password: str) -> bool:
    """Проверка пароля на соответствие сохранённому в БД."""

    salt = pass_hash[:32]
    key = pass_hash[32:]

    new_key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000
    )

    if new_key == key:
        return True
    else:
        return False
