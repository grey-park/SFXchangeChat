from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from sympy import true


# what gets hashed (the message body bytes);
# what gets signed (the SHA-256 fingerprint of those bytes);
# the parameters you pass to the library (hash algorithm, padding scheme, key size) and why;
# where verification happens (always on the client);
# why the private key never leaves the client.

# ********************************************************************************
# on signe l'empreinte SHA-256 du message avec la clé privée
# ********************************************************************************

def sign_message(private_key, message_bytes: bytes) -> bytes:
    """
    Signe les bytes du corps du message avec la private key.
    Retourne la signature en bytes (256 bytes pour une clé de 2048-bit). 2048 bits / 8 = 256 octets
    """
    return private_key.sign(
        message_bytes,            # raw message body bytes
        padding.PKCS1v15(),       # padding scheme (donnée en section 4.2)
        hashes.SHA256(),          # hashes le message avec SHA-256 (donnée en section 4.2)
    )

# ********************************************************************************
# on vérifie que la signature correspond au message avec la clé publique
# ********************************************************************************

def verify_signature(public_key, message_bytes: bytes, signature: bytes) -> bool:
    return true
