# server.py

import socket  # socket.create_connection(...)
from protocol import frame as fr
from protocol import decoder as dec
from protocol import encoder as enc
from storage import object_store as store

HOST = "127.0.0.1"  # localhost Identiques au client
PORT = 6000

# 1) créer le socket d'écoute (srv = socket d'ECOUTE - server)
srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # socket.AF_INET = famille d'adresses IPv4 + type TCP
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # réutiliser le port sans attendre (pratique en dev)
srv.bind((HOST, PORT))       # attacher (réserve) le socket à l'adresse:port (tupple)
srv.listen()                 # se mettre en écoute (accepter des connexions entrantes)
print(f"Serveur en écoute sur {HOST}:{PORT}...")

# 2) attendre un client
conn, addr = srv.accept()    # <- attends puis fabrique la frame à la réception
    # conn = un nouveau socket, dédié à dialoguer avec ce client précis -> arg sock dans frame
    # addr = l'adresse du client (son IP et son port).
print(f"Client connecté : {addr}")

# 3) lire une trame avec frame.py (conn = socket de DIALOGUE dans recv_frame - client)
frame_type, payload = fr.recv_frame(conn)
print(f"Trame reçue -> type={frame_type}  payload={payload}")

# 4) décoder + valider (octets -> dict)
data = dec.decode_request(frame_type, payload)
print(f"Requête décodée : {data['command']}")

# # 5) stocker l'objet
# metadata = store.store_object(data)
# print(f"Objet stocké : id={metadata['object_id']}")

# # 6) répondre OK (dict -> trame)
# reponse = enc.encode_ok({
#     "message": f"Objet stocké avec l'id {metadata['object_id']}.",
#     "object_id": metadata["object_id"],
# })
# conn.sendall(reponse)

# 7) close connections
conn.close()  # ferme la connexion avec ce client (fin de dialogue)
srv.close()  # ferme le socket d'écoute (fin du server)

