# tests/services/test_encryption.py
# Contract assertions for Encryption Service: policy, key derivation, encrypt/decrypt

import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from app.services.encryption import (
    get_policy,
    is_encryption_required,
    encrypt_memory_data,
    decrypt_memory_data,
    generate_key,
    load_key,
    save_key,
    ENCRYPTION_POLICY,
    _derive_key,
)


def test_get_policy():
    """get_policy must return the per-type encryption policy dict."""
    policy = get_policy()
    expected_types = {"FACT", "MEMORY", "DECISION", "GOAL", "PREDICTION", "LESSON", "INTERPRETATION", "UNKNOWN"}
    for mtype in expected_types:
        assert mtype in policy
    assert policy["FACT"] == "none"
    assert policy["MEMORY"] == "optional"
    assert policy["INTERPRETATION"] == "mandatory"


def test_is_encryption_required():
    """is_encryption_required must correctly identify per-type policy."""
    assert is_encryption_required("FACT") is False
    assert is_encryption_required("UNKNOWN") is False
    assert is_encryption_required("MEMORY") is True
    assert is_encryption_required("DECISION") is True
    assert is_encryption_required("GOAL") is True
    assert is_encryption_required("PREDICTION") is True
    assert is_encryption_required("LESSON") is True
    assert is_encryption_required("INTERPRETATION") is True


def test_encryption_policy_constants():
    """ENCRYPTION_POLICY must match the expected per-type values."""
    assert ENCRYPTION_POLICY["FACT"] == "none"
    assert ENCRYPTION_POLICY["MEMORY"] == "optional"
    assert ENCRYPTION_POLICY["GOAL"] == "optional"
    assert ENCRYPTION_POLICY["LESSON"] == "mandatory"
    assert ENCRYPTION_POLICY["INTERPRETATION"] == "mandatory"


def test_generate_key():
    """generate_key must derive a 32-byte key from a passphrase."""
    key = generate_key("testpass")
    assert isinstance(key, bytes)
    assert len(key) == 32
    # Same passphrase should produce same key (deterministic with fixed salt)
    key2 = generate_key("testpass")
    assert key == key2


def test_generate_key_different_passphrases():
    """generate_key must produce different keys for different passphrases."""
    key1 = generate_key("passphrase1")
    key2 = generate_key("passphrase2")
    assert key1 != key2


def test_load_save_key():
    """load_key and save_key must persist keys to disk."""
    import os, tempfile
    key = generate_key("keytestpass")
    with tempfile.NamedTemporaryFile(suffix=".key", delete=False) as f:
        tmp_path = f.name
    try:
        save_key(key, tmp_path)
        loaded = load_key(tmp_path)
        assert loaded == key
    finally:
        os.unlink(tmp_path)


def test_encrypt_decrypt_memory():
    """encrypt_memory_data and decrypt_memory_data must round-trip correctly."""
    # MEMORY (optional with passphrase)
    original = b"secret memory content"
    enc = encrypt_memory_data(original, "MEMORY", passphrase="testpass")
    dec = decrypt_memory_data(enc, passphrase="testpass")
    assert dec == original

    # FACT (none - no encryption)
    original_fact = b"fact content"
    enc_fact = encrypt_memory_data(original_fact, "FACT")
    # For FACT, algorithm is "none", so encrypted is just base64 of plaintext
    dec_fact = decrypt_memory_data(enc_fact)
    assert dec_fact == original_fact

    # INTERPRETATION (mandatory with passphrase)
    original_interp = b"interpretation draft"
    enc_interp = encrypt_memory_data(original_interp, "INTERPRETATION", passphrase="testpass")
    dec_interp = decrypt_memory_data(enc_interp, passphrase="testpass")
    assert dec_interp == original_interp


def test_encrypt_decrypt_without_passphrase_optional():
    """optional encryption without passphrase should return unencrypted data marked as optional."""
    original = b"optional memory"
    enc = encrypt_memory_data(original, "MEMORY")  # no passphrase
    # Should be base64 of plaintext with optional flag
    assert enc["algorithm"] == "aes-gcm"
    assert enc["optional"] is True
    # Decrypt without passphrase should still work (returns data as-is for optional)
    dec = decrypt_memory_data(enc)
    assert dec == original


def test_encrypt_decrypt_mandatory_without_passphrase_fails():
    """mandatory encryption without passphrase should raise ValueError."""
    original = b"mandatory content"
    # Verify that mandatory encryption without passphrase raises ValueError
    try:
        encrypt_memory_data(original, "INTERPRETATION", passphrase=None)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass  # expected


def test_encrypt_decrypt_fact_no_encryption():
    """FACT type must not encrypt - data remains plaintext (base64 encoded)."""
    original = b"FACT: earth is round"
    enc = encrypt_memory_data(original, "FACT")
    assert enc["algorithm"] == "none"
    # Decrypt (base64 decode)
    dec = decrypt_memory_data(enc)
    assert dec == original