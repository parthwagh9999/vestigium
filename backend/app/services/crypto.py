"""Encryption service for API key vault using Fernet symmetric encryption."""

from __future__ import annotations

import base64
import logging

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)


class CryptoService:
    """Service for encrypting and decrypting sensitive values.

    Uses Fernet symmetric encryption for API keys and secrets stored
    in the database. If no encryption key is configured, operates in
    passthrough mode with a warning.
    """

    def __init__(self, encryption_key: str) -> None:
        if encryption_key:
            try:
                self._fernet = Fernet(encryption_key.encode())
            except Exception:
                try:
                    padded = base64.urlsafe_b64encode(encryption_key.encode()[:32].ljust(32, b"\0"))
                    self._fernet = Fernet(padded)
                except Exception:
                    logger.warning("Invalid encryption key. Generating a temporary key.")
                    self._fernet = Fernet(Fernet.generate_key())
        else:
            logger.warning("No encryption key configured. Using temporary key. Set ENCRYPTION_KEY in .env")
            self._fernet = Fernet(Fernet.generate_key())

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext string.

        Args:
            plaintext: The value to encrypt.

        Returns:
            Base64-encoded encrypted string.
        """
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt an encrypted string.

        Args:
            ciphertext: The encrypted value.

        Returns:
            The decrypted plaintext.

        Raises:
            ValueError: If decryption fails (wrong key or corrupted data).
        """
        try:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        except InvalidToken as e:
            msg = "Failed to decrypt value — encryption key may have changed"
            raise ValueError(msg) from e
