# storage/object_store.py

# Stockage serveur : un dossier par objet signé (section 6.3)
# format: object_1/ metadata.json + content.bin + signature.bin + public_key.pem
# V1: A. store + B. get
# V2: C. list + D. tamper

import base64
import binascii
import json
import os
from datetime import datetime, timezone

STORAGE_DIR = "server_storage"

# ************************************************************************
# Helper fonctions
# ************************************************************************

# chemin du dossier d'un objet : server_storage/object_1/...
def _object_dir(object_id):
    return os.path.join(STORAGE_DIR, f"object_{object_id}")

# trouve le prochain id libre : 1, 2, 3, ... (pas de compteur simple car on veut stockage persistent)
def _find_next_object_id():
    os.makedirs(STORAGE_DIR, exist_ok=True)
    # compter les dossiers object_ déjà présents
    dossiers = [n for n in os.listdir(STORAGE_DIR) if n.startswith("object_")]
    return str(len(dossiers) + 1)

class StorageError(Exception):
    """storage problems (unknown id, bad base64...)."""

def _b64_to_bytes(value: str, field: str) -> bytes:
    """wrapper principalement pour catcher le StorageError error Base64"""
    try:
        return base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise StorageError(f"Field {field!r} is not valid Base64.") from exc

# ************************************************************************
# A. STORE objet sur le disque
# ************************************************************************

def store_object(request: dict) -> dict:
    """
    Stocke un objet signé à partir d'un payload SEND_SIGNED_TEXT.
    Renvoie le dict metadata (pour que le serveur confirme au client).
    """
    object_id = _find_next_object_id()
    obj_dir = _object_dir(object_id)
    os.makedirs(obj_dir, exist_ok=False)

    # parse content and store
    content = _b64_to_bytes(request["message_b64"], "message_b64")
    with open(os.path.join(obj_dir, "content.bin"), "wb") as f:
        f.write(content)

    # parse signature and store
    signature = _b64_to_bytes(request["signature_b64"], "signature_b64")
    with open(os.path.join(obj_dir, "signature.bin"), "wb") as f:
        f.write(signature)

    # parse public key and store
    public_key_pem = _b64_to_bytes(request["public_key_b64"], "public_key_b64")
    with open(os.path.join(obj_dir, "public_key.pem"), "wb") as f:
        f.write(public_key_pem)

    # parse metabata and store
    metadata = {
        "object_id": object_id,
        "object_name": request["object_name"],
        "sender": request["sender"],
        "hash_algorithm": request["hash_algorithm"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tampered": False,
    }
    with open(os.path.join(obj_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return metadata  # pour serveur répondre au client pour confirmer
                     # -> e.g. {"object_id": "1", ..., tampered=false }

# ************************************************************************
# B. GET objet objet par id (depuis le disque)
# ************************************************************************

def get_object(object_id: str) -> dict:
    """
    Lit un objet signé depuis le disque et le renvoie le payload sous forme de dict
    (champs binaires encodés en Base64, prêt pour le JSON).
    """
    obj_dir = _object_dir(object_id)
    meta_path = os.path.join(obj_dir, "metadata.json")
    if not os.path.isdir(obj_dir) or not os.path.exists(meta_path):
        raise StorageError("Object not found.")

    with open(meta_path, encoding="utf-8") as f:
        metadata = json.load(f)
    with open(os.path.join(obj_dir, "content.bin"), "rb") as f:
        content = f.read()
    with open(os.path.join(obj_dir, "signature.bin"), "rb") as f:
        signature = f.read()
    with open(os.path.join(obj_dir, "public_key.pem"), "rb") as f:
        public_key_pem = f.read()

    return {
        "metadata": metadata,
        "message_b64": base64.b64encode(content).decode("ascii"),
        "signature_b64": base64.b64encode(signature).decode("ascii"),
        "public_key_b64": base64.b64encode(public_key_pem).decode("ascii"),
    }  # serveur répondre au client
       # metadata (e.g. {"object_id": "1", ..., tampered=false })
       # + champs binaires ré-encodés en Base64 (prêt pour le JSON de la réponse)

# ************************************************************************
# C. LIST objets (depuis le disque)
# ************************************************************************
def list_objects():
    """liste de dicts metadata SEULEMENT (un par objet stocké)"""
    os.makedirs(STORAGE_DIR, exist_ok=True)
    objects = []
    for name in os.listdir(STORAGE_DIR):
        if name.startswith("object_"):
            meta_path = os.path.join(STORAGE_DIR, name, "metadata.json")
            if os.path.exists(meta_path):
                with open(meta_path, encoding="utf-8") as f:
                    objects.append(json.load(f))
    return objects  # pour serveur répondre au client -> liste de dicts metadata SEULEMENT (un par objet stocké)

# ************************************************************************
# D. tamper objet with id (sur le disque)
# ************************************************************************
def tamper_object(object_id):
    """
    Corrompt volontairement le contenu d'un objet. (SEUL content.bin est modifié)
    Comme signature pas recalculée -> ne correspond plus au contenu stocké -> vérif INVALID
    """
    obj_dir = _object_dir(object_id)
    content_path = os.path.join(obj_dir, "content.bin")
    meta_path = os.path.join(obj_dir, "metadata.json")

    if not os.path.exists(meta_path):
        raise StorageError("Object not found.")

    # 1) lire le contenu actuel
    with open(content_path, "rb") as f:
        content = f.read()

    # 2) modifier le contenu (on ajoute des octets au contenu) et stoque "content.bin"
    content = content + b"TAMPERED"
    with open(content_path, "wb") as f:
        f.write(content)

    # 3) marquer tampered=True dans metadata.json
    with open(meta_path, encoding="utf-8") as f:
        metadata = json.load(f)
    metadata["tampered"] = True
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return metadata  # pour serveur répondre au client -> retourne le metadata mis à jour (tampered=True)