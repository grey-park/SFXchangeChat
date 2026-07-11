# client.py
# commandes supportées, voir ReadMe.md


import base64  # encoder/décoder les champs binaires en texte, parce que le JSON ne transporte que du texte
import os
import shlex   # commandes Unix
import socket  # socket.create_connection(...)

from protocol import frame as fr  # lire/écrire une trame SFX
from protocol import encoder as enc
from protocol import decoder as dec
from crypto import rsa_keys, signature

HOST = "127.0.0.1"  # localhost
PORT = 6000

FILES_DIR = "files_storage"
FILES_IN = os.path.join(FILES_DIR, "to_send")     # fichiers à signer
FILES_OUT = os.path.join(FILES_DIR, "received")   # fichiers vérifiés

# ************************************************************************
# Les 10 commandes
# ************************************************************************
conn = None  # socket de connexion = None (tant qu'on n'est pas connecté)

def cmd_connect():
    """connection au server"""
    global conn
    if conn is not None:
        print("Déjà connecté.")  # évite d'ouvrir 2 sockets
        return
    try:
        conn = socket.create_connection((HOST, PORT))
        print(f"Connecté à {HOST}:{PORT}")
    except ConnectionRefusedError:
        print(f"Connexion refusée : le serveur {HOST}:{PORT} n'est pas lancé ?")  # si trouve pas le serveur

def cmd_disconnect():
    """déconnection du serveur"""
    global conn
    if conn is None:
        print("Pas connecté.")
        return
    conn.close()
    conn = None
    print("Déconnecté.")

def cmd_generate_keys(username):
    """crée keys/<user>_private.pem + keys/<user>_public.pem"""
    rsa_keys.generate_key_pair(username)
    print(f"Clés RSA-2048 générées pour '{username}' (la clé privée reste la machine cliente).")

def cmd_send_text(username, object_name, message_texte):
    # 1) signer le message avec la clé privée du client
    priv = rsa_keys.load_private_key_object(username)
    message = message_texte.encode("utf-8")
    sig = signature.sign_message(priv, message)
    pub_pem = rsa_keys.load_public_key_bytes(username)

    # 2) construire la requête (binaires en Base64 pour le JSON) octets -> texte
    requete = {
        "command": "SEND_SIGNED_TEXT",
        "object_name": object_name,
        "sender": username,
        "message_b64": base64.b64encode(message).decode("ascii"),
        "signature_b64": base64.b64encode(sig).decode("ascii"),
        "public_key_b64": base64.b64encode(pub_pem).decode("ascii"),
        "hash_algorithm": "SHA-256",
    }

    # 3) envoyer + afficher la réponse
    reponse = envoyer(requete)  # helper pour envoyer la requet et recevoir la réponse (format dict)
    print(reponse.get("message", reponse))

def cmd_list():
    """retrouve la liste d'objets e.g. id=1  nom=object_title1  sender=Davide  tampered=True"""
    reponse = envoyer({"command": "LIST_OBJECTS"})  # helper pour envoyer la requet et recevoir la réponse (format dict)
    objects = reponse.get("objects", [])
    if not objects:
        print("Aucun objet stocké.")
        return
    for meta in objects:
        print(f"  id={meta['object_id']}  nom={meta['object_name']}  sender={meta['sender']}  tampered={meta['tampered']}")

def cmd_get(object_id):
    """retrouve un objet avec id + vérifie
       e.g. output: Objet 1 : signature INVALID"""
    metadata, valide, message = recuperer_et_verifier(object_id)  # reponse["metadata"], valide, message
    if metadata is None:
        print(f"Objet {object_id} introuvable.")
        return
    is_valid = "VALID" if valide else "INVALID"
    print(f"Objet {object_id} : signature {is_valid}")

    # /!\ n'affiche le message que si la signature est valide /!\
    if valide:
        texte = message.decode('utf-8', errors='replace')  # replace pour pas planté par un U+FFFD
        print(f"  message : {texte!r}")
    else:
        print("affiche pas le message (signature invalide).")

