# protocol/encoder.py
# frame.py = transporter des octets bruts dans une trame
# JSON = organiser les données dans le playload
# encode: transforme JSON à octets (frame)

import json
from . import frame as fr

# ************************************************************************
# Correspondance entre le champ "command" (JSON) -> TYPE byte (trame)
# Car le type est marqué 2x (uniquement pour les REQUÊTES) :
# ************************************************************************

# correspondance JSON "command" -> TYPE byte dans trame (S, L, G, T)
COMMAND_TO_TYPE = {
    "SEND_SIGNED_TEXT": fr.TYPE_SUBMIT,   # S
    "LIST_OBJECTS":     fr.TYPE_LIST,     # L
    "GET_OBJECT":       fr.TYPE_GET,      # G
    "TAMPER_OBJECT":    fr.TYPE_TAMPER,   # T
}
# (O et E sont des réponses, pas des commandes.)

# ************************************************************************
# Helper commun : dict -> octets JSON
# ensure_ascii=False -> garde les accents lisibles (é = é, pas \u00e9) (désactives les échappement)
# on garde tout car ensuite on encode en UTF-8.
# ************************************************************************

# python object -> texte JSON -> octets
def encode_json(data):
    """Sérialise un dict en octets UTF-8 contenant du JSON."""
    text = json.dumps(data, ensure_ascii=False)  # 1) dict -> texte JSON
    return text.encode("utf-8")  # 2) texte -> octets

# ************************************************************************
# A. tratiement des REQUÊTE envoyées par le CLIENT :
#    encode_request({"command": "GET_OBJECT", "object_id": "1"})
#    utilise encode_json (dict -> octets JSON) pour dict de requête -> trame
# ************************************************************************

def encode_request(data):
    """
    Construit une trame de request du client
    INPUT: dict décrivant la requête (ex: {"command": "GET_OBJECT", "object_id": "1"})
    OUTPUT: trame de requête (octets) prête à envoyer sur le socket.
    Le TYPE de la trame est déduit du champ 'command'.
    """
    # 1) lire la commande et vérifier qu'elle est supportée
    command = data.get("command")                    # accès par .get() -> None si absent (pas d'erreur)
    if command not in COMMAND_TO_TYPE:
        raise ValueError(f"Commande non supportée : {command!r}")

    # 2) traduire la commande en TYPE byte
    frame_type = COMMAND_TO_TYPE[command]  # e.g. : "GET_OBJECT" -> b"G"

    # 3) traduire de dict -> octets JSON
    # INPUT: {"command": "GET_OBJECT", "object_id": "1"}
    # OUTPUT: b'{"command": "GET_OBJECT", "object_id": "1"}'
    payload_bytes = encode_json(data)

    # 4) emballer les octets JSON -> trame SFX du bon type
    # protocol.frame.pack_frame : Assemble une trame complète : HEADER + TYPE + LENGTH + PAYLOAD.
    return fr.pack_frame(frame_type, payload_bytes)
    # OUTPUT: SFX + <TYPE> + <longueur> + {"command":"GET_OBJECT","object_id":"1"}

# ************************************************************************
# B. traitement des RÉPONSES envoyées par le SERVEUR:
#     succès (O) et erreur (E)
#     utilise helper encode_json (dict -> octets JSON) pour dict de réponses -> trame
# ************************************************************************

def encode_ok(data):
    """Construit une trame de réponse succès (O). Ajoute status=OK."""

    # 1) data -> dict Python en mémoire
    # Le **data déplie le dict reçu et lui ajoute status: OK devant
    payload = {"status": "OK", **data}  # {"status": "OK", "object_id": "1", ...}

    # 2) dict -> octets JSON
    payload_bytes = encode_json(payload)

    # 3) emballer les octets JSON -> trame SFX de type O
    # protocol.frame.pack_frame : Assemble une trame complète : HEADER + TYPE + LENGTH + PAYLOAD.
    return fr.pack_frame(fr.TYPE_OK, payload_bytes)
    # -> SFX + O + <longueur> + {"status":"OK","object_id":"1",...}


def encode_error(message):
    """Construit une trame de réponse erreur (E). (section 8)"""

    # 1) construire le dict de réponse d'erreur (section 8)
    payload = {"status": "ERROR", "message": message}  # {"status": "ERROR", "message": "Object not found."}

    # 2) dict -> octets JSON
    payload_bytes = encode_json(payload)

    # 3) emballer les octets JSON -> trame SFX de type E
    # protocol.frame.pack_frame : Assemble une trame complète : HEADER + TYPE + LENGTH + PAYLOAD.
    return fr.pack_frame(fr.TYPE_ERROR, payload_bytes)
    # -> SFX + E + <longueur> + {"status":"ERROR","message":"Object not found."}

