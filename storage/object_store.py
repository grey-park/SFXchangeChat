# storage/object_store.py

# Stockage serveur : un dossier par objet signé (section 6.3)
# format: object_1/ metadata.json + content.bin + signature.bin + public_key.pem
# V1: A. store + B. get
# V2: list + tamper

import os

STORAGE_DIR = "server_storage"

# ************************************************************************
# Helper fonctions
# ************************************************************************

# chemin du dossier d'un objet : server_storage/object_1/...
def _object_dir(object_id):
    return os.path.join(STORAGE_DIR, f"object_{object_id}")


# trouve le prochain id libre : 1, 2, 3, ... (pas de compteur simple car section demande stockage persistent)
def _find_next_object_id():
    os.makedirs(STORAGE_DIR, exist_ok=True)
    # compter les dossiers object_ déjà présents
    dossiers = [n for n in os.listdir(STORAGE_DIR) if n.startswith("object_")]
    return str(len(dossiers) + 1)

# ************************************************************************
# A. STORE objet sur le disque
# ************************************************************************
def store_object(request):
    raise NotImplementedError("store_object: à implémenter")

# ************************************************************************
# B. GET objet objet par id (depuis le disque)
# ************************************************************************
def get_object(object_id):
    raise NotImplementedError("get_object: à implémenter")
