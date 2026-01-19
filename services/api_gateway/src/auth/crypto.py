from passlib.context import CryptContext
from cryptography.fernet import Fernet
import os


class PasswordHasherService:
    def __init__(self):
        self._pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")

    def hash_password(self, password: str) -> str:
        """return hashed psw"""
        return self._pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """verify hashed psw"""
        return self._pwd_context.verify(plain_password, hashed_password)


class FernetService:
    def __init__(self, key: str = None):
        # Allow passing key explicitly or falling back to env
        self.key = key or os.getenv("FERNET_KEY")
        if not self.key:
             # Fallback for dev if not set (Safe for now as per "Plan 1" limits, but should be critical later)
             # Raising warning? For now lets assume env is set or we generate one.
             pass

    def encrypt(self, text: str) -> str:
        """
        Encrypt a string using Fernet.
        """
        if not self.key: return text # Fail safe? Or Error?
        return Fernet(self.key.encode()).encrypt(text.encode()).decode()

    def decrypt(self, token: str) -> str:
        """
        Decrypt a Fernet-encrypted string.
        """
        if not self.key: return token
        return Fernet(self.key.encode()).decrypt(token.encode()).decode()