def cmd_verify(object_id):
    """comme get mais sans le message"""
    metadata, valide, message = recuperer_et_verifier(object_id)
    if metadata is None:
        print(f"Objet {object_id} introuvable.")
        return
    is_valid = "VALID" if valide else "INVALID"
    print(f"Objet {object_id} : signature {is_valid}")

def cmd_verify_all():
    """ e.g. Objet 1 (object_title1) : signature INVALID, Objet 2 (object_title1) : signature INVALID
             Résumé : 0 VALID / 2 INVALID (sur 2)."""
    reponse = envoyer({"command": "LIST_OBJECTS"})  # helper pour envoyer la requet et recevoir la réponse (format dict)
    objects = reponse.get("objects", [])
    if not objects:
        print("Aucun objet à vérifier.")
        return

    valides = 0
    for meta in objects:
        object_id = meta["object_id"]
        metadata, valide, message = recuperer_et_verifier(object_id)
        is_valid = "VALID" if valide else "INVALID"
        print(f"Objet {object_id} ({meta['object_name']}) : signature {is_valid}")
        if valide:
            valides += 1

    total = len(objects)
    print(f"Résumé : {valides} VALID / {total - valides} INVALID (sur {total}).")

def cmd_tamper(object_id):
    """altère un message stoqué"""
    reponse = envoyer({
        "command": "TAMPER_OBJECT", "object_id": object_id,
    })
    message = reponse.get("message", reponse)
    print(message)

def cmd_send_file(username, filename):
    """récupère un fichier depuis files_storage/to_send/ + signe + envoie"""
    filepath = os.path.join(FILES_IN, filename)
    if not os.path.isfile(filepath):
        print(f"Fichier introuvable {FILES_IN} : {filename}")
        return
    with open(filepath, "rb") as f:
        contenu = f.read()
    if len(contenu) > fr.MAX_PAYLOAD:
        print("Fichier trop gros (max 1 Mo).")
        return
    priv = rsa_keys.load_private_key_object(username)
    sig = signature.sign_message(priv, contenu)
    pub_pem = rsa_keys.load_public_key_bytes(username)
    requete = {
        "command": "SEND_SIGNED_TEXT",
        "object_name": filename,          # mon choix : le nom du fichier sert de label
        "sender": username,
        "message_b64": base64.b64encode(contenu).decode("ascii"),
        "signature_b64": base64.b64encode(sig).decode("ascii"),
        "public_key_b64": base64.b64encode(pub_pem).decode("ascii"),
        "hash_algorithm": "SHA-256",
    }
    reponse = envoyer(requete)
    print(reponse.get("message", reponse))

def cmd_get_file(object_id, filename):
    """récupère un objet + vérifie la signature + écrit le fichier SI VALID"""
    metadata, valide, message = recuperer_et_verifier(object_id)
    if metadata is None:
        print(f"Objet {object_id} introuvable.")
        return
    is_valid = "VALID" if valide else "INVALID"
    print(f"Objet {object_id} : signature {is_valid}")

    if valide:
        os.makedirs(FILES_OUT, exist_ok=True)
        output_path = os.path.join(FILES_OUT, filename)
        with open(output_path, "wb") as f:
            f.write(message)
        print(f"Fichier écrit dans {output_path}")
    else:
        print("Fichier non écrit (signature invalide).")

def cmd_help():
    print("""Commandes :
  /connect                                       se connecter au serveur
  /disconnect                                    se déconnecter
  /generate_keys <username>                      générer une paire de clés
  /send_text <username> <object_name> <message>  signer et envoyer un message
  /list                                          lister les objets
  /get <id>                                      récupérer + vérifier + affiche message SI SIGNATURE VALID
  /verify <id>                                   vérifier la signature (is_valid seul)
  /tamper <id>                                   altérer un objet
  /send_file <username> <object_name> <fichier>  signer et envoyer un fichier (depuis files_storage/to_send/)
  /get_file <id> <fichier>                       vérifier et écrire le fichier (dans files_storage/received/)
  /exit                                          quitter""")

