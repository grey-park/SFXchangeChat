from crypto.rsa_keys import generate_key_pair, has_keys, load_private_key_object, load_public_key_object, \
    load_public_key_bytes
from crypto.signature import sign_message

if __name__ == "__main__":

    # management des pairs de clés

    priv_path, pub_path = generate_key_pair("Alice")
    print("Clé privée écrite dans :", priv_path)
    print("Clé publique écrite dans :", pub_path)

    print("clés existents :", has_keys("Alice"))
    print("clés existents :", has_keys("Bob"))

    print("load private key object from PEM", load_private_key_object("Alice"))
    print("load public key object from PEM", load_public_key_object("Alice"))
    print("load public key bytes from PEM", load_public_key_bytes("Alice"))
    # print("load public key bytes from PEM", load_private_key_bytes("Alice"))

    priv = load_private_key_object("Alice")
    pub = load_public_key_object("Alice")

    # signer le message
    message = b"Hello world"  # message body en octets (UTF-8)
    signature = sign_message(priv, message)
    print(signature)
    print("Taille de la signature :", len(signature), "octets")  # 256

    # vérification de la signature