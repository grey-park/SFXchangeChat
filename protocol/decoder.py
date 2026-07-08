# protocol/encoder.py
# frame.py = transporter des octets bruts dans une trame
# mais serveur et client raisonne en dictionnaires

# Transforme un dict Python en trame SFX prête à envoyer.
# dict Python <- decoder - JSON <- octets - trame (frame.py)

# protocol/decoder.py
# Fait l'INVERSE de l'encoder : octets (payload) -> JSON -> dict, PLUS la validation.
# C'est le decoder qui protège le serveur contre les trames malformées (section 8).

import json
from . import frame as fr
from .encoder import COMMAND_TO_TYPE

# ************************************************************************
# Champs obligatoires attendus pour chaque commande.
# Le decoder vérifie que tous sont présents (section 8 : "missing mandatory fields").
# ************************************************************************

# On utilise REQUIRED_FIELDS pour vérifier qu'un payload reçu a bien tous les champs attendus
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
# Exception levée quand un payload est invalide ou incohérent.
# ************************************************************************

class PayloadError(Exception):
    """Payload JSON invalide ou incohérent avec la trame."""

# ************************************************************************
# Helper commun : octets JSON -> dict  (l'inverse de encode_json)
# ************************************************************************

# octets -> texte -> python object
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
        raise PayloadError("Payload n'est pas de l'UTF-8 valide.")  # module python

    # 2) texte -> objet Python
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        raise PayloadError("Payload n'est pas du JSON valide.")  # module json

    # 3) Test si c'est bien un objet JSON (dict)
    if not isinstance(data, dict):
        raise PayloadError("Le JSON doit être un objet.")

    return data

# ************************************************************************
# REQUÊTE reçue par le SERVEUR : octets -> dict + 4 validations (section 8)
# ************************************************************************


# ************************************************************************
# RÉPONSE reçue par le CLIENT : octets -> dict (trame O ou E)
# ************************************************************************