# ************************************************************************
# Helper : envoyer une requête au SERVER + lire sa réponse (tout en dict)
# utilisée dans les commandes: cmd_send_text + cmd_list() + cmd_tamper(object_id)
# ************************************************************************
def envoyer(requete):
    """Envoie la requête au serveur (dict) + récupère le dict réponse."""
    trame = enc.encode_request(requete)  # 1) dict -> trame (octets)
    conn.sendall(trame)  # 2) envoyer la trame au serveur
    frame_type, payload = fr.recv_frame(conn)  # 3) lire la trame de réponse
    reponse = dec.decode_response(frame_type, payload)  # 4) trame -> dict
    return reponse

# ************************************************************************
# Helper : Récupérer un objet du serveur + vérifier sa signature localement
# utilisée dans les commandes: cmd_get(object_id) + cmd_verify(object_id) pour les objets stockés
# ************************************************************************
def recuperer_et_verifier(object_id):
    """
    Return reponse["metadata"], valide, message
      - metadata = dict de l'objet (None si introuvable)
      - valide   = True/False (signature VALID/INVALID)
      - message  = les octets du message
    """
    # vérification de la réponse côté client
    reponse = envoyer({"command": "GET_OBJECT", "object_id": object_id})
    if reponse.get("status") == "ERROR":
        return None, None, None  # si server répond error

    # 1) Si pas erreur -> redécoder les champs Base64 en octets
    message = base64.b64decode(reponse["message_b64"])
    sig = base64.b64decode(reponse["signature_b64"])
    pub_pem = base64.b64decode(reponse["public_key_b64"])

    # 2) vérification de signature côté client
         # reconstruire la clé publique de l'objet puis on vérifier la signature
    pub = rsa_keys.deserialize_public_key(pub_pem)
    valide = signature.verify_signature(pub, message, sig)

    return reponse["metadata"], valide, message

# ************************************************************************
# Boucle principale : lire une commande -> l'exécuter
# ************************************************************************
def main():
    print("Client démarré.")
    while True:

        ligne = input("> ").strip()
        if not ligne: continue  # le program attend la cmd

        # Structure de la commande = le premier mot, args = le reste
        parts = shlex.split(ligne)     # découpe en respectant les guillemets
        commande = parts[0]
        args = parts[1:]

        # Si une commande a besoin du réseau et pas connecté -> print("Pas connecté.")
        LIST_LOCAL_CMD = ("/help", "/connect", "/generate_keys", "/exit")
        if conn is None and commande not in LIST_LOCAL_CMD:
            print("Pas connecté. /connect pour se connecter au serveur.")
            continue

        try:
            if commande == "/help":             cmd_help()
            elif commande == "/connect":        cmd_connect()
            elif commande == "/disconnect":     cmd_disconnect()
            elif commande == "/generate_keys":  cmd_generate_keys(args[0])
            elif commande == "/send_text":      cmd_send_text(args[0], args[1], " ".join(args[2:]))  # pour gérer les espaces
            elif commande == "/list":           cmd_list()
            elif commande == "/get":            cmd_get(args[0])
            elif commande == "/verify":         cmd_verify(args[0])
            elif commande == "/verify_all":     cmd_verify_all()
            elif commande == "/tamper":         cmd_tamper(args[0])
            elif commande == "/send_file":      cmd_send_file(args[0], args[1])
            elif commande == "/get_file":       cmd_get_file(args[0], args[1])
            elif commande == "/exit":
                if conn is not None:            cmd_disconnect()
                break
            else:                               print(f"Commande inconnue : {commande}")
        except IndexError:                      print("Argument manquant.")

if __name__ == "__main__":
    main()