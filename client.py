# client.py

import base64
import socket  # socket.create_connection(...)
from protocol import decoder as dec
from protocol import encoder as enc
from crypto import rsa_keys, signature
from protocol import frame as fr

HOST = "127.0.0.1"  # localhost
PORT = 6000

# 1) préparer les clés et signer un message
rsa_keys.generate_key_pair("alice")
priv = rsa_keys.load_private_key_object("alice")
message = b"Hello world"
sig = signature.sign_message(priv, message)  # signature avec SK 256 octets
pub_pem = rsa_keys.load_public_key_bytes("alice")  # récupères PK en octets au format PEM

# 2) construire la requête SEND_SIGNED_TEXT (champs binaires en Base64)
    # ici le dict contient le message brut + signature + clé publique + le type d'algo
    # b64encode prend des octets et les réécrit avec 64 caractères sûrs
    # puis .decode("ascii") convertit ces bytes en str pour utiliser json.dumps()
requete = {
    "command": "SEND_SIGNED_TEXT",
    "object_name": "note1",
    "sender": "alice",
    "message_b64": base64.b64encode(message).decode("ascii"),
    "signature_b64": base64.b64encode(sig).decode("ascii"),
    "public_key_b64": base64.b64encode(pub_pem).decode("ascii"),
    "hash_algorithm": "SHA-256",
}

# 3) se connecter + encorde la request (dict -> trame via encoder) + send
cli = socket.create_connection((HOST, PORT))
enc_request = enc.encode_request(requete)  # input: dict / output: bytes (JSON en UTF-8)
cli.sendall(enc_request)
print("Requete envoyée.")

# # 4) lire la réponse (trame -> dict via decoder)
# frame_type, payload = fr.recv_frame(cli)
# reponse = dec.decode_response(frame_type, payload)
# print(f"Réponse : {reponse}")

cli.close()
