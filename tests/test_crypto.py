# tests/test_crypto.py

from crypto.rsa_keys import (
    generate_key_pair, has_keys,
    load_private_key_object, load_public_key_object, load_public_key_bytes,
)
from crypto.signature import sign_message, verify_signature


def test_generation_cles():
    generate_key_pair("Alice")
    assert has_keys("Alice") is True
    assert has_keys("Inconnu") is False


def test_taille_cle():
    generate_key_pair("Alice")
    priv = load_private_key_object("Alice")  # charge object
    assert priv.key_size == 2048


def test_signature_valide():
    generate_key_pair("Alice")
    priv = load_private_key_object("Alice")  # charge object
    pub = load_public_key_object("Alice")
    sig = sign_message(priv, b"Hello world")
    assert verify_signature(pub, b"Hello world", sig) is True


def test_message_alteration_invalide():
    generate_key_pair("Alice")
    priv = load_private_key_object("Alice")  # charge object
    pub = load_public_key_object("Alice")
    sig = sign_message(priv, b"Hello world")
    assert verify_signature(pub, b"Hell0 world", sig) is False

def test_public_key_bytes_begin_PUBLIC_KEY():
    generate_key_pair("Alice")
    pem = load_public_key_bytes("Alice")  # charge les octets bruts
    assert pem.startswith(b"-----BEGIN PUBLIC KEY-----")

def test_taille_signature():
    generate_key_pair("Alice")
    priv = load_private_key_object("Alice")  # charge object
    sig = sign_message(priv, b"Hello world")
    assert len(sig) == 256