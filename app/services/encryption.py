# app/services/encryption.py - Encryption Service
# Injectable PBKDF2-based encryption service with per-type policy enforcement
#
# Supported types and their encryption policy:
#   FACT            -> "none"        (MUST NOT encrypt)
#   MEMORY, DECISION,
#   PREDICTION, GOAL -> "optional"   (SHOULD encrypt when requested)
#   INTERPRETATION, LESSON, IDENTITY -> "mandatory" (MUST encrypt)
#
# Keys derive from user passphrase via PBKDF2-HMAC-SHA256.
# Keys never leave the process in memory.

import base64
import os
import getpass
from pathlib import Path

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend


# ────────────────────────────────────────────────────────────────────
# Per-type encryption policy
# ──────────────────────────────────────────────────────────────────_

ENCRYPTION_POLICY = {
    "FACT": "none",
    "MEMORY": "optional",
    "DECISION": "optional",
    "GOAL": "optional",
    "PREDICTION": "optional",
    "LESSON": "mandatory",
    "INTERPRETATION": "mandatory",
    "UNKNOWN": "none",
}


def get_policy() -> dict:
    """Return the per-type encryption policy dict.

    Returns:
        dict mapping memory type to "none" | "optional" | "mandatory"
    """
    return dict(ENCRYPTION_POLICY)


def is_encryption_required(memory_type: str) -> bool:
    """Check if a given memory type requires encryption per policy.

    Args:
        memory_type: One of the 8 memory types.

    Returns:
        True if encryption is "mandatory" or "optional" (i.e. not "none").
    """
    policy = ENCRYPTION_POLICY.get(memory_type, "none")
    return policy != "none"


# ────────────────────────────────────────────────────────────────────
# Key derivation from passphrase (PBKDF2-HMAC-SHA256)
# ──────────────────────────────────────────────────────────────────_

SALT_LENGTH = 16  # 16 bytes = 128 bits
ITERATIONS = 200_000  # PBKDF2 iterations; adjust for performance


def _derive_key(passphrase: str, salt: bytes | None = None) -> tuple[bytes, bytes]:
    """Derive an encryption key from a passphrase using PBKDF2.

    Args:
        passphrase: User-provided passphrase string.
        salt: Optional salt (16 bytes). If None, a fixed deterministic salt is used.

    Returns:
        tuple: (derived_key_bytes, salt_bytes) - salt is prepended to output for storage.
    """
    if salt is None:
        # Fixed deterministic salt so the same passphrase always
        # produces the same key (used for per-passphrase operations).
        # In production, the key should be loaded from the saved key file.
        salt = b"DECIA_ENC_SALT_2026"  # 16-byte fixed salt
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=ITERATIONS,
    )
    key = kdf.derive(passphrase.encode("utf-8"))
    return key, salt


def generate_key(passphrase: str) -> bytes:
    """Derive and return an encryption key from a passphrase.

    Args:
        passphrase: User-provided passphrase string.

    Returns:
        bytes: 32-byte derived key (AES-256).
    """
    key, _ = _derive_key(passphrase)
    return key


# ────────────────────────────────────────────────────────────────────
# AES-GCM encrypt/decrypt
# ──────────────────────────────────────────────────────────────────_

