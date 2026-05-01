"""
Модуль безопасности приложения.

В этом файле находятся функции для хеширования и проверки паролей.
Пароли нельзя хранить в базе данных в открытом виде, поэтому перед сохранением
пароль преобразуется в хеш.
"""

import hashlib
import secrets


def hash_password(password: str) -> str:
    """
    Создает безопасный хеш пароля.

    Параметры:
        password: пароль пользователя в обычном текстовом виде.

    Возвращает:
        строку формата salt$hash, где:
        - salt нужен для защиты от одинаковых хешей у одинаковых паролей;
        - hash является результатом криптографического преобразования пароля.
    """
    if not password:
        raise ValueError("Пароль не может быть пустым.")

    salt = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000,
    ).hex()

    return f"{salt}${password_hash}"


def verify_password(password: str, stored_password_hash: str) -> bool:
    """
    Проверяет, соответствует ли введенный пароль сохраненному хешу.

    Параметры:
        password: пароль, который ввел пользователь.
        stored_password_hash: хеш пароля из базы данных.

    Возвращает:
        True, если пароль верный.
        False, если пароль неверный.
    """
    try:
        salt, saved_hash = stored_password_hash.split("$", 1)
    except ValueError:
        return False

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000,
    ).hex()

    return secrets.compare_digest(password_hash, saved_hash)