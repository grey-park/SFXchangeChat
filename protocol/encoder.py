# protocol/encoder.py
# frame.py = transporter des octets bruts dans une trame
# mais serveur et client raisonne en dictionnaires

# Transforme un dict Python en trame SFX prête à envoyer.
# dict Python - encoder -> JSON - octets -> trame (frame.py)


import json
from . import frame as fr

# ************************************************************************
# Correspondance entre le champ "command" (JSON) -> TYPE byte (trame)
# Le type est marqué 2x (uniquement pour les REQUÊTES) :
# - TYPE byte dans la trame        : S, L, G, T
# - champ "command" dans le JSON   : SEND_SIGNED_TEXT, LIST_OBJECTS, GET_OBJECT, TAMPER_OBJECT
# ************************************************************************

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
# dict de requête -> trame complète (utilise encode_json (dict -> octets JSON))
# le CLIENT s'en sert pour envoyer une requête
# - encode_request({"command": "GET_OBJECT", "object_id": "1"})
# ************************************************************************

def decode_json(text):
    return true