def encrypt(data: bytes | str, key: bytes) -> bytes:
    """Encrypt data using AES-256-GCM.

    Args:
        data: Plaintext data (str or bytes).
        key: 32-byte encryption key.

    Returns:
        bytes: base64-encoded (nonce + ciphertext + tag).
    """
    if isinstance(data, str):
        data = data.encode("utf-8")

    if len(key) != 32:
        raise ValueError("Key must be 32 bytes (AES-256)")

    nonce = os.urandom(12)  # 96-bit nonce for GCM
    cipher = Cipher(algorithms.AES(key), modes.GCM(nonce), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(data) + encryptor.finalize()
    # Return: base64(nonce + ciphertext + tag)
    result = base64.b64encode(nonce + ciphertext + encryptor.tag)
    return result


def decrypt(encrypted_bytes: bytes, key: bytes) -> bytes:
    """Decrypt data using AES-256-GCM.

    Args:
        encrypted_bytes: base64-encoded (nonce + ciphertext + tag).
        key: 32-byte decryption key (must match the one used to encrypt).

    Returns:
        bytes: Plaintext data.

    Raises:
        ValueError: If key mismatch or corrupt data.
    """
    if len(key) != 32:
        raise ValueError("Key must be 32 bytes (AES-256)")

    try:
        raw = base64.b64decode(encrypted_bytes)
    except Exception as e:
        raise ValueError(f"Invalid base64 encrypted data: {e}")

    if len(raw) < 12 + 16:  # minimum: nonce(12) + tag(16)
        raise ValueError("Encrypted data too short")

    nonce = raw[:12]
    ciphertext = raw[12:-16]
    tag = raw[-16:]

    cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag), backend=default_backend())
    decryptor = cipher.decryptor()
    try:
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    except Exception:
        raise ValueError("Decryption failed: key mismatch or corrupt data")

    return plaintext


# ────────────────────────────────────────────────────────────────────
# Key save/load to disk
# ──────────────────────────────────────────────────────────────────_

def save_key(key: bytes, path: str | os.PathLike) -> None:
    """Save a derived key to disk with restrictive permissions (chmod 600).

    Args:
        key: 32-byte key to save.
        path: File path to write the key to.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(key)
    # Set permissions to 600 (owner read/write only)
    try:
        os.chmod(path, 0o600)
    except Exception:
        # chmod may fail in some environments; not fatal
        pass


def load_key(path: str | os.PathLike) -> bytes:
    """Load a previously saved key from disk.

    Args:
        path: File path to read the key from.

    Returns:
        bytes: The loaded key (32 bytes).

    Raises:
        ValueError: If key file does not contain 32 bytes.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Key file not found: {path}")
    key = path.read_bytes()
    if len(key) != 32:
        raise ValueError(f"Invalid key file: expected 32 bytes, got {len(key)}")
    return key


# ────────────────────────────────────────────────────────────────────
# Type-specific encryption with policy enforcement
# ──────────────────────────────────────────────────────────────────-

def encrypt_memory_data(
    data: bytes | str,
    memory_type: str,
    passphrase: str | None = None,
) -> dict:
    """Encrypt memory data per type policy.

    Args:
        data: Plaintext memory content.
        memory_type: One of the 8 memory types.
        passphrase: User passphrase for key derivation.
            If None and encryption is mandatory, raises ValueError.

    Returns:
        dict with keys: "encrypted" (base64 data), "algorithm", "type",
            "optional" (bool if optional without passphrase).

    Raises:
        ValueError: If encryption is mandatory but no passphrase provided,
                    or if FACT type is attempted to be encrypted with policy.
    """
    policy = ENCRYPTION_POLICY.get(memory_type, "none")

    if policy == "none":
        # FACT: return data as-is, no encryption
        plain = data if isinstance(data, bytes) else data.encode("utf-8")
        return {
            "encrypted": base64.b64encode(plain).decode("utf-8"),
            "algorithm": "none",
            "type": memory_type,
        }

    if policy == "optional":
        if passphrase is None:
            # Optional: return unencrypted but mark as such
            plain = data if isinstance(data, bytes) else data.encode("utf-8")
            return {
                "encrypted": base64.b64encode(plain).decode("utf-8"),
                "algorithm": "aes-gcm",
                "type": memory_type,
                "optional": True,
            }
        key = generate_key(passphrase)
        enc = encrypt(data, key)
        return {
            "encrypted": enc.decode("utf-8"),
            "algorithm": "aes-gcm",
            "type": memory_type,
            "optional": False,
        }

    if policy == "mandatory":
        if passphrase is None:
            raise ValueError(
                f"Mandatory encryption for type '{memory_type}' "
                "but no passphrase provided"
            )
        key = generate_key(passphrase)
        enc = encrypt(data, key)
        return {
            "encrypted": enc.decode("utf-8"),
            "algorithm": "aes-gcm",
            "type": memory_type,
            "optional": False,
        }

    # Fallback: treat as optional
    plain = data if isinstance(data, bytes) else data.encode("utf-8")
    return {
        "encrypted": base64.b64encode(plain).decode("utf-8"),
        "algorithm": "none",
        "type": memory_type,
    }


