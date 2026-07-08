
# srv = socket d'écoute -> (créé par socket.socket, attend les connexions)
# srv.accept()  <- attends puis fabrique la frame à la réception
# sock server = conn, addr = srv.accept() -> (serveur fabrique un conn à chaque client)

import socket  # socket.create_connection(...)
from protocol import frame as fr

# Identiques au client
HOST = "127.0.0.1"  # localhost
PORT = 6000

# 1) créer le socket d'écoute (srv écoute)
srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # socket.AF_INET = famille d'adresses IPv4 + type TCP
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # réutiliser le port sans attendre (pratique en dev)
srv.bind((HOST, PORT))       # attacher (réserve) le socket à l'adresse:port (tupple)
srv.listen()                 # se mettre en écoute (accepter des connexions entrantes)
print(f"Serveur en écoute sur {HOST}:{PORT}...")

# 2) attendre un client
conn, addr = srv.accept()    # programme s'arrête sur cette ligne et attend une connexion
# conn = un nouveau socket, dédié à dialoguer avec ce client précis -> arg sock dans frame
# addr = l'adresse du client (son IP et son port).
print(f"Client connecté : {addr}")

# 3) lire une trame avec frame.py (conn devient le "sock" dans recv_frame)
frame_type, payload = fr.recv_frame(conn)
# on lit sur le socket de dialogue, pas sur celui d'écoute
# conn devient le sock à l'intérieur de recv_frame
print(f"Trame reçue -> type={frame_type}  payload={payload}")

# recv_frame -> payload brut -> répond "OK"
# 4) répondre une trame OK
fr.send_frame(conn, fr.TYPE_OK, b'{"status":"OK","message":"bien recu"}')
# renvoie une trame de réponse au client sur conn de type O

# 5) close connections
conn.close()  # ferme la connexion avec ce client (fin de dialogue)
srv.close()  # ferme le socket d'écoute (fin du server)

# théorie
# SERVEUR                                     CLIENT
# 1) socket() -> bind -> listen
# 2) accept()  (attend)
#                                             1) create_connection()  (se connecte)
# 2) accept() se débloque -> conn
#                                             2) send_frame(GET)      (envoie)
# 3) recv_frame(conn) -> lit GET
# 4) send_frame(conn, OK)              -->    3) recv_frame -> lit OK
# 5) conn.close()                             4)   cli.close()