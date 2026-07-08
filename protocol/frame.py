# protocol/frame.py

# section 5 Communication Protocol (SFX)

# TCP est un flux d'octets : les données arrivent en un flot continu, sans séparation.
# format de trame à longueur préfixée
# [HEADER][TYPE][LENGTH][PAYLOAD]
#   3B     1B    4B      N octets

# import socket  # recv et sendall
# J'utilise l'objet sock = un object socket qui aura des méthodes

import struct

# ******************************************************
# format de trame (session SFX frame format)
# ******************************************************

HEADER = b"SFX"          # les 3 octets
HEADER_SIZE = 3
TYPE_SIZE = 1
LENGTH_SIZE = 4  # PAYLOAD in bytes (4-byte big-endian unsigned integer, most significant byte comes first)
FIXED_PART_SIZE = HEADER_SIZE + TYPE_SIZE + LENGTH_SIZE   # = 8

MAX_PAYLOAD = 1_048_576  # 1 MB (imposé section 5)

# Les types de trame (1 octet ASCII chacun) (section 5.1 Message Types)
TYPE_SUBMIT = b"S"              # submit a signed object
TYPE_LIST = b"L"                # list objects
TYPE_GET = b"G"                 # get one object
TYPE_TAMPER = b"T"              # tamper an object
TYPE_OK = b"O"                  # success response
TYPE_ERROR = b"E"               # error response

# ************************************************************************
# Définition des formats valides + helpers
# ************************************************************************

VALID_REQUEST_TYPES = {TYPE_SUBMIT, TYPE_LIST, TYPE_GET, TYPE_TAMPER}
VALID_RESPONSE_TYPES = {TYPE_OK, TYPE_ERROR}
VALID_TYPES = VALID_REQUEST_TYPES | VALID_RESPONSE_TYPES

def is_request_type(frame_type):
    """True si l'octet de type correspond à une requête (S, L, G, T)."""
    return frame_type in VALID_REQUEST_TYPES

def is_response_type(frame_type):
    """True si l'octet de type correspond à une réponse (O, E)."""
    return frame_type in VALID_RESPONSE_TYPES

# ************************************************************************
# Création des class exceptions pour avoir un message différent selon le problème
# erreur demandé en section 8: "Server must return error frames"
# ************************************************************************

class ConnectionClosed(Exception):
    """Le pair a fermé la connexion pendant la lecture."""

class FrameError(Exception):
    """Trame malformée (mauvais header, type inconnu, longueur invalide)."""


# ************************************************************************
# Gestion de la fragmentation des frames = utilisé dans recv_frame()
# ************************************************************************

def recv_exact(sock, n):
    """
    recv_exact(sock, n) = Lit exactement n octets du socket
    pas = à
    sock.recv(n) = donne jusqu'à n octets
    Il faut boucler sur le recv() = gère la fragmentation
    "keep calling recv() until you have collected the exact number of bytes you expect"
    """
    chunks = []
    remaining = n
    while remaining > 0:
        chunk = sock.recv(remaining)
        if not chunk:                      # b"" = (chaîne d'octets vide) = le pair a fermé la connexion
            raise ConnectionClosed("Connexion fermée pendant la lecture.")
        chunks.append(chunk)
        remaining -= len(chunk)            # on décompte ce qu'on a VRAIMENT reçu
    return b"".join(chunks)                # on recolle les morceaux


# ************************************************************************
# Assemble une trame complète : HEADER + TYPE + LENGTH + PAYLOAD.
# ************************************************************************

def pack_frame(frame_type, payload):
    """
    Assemble une trame complète : HEADER + TYPE + LENGTH + PAYLOAD.
    struct.pack(">I", len(payload)) convertit le nombre (la taille du payload) en 4 octets big-endian
    """
    if frame_type not in VALID_TYPES:
        raise FrameError(f"Type de trame inconnu : {frame_type!r}")

    # "reject any frame whose LENGTH exceeds a fixed maximum and return an error response"
    if len(payload) > MAX_PAYLOAD:
        raise FrameError("Payload dépasse MAX_PAYLOAD (1 MB).")

    length = struct.pack(">I", len(payload))   # longueur sur 4 octets big-endian (write)
    return HEADER + frame_type + length + payload

# ************************************************************************
# gestion de l'envoie de la frame
# ************************************************************************

def send_frame(sock, frame_type, payload):
    """Construit et envoie une trame complète (sendall gère les envois partiels)."""
    sock.sendall(pack_frame(frame_type, payload))

# ************************************************************************
# gestion de la réception de la frame
# ************************************************************************

def recv_frame(sock):
    """
    Lit une trame complète et renvoie (frame_type, payload).
    Lit en 2 temps : d'abord les 8 octets fixes (pour connaître LENGTH),
    puis exactement LENGTH octets de payload.
    """
    # 1) les 8 octets fixes : HEADER (3) + TYPE (1) + LENGTH (4)
    fixed = recv_exact(sock, FIXED_PART_SIZE)
    header = fixed[0:HEADER_SIZE]
    frame_type = fixed[HEADER_SIZE:HEADER_SIZE + TYPE_SIZE]
    length_bytes = fixed[HEADER_SIZE + TYPE_SIZE:FIXED_PART_SIZE]

    if header != HEADER:
        raise FrameError("Header invalide : SFX attendu.")
    if frame_type not in VALID_TYPES:
        raise FrameError(f"Type de trame inconnu : {frame_type!r}")

    # struct.unpack(">I", length_bytes) convertit les 4 octets big-endian en nombre (la taille du payload) read
    (length,) = struct.unpack(">I", length_bytes)   # 4 octets -> nombre
    if length > MAX_PAYLOAD:
        raise FrameError("Longueur invalide : dépasse MAX_PAYLOAD.")

    # 2) exactement LENGTH octets de payload
    payload = recv_exact(sock, length) if length > 0 else b""
    return frame_type, payload