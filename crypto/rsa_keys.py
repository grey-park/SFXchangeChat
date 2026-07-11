# crypto/rsa_keys.py

import os

# librairie cryptography
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


KEY_SIZE = 2048
PUBLIC_EXPONENT = 65537
KEYS_DIR = "keys"
# username = "John"

# ********************************************************************************
# Routing des emplacement des clés PEM selon le username
# ********************************************************************************

def _private_key_path(username):
    return os.path.join(KEYS_DIR, f"{username}_private.pem")
def _public_key_path(username):
    return os.path.join(KEYS_DIR, f"{username}_public.pem")

# ********************************************************************************
# génération des clés RSA pour un username donné
# Stockage en PEM -> prend la clé RSA (binaire) et l'encode en Base64
# ********************************************************************************

def generate_key_pair(username):
    os.makedirs(KEYS_DIR, exist_ok=True)  # check dir exist

    # 1. ********************** -----BEGIN PRIVATE KEY----- **********************

    # Génération de la paire RSA (public_exponent=65537, key_size=2048)
    # cryptography choisi au hasard p et q et calcule le modulus n = p x q
    # puis calcule d = e^-1 mod (p-1)(q-1) pour la clé privée
    # retourne un objet clé privée (dont on peut dériver la clé publique via .public_key)
    # cryptography.hazmat.primitives.asymmetric.rsa.generate_private_key(public_exponent, key_size, backend=None)
    private_key = rsa.generate_private_key(public_exponent=PUBLIC_EXPONENT, key_size=KEY_SIZE)

    # Sérialisation de la clé privée en PEM
    # SK format PKCS8 car conteneur générique moderne (chiffrement par mot de passe possible)
    # NoEncryption SK pas chiffrée par simplification
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    # écriture sur disque
    priv_path = _private_key_path(username)
    with open(priv_path, "wb") as f:
        f.write(private_pem)  # wb = write binary


    # 2. ********************** -----BEGIN PUBLIC KEY----- **********************

    # Dériver la clé publique via .public_key()
    public_key = private_key.public_key()  # clé privée RSA (n,e,d,p,q) -> clé public RSA (n,e)

    # Sérialisation de la clé publique en PEM
    # SubjectPublicKeyInfo -----BEGIN PUBLIC KEY-----
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    # écriture sur disque
    pub_path = _public_key_path(username)
    with open(pub_path, "wb") as f:
        f.write(public_pem)  # wb = write binary

    return priv_path, pub_path

# ********************************************************************************
# Helpers: Lecture depuis le fichier PEM + has_key
# ********************************************************************************

def has_keys(username: str):
    """user exists?"""
    return (os.path.exists(_private_key_path(username))
            and os.path.exists(_public_key_path(username))
            )

def load_public_key_object(username):
    """Lit le fichier PEM de l'utilisateur et renvoie l'objet clé publique."""
    with open(_public_key_path(username), "rb") as f:
        # cryptography.hazmat.primitives.serialization.load_pem_public_key(data, password=None, backend=None)
        return serialization.load_pem_public_key(f.read())

def load_private_key_object(username):
    """Lit le fichier PEM de l'utilisateur et renvoie l'objet clé privée."""
    with open(_private_key_path(username), "rb") as f:
        # cryptography.hazmat.primitives.serialization.load_pem_private_key(data, password=None, backend=None)
        return serialization.load_pem_private_key(f.read(), password=None)  # rb = read binary


def load_public_key_bytes(username: str) -> bytes:
    """Load the user's public key as raw PEM bytes (to embed in signed objects)."""
    with open(_public_key_path(username), "rb") as f:
        return f.read()

# # Fonction debug à supprimer car clé privée ne doit jamais quitter la machine du client
# def load_private_key_bytes(username: str) -> bytes:
#     with open(_private_key_path(username), "rb") as f:
#         return f.read()

def deserialize_public_key(pem_bytes):
    """Reconstruit un objet clé publique à partir d'octets PEM reçus (pour la vérification)."""
    return serialization.load_pem_public_key(pem_bytes)
