# conn  = socket de dialogue (parle à un client précis) -> c'est le sock de frame
# sock client = cli = socket.create_connection(...)

import socket  # socket.create_connection(...)
from protocol import frame as fr

HOST = "127.0.0.1"  # localhost
PORT = 6000

# 1) se connecter au serveur (créer un socket client) (conn dialogue)
cli = socket.create_connection((HOST, PORT))  # tuple (adresse, port)
print(f"Connecté à {HOST}:{PORT}")  # server doit etre online pour ne pas échouer
# cli = object sock

# payload brut
# 2) envoyer une trame GET (cli devient le "sock" dans send_frame)
fr.send_frame(cli, fr.TYPE_GET, b'{"object_id":"1"}')  # passe le sock
print("Trame envoyée.")
# send_frame appelle pack_frane qui assemble puis sendall

# payload brut
# 3) lire la réponse du serveur
frame_type, payload = fr.recv_frame(cli)  # appel fonction recv_frame sur cli
print(f"Réponse reçue -> type={frame_type}  payload={payload}")
# lit la trame que le serveur a renvoyée -> retourn frame_type et payload (format déballé)
# recv_frame = lit les 8 octets fixes + lit le payload + réponse O (OK) ou E (ERROR)

# 4) close
cli.close()
# cli.close() ferme la connexion.
# Si le serveur relisait après, son recv renverrait b"" -> ConnectionClosed