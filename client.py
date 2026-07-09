# conn  = socket de dialogue (parle à un client précis) -> c'est le sock de frame
# sock client = cli = socket.create_connection(...)
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
enc_request = enc.encode_request(requete)
cli.sendall(enc_request)
print("Requete envoyée.")

# # 4) lire la réponse (trame -> dict via decoder)
# frame_type, payload = fr.recv_frame(cli)
# reponse = dec.decode_response(frame_type, payload)
# print(f"Réponse : {reponse}")

cli.close()

#
# # 1) se connecter au serveur (créer un socket client) (conn dialogue)
# cli = socket.create_connection((HOST, PORT))  # tuple (adresse, port)
# print(f"Connecté à {HOST}:{PORT}")  # server doit etre online pour ne pas échouer
# # cli = object sock
#
# # payload brut
# # 2) envoyer une trame GET (cli devient le "sock" dans send_frame)
# fr.send_frame(cli, fr.TYPE_GET, b'{"object_id":"1"}')  # passe le sock
# print("Trame envoyée.")
# # send_frame appelle pack_frane qui assemble puis sendall
#
# # payload brut
# # 3) lire la réponse du serveur
# frame_type, payload = fr.recv_frame(cli)  # appel fonction recv_frame sur cli
# print(f"Réponse reçue -> type={frame_type}  payload={payload}")
# # lit la trame que le serveur a renvoyée -> retourn frame_type et payload (format déballé)
# # recv_frame = lit les 8 octets fixes + lit le payload + réponse O (OK) ou E (ERROR)
#
# # 4) close
# cli.close()
# # cli.close() ferme la connexion.
# # Si le serveur relisait après, son recv renverrait b"" -> ConnectionClosed