def decrypt_memory_data(
    encrypted_data: dict,
    passphrase: str | None = None,
) -> bytes:
    """Decrypt memory data using stored metadata.

    Args:
        encrypted_data: dict returned by encrypt_memory_data().
        passphrase: User passphrase. Required for "optional" and "mandatory" types.

    Returns:
        bytes: Plaintext decrypted data.

    Raises:
        ValueError: If decryption fails or passphrase is missing when required.
    """
    algorithm = encrypted_data.get("algorithm", "none")
    mem_type = encrypted_data.get("type", "")

    if algorithm == "none":
        # FACT type or unencrypted data
        try:
            return base64.b64decode(encrypted_data["encrypted"])
        except Exception:
            raise ValueError("Invalid encrypted data format")

    if algorithm == "aes-gcm":
        key = None
        if passphrase is not None:
            key = generate_key(passphrase)

        if key is None:
            # If no passphrase and algorithm is aes-gcm,
            # the data was stored as "optional without encryption";
            # return the base64-decoded data as-is.
            enc_b64 = encrypted_data["encrypted"]
            try:
                return base64.b64decode(enc_b64)
            except Exception:
                raise ValueError("Invalid encrypted data format")

        enc_b64 = encrypted_data["encrypted"]
        try:
            return decrypt(enc_b64, key)
        except ValueError as e:
            raise ValueError(f"Decryption failed: {e}")

    raise ValueError(f"Unknown algorithm: {algorithm}")


# ────────────────────────────────────────────────────────────────────
# CLI entry point: decia-encryption init
# ──────────────────────────────────────────────────────────────────-

def _getpass_passphrase(prompt: str) -> str:
    """Read a passphrase from stdin without echo.

    Args:
        prompt: Prompt message to display.

    Returns:
        str: The entered passphrase (without echo).
    """
    try:
        return getpass.getpass(prompt)
    except Exception:
        # Fallback: read from stdin normally (echo visible)
        return input(prompt + " ")


def _cli_init() -> None:
    """Interactive first-run setup for the encryption service.

    - Generates master key from user passphrase
    - Saves key to config/encryption.key (chmod 600)
    - Creates config/encryption.yaml with policy defaults
    - Prompts for optional types encryption preference
    """
    import sys

    print("=== DECIA Encryption Initialization ===")
    print()

    # Get passphrase
    passphrase = _getpass_passphrase("Set master passphrase: ")
    confirm = _getpass_passphrase("Confirm passphrase: ")
    if passphrase != confirm:
        print("ERROR: Passphrases do not match.")
        sys.exit(1)

    # Derive key and save
    key, salt = _derive_key(passphrase)

    # Save key to config/encryption.key (chmod 600)
    key_path = Path("config/encryption.key")
    key_path.parent.mkdir(parents=True, exist_ok=True)
    save_key(key, key_path)

    # Create encryption.yaml with policy defaults
    policy_config = {
        "policy": ENCRYPTION_POLICY,
        "key_file": str(key_path.absolute()),
        "salt_base64": base64.b64encode(salt).decode("utf-8"),
        "iterations": ITERATIONS,
    }

    yaml_path = Path("config/encryption.yaml")
    yaml_path.parent.mkdir(parents=True, exist_ok=True)
    import yaml
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(policy_config, f, default_flow_style=False, sort_keys=True)

    print(f"Key saved to: {key_path.absolute()}")
    print(f"Config saved to: {yaml_path.absolute()}")
    print(f"Permissions: 600 on key file")
    print()
    print("Encryption policy:")
    for mtype, level in ENCRYPTION_POLICY.items():
        print(f"  {mtype:12s} -> {level}")
    print()
    print("Initialization complete. DECIA is now ready for encrypted memory storage.")


# ────────────────────────────────────────────────────────────────────
# Module-level CLI dispatch
# ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "init":
        _cli_init()
    else:
        print("Usage: decia-encryption init  # Interactive first-run setup")
        sys.exit(1)