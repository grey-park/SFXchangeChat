# protocol/decoder.py
# frame.py = transporter des octets bruts dans une trame
# JSON = organiser les données dans le playload
# decode: transforme octets (frame) à JSON + protège le serveur contre les trames malformées (section 8).

import json
from . import frame as fr
from .encoder import COMMAND_TO_TYPE

# ************************************************************************
# Champs obligatoires attendus pour chaque commande.
# Le decoder vérifie que tous sont présents (section 8 : "missing mandatory fields").
# ************************************************************************

# ici payload contient le message brut + signature + clé publique + le type d'algo
REQUIRED_FIELDS = {
    "SEND_SIGNED_TEXT": [
        "command", "object_name", "sender",
        "message_b64", "signature_b64", "public_key_b64", "hash_algorithm",
    ],
    "LIST_OBJECTS":  ["command"],
    "GET_OBJECT":    ["command", "object_id"],
    "TAMPER_OBJECT": ["command", "object_id"],
}

# ************************************************************************
# FrameError   =  trame malformé (provient de frame.py)
# PayloadError =  trame ok, mais CONTENU malformé (provient de decoder.py
# ************************************************************************

class PayloadError(Exception):
    """Payload JSON invalide ou incohérent avec la trame."""

# ************************************************************************
# Helper commun : octets JSON -> dict  (l'inverse de encode_json)
# ************************************************************************

def decode_json(payload):
    """
    INPUT: octets (le payload de la trame)
    OUTPUT: dict Python
    Lève PayloadError si erreurs ( l'UTF-8 / du JSON / un objet valide.
    """
    # 1) octets -> texte
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        raise PayloadError("Payload pas UTF-8 valide.")  # module python

    # 2) texte -> objet Python
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        raise PayloadError("Payload pas JSON valide.")  # module json

    # 3) Vérifier si data est bien un dict
    if not isinstance(data, dict):
        raise PayloadError("JSON doit être un objet.")

    return data

# ************************************************************************
# A. tratiement des REQUÊTE reçue par le SERVEUR : octets -> dict (trame S, L, G ou T)
# ************************************************************************

def decode_request(frame_type, payload):
    """
    INPUT: le TYPE byte de la trame + le payload (octets)
    décodage du payload avec decode_json(payload)
    (4 validations (section 8))
    OUTPUT: dict de la requête validé.
    """
    # check 1 : JSON valide) -> utilise decode_json
    data = decode_json(payload)

    # check 2 : la commande doit être connue
    command = data.get("command")
    if command not in REQUIRED_FIELDS:
        raise PayloadError(f"Commande non supportée : {command!r}")

    # check 3 : check si TYPE en byte correspondre à la commande
    if COMMAND_TO_TYPE[command] != frame_type:
        raise PayloadError(
            f"Le type {frame_type!r} ne correspond pas à la commande {command!r}."
        )

    # check 4 : tous les champs obligatoires doivent être présents
    missing = [field for field in REQUIRED_FIELDS[command] if field not in data]
    if missing:
        raise PayloadError(f"Champs obligatoires manquants : {', '.join(missing)}")

    return data

# ************************************************************************
# B. traitement des RÉPONSE reçue par le CLIENT : octets -> dict (trame O ou E)
# ************************************************************************

def decode_response(frame_type, payload):
    """
    INPUT: le TYPE byte + le payload d'une réponse serveur
    OUTPUT: dict de la réponse.
    """
    if frame_type not in fr.VALID_RESPONSE_TYPES:
        raise PayloadError(f"Trame de réponse attendue, reçu {frame_type!r}.")
    return decode_json(payload)