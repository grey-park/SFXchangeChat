# server.py
# Gère les 4 commandes en boucle : SEND, LIST, GET, TAMPER.

import socket  # socket.create_connection(...)
from protocol import frame as fr
from protocol import decoder as dec
from protocol import encoder as enc
from storage import object_store as store

HOST = "127.0.0.1"  # localhost Identiques au client
PORT = 6000

# ************************************************************************
# B.2 Helper: Traitement d'une commande :
# ************************************************************************
def traiter_commande(data):
    """INPUT: une requête décodée et validée
       inside: exécute la fonction storage selon la commande demandée
       OUTPUT:  la trame de réponse (octets), OK ou ERROR"""

    command = data["command"]

    if command == "SEND_SIGNED_TEXT":
        metadata = store.store_object(data)
        return enc.encode_ok({
            "message": f"Objet stocké avec l'id {metadata['object_id']}.",
            "object_id": metadata["object_id"],
        })

    if command == "LIST_OBJECTS":
        objects = store.list_objects()
        return enc.encode_ok({"objects": objects, "count": len(objects)})

    if command == "GET_OBJECT":
        obj = store.get_object(data["object_id"])
        return enc.encode_ok(obj)

    if command == "TAMPER_OBJECT":
        metadata = store.tamper_object(data["object_id"])
        return enc.encode_ok({
            "message": f"Objet {metadata['object_id']} altéré (content.bin modifié, signature intacte).",
        })

    return enc.encode_error("Commande non supportée.")

def main():
    # ************************************************************************
    # A. Préparation du serveur
    # ************************************************************************

    # 1) créer le socket d'écoute (srv = socket d'ECOUTE - server)
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # socket.AF_INET = famille d'adresses IPv4 + type TCP
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # réutiliser le port sans attendre (pratique en dev)
    srv.bind((HOST, PORT))       # attacher (réserve) le socket à l'adresse:port (tupple)
    srv.listen()                 # se mettre en écoute (accepter des connexions entrantes)
    print(f"Serveur en écoute sur {HOST}:{PORT}...")

    try:
        # boucle externe : On traite un client à la fois ; on ré-accepte après chaque déconnexion
        # évite la fermeture du server à la déconnection du client courant
        while True:

            # 2) attendre un client
            conn, addr = srv.accept()    # <- attends puis fabrique la frame à la réception
                # conn = un nouveau socket, dédié à dialoguer avec ce client précis -> arg sock dans frame
                # addr = l'adresse du client (son IP et son port).
            print(f"Client connecté : {addr}")

            # ************************************************************************
            # B.2 boucle de traitement des commandes du client courant
            #      lire trame -> décode -> traiter -> répondre
            # ************************************************************************
            while True:
                # 1) a lire trame (+ validation de la trame)
                try:
                    frame_type, payload = fr.recv_frame(conn)  # 1) a lire trame
                except fr.ConnectionClosed:
                    print("Client déconnecté.")
                    break
                except fr.FrameError as e:
                    conn.sendall(enc.encode_error(str(e)))
                    break

                # 2) décoder la trame
                try:
                    data = dec.decode_request(frame_type, payload)
                except dec.PayloadError as e:
                    conn.sendall(enc.encode_error(str(e)))
                    continue

                # 3) traiter la commande + répondre
                try:
                    reponse = traiter_commande(data)  # Helper: Traitement d'une commande
                except store.StorageError as e:
                    reponse = enc.encode_error(str(e))  # si une StorageError est levée pendant traiter_commande -> return e

                # 4) Envoie réponse OK ou ERREUR au client
                conn.sendall(reponse)

            # 7) close connections
            conn.close()  # ferme la connexion avec un client (fin de dialogue)

    except KeyboardInterrupt:
        print("\nArrêt du serveur.")
    finally:
        srv.close()  # ferme le socket d'écoute (fin du server)

if __name__ == "__main__":
    main()