# SFXchange (Échange local de messages signés)

- Système client/serveur local qui échange des messages texte signés sur TCP
- Il détecte toute altération (tampering) grâce à la signature numérique.
- l'objectif est de garantir l'intégrité et l'authentification de l'origine du message via signature RSA.
- Ne tient pas compte de la confidentialité, puis-ce que le message n'est pas chiffré.

## 1. Prérequis
- j'ai utilisé la librairie "cryptography"
```
pip install cryptography
```

## 2. Structure du projet
- la structure est donnée en section 3.2

```
SFXchangeChat/ 
|-- server.py
|-- client.py
|
|-- protocol/
| |-- frame.py
| |-- encoder.py
| |-- decoder.py
|
|-- crypto/
| |-- hashing.py <- pas utilisé
| |-- rsa_keys.py
| |-- signature.py
|
|-- storage/
| |-- object_store.py
|
|-- tests/
| |-- test_crypto.py
```

## 3. Utilisation
Terminal 1 : python server.py
```
python server.py
```
Terminal 2 : python client.py
```
python client.py
```
## 4. Commandes du client

| Commande                                        | Rôle                                                               |
|-------------------------------------------------|--------------------------------------------------------------------|
| `/help`                                         | affiche la liste des commandes                                     |
| `/connect`                                      | se connecte au serveur                                             |
| `/disconnect`                                   | ferme la connexion                                                 |
| `/generate_keys <username>`                     | génère une paire de clés RSA-2048                                  |
| `/send_text <username> <object_name> <message>` | signe le message et l'envoie                                       |
| `/list`                                         | liste les objets stockés                                           |
| `/get <id>`                                     | récupère un objet, le vérifie, affiche le message /!\ si valide /!\ |
| `/verify <id>`                                  | récupère les données du stockage et vérifie la signature           |
| `/verify_all`                                   | récupère et vérifie **tous** les objets, puis affiche un résumé    |
| `/tamper <id>`                                  | demande au serveur d'altérer un objet stocké                       |
| `/send_file <username> <fichier>`               | signe et envoie un fichier (depuis `files_storage/to_send/`)       |
| `/get_file <id> <fichier>`                      | vérifie et écrit le fichier si valide (dans `files_storage/received/`) |
| `/exit`                                         | quitte le client                                                   |

## 5. Séquence de démonstration
Pour la démo, on fait:
- connection + génération des clés
- L'objet est signé et stocké
- L'objet est réupéré sur le stockage et vérifié (VALID)
- Le contenu de l'objet stoqué est altéré `/tamper`
- Vérification: le contenu ne correspond plus à la signature (INVALID)
- Possibilité d'altérer manuellement depuis un autre terminal

```
# --- message texte ---
/connect
/generate_keys Davide
/send_text Davide object_title1 Hello world
/list
/get 1              -> signature VALID
/tamper 1
/get 1              -> signature INVALID
/verify 1           -> signature INVALID
/verify_all         -> résumé, ex. "1 VALID / 1 INVALID (sur 2)"

# --- fichier signé ---
/send_file Davide secret.txt               -> objet id 2 (lu depuis files_storage/to_send/)
/get_file 2 recu.txt                       -> VALID, écrit dans files_storage/received/recu.txt
/tamper 2
/get_file 2 recu2.txt                      -> INVALID, fichier NON écrit
/verify_all         -> résumé, ex. "1 VALID / 1 INVALID (sur 2)"

# --- altération manuelle ---
/send_text Davide object_title1 Hello world2
/get 3              -> signature VALID
# terminal 3 :
printf 'corrompu' > server_storage/object_3/content.bin
# terminal client :
/verify 3           -> signature INVALID
```

## 6. Le protocole SFX
 
Chaque message est une trame binaire :
 
```
[HEADER][TYPE][LENGTH][PAYLOAD]
  3 o     1 o    4 o     N octets
```
 
- **HEADER** : les 3 octets `SFX` (toute autre valeur = trame rejetée)
- **TYPE** : `S` submit, `L` list, `G` get, `T` tamper, `O` ok, `E` erreur
- **LENGTH** : taille du payload, entier non signé 4 octets big-endian
- **PAYLOAD** : 
  - un objet JSON en UTF-8
  - les champs binaires (message, signature, clé publique) sont encodés en Base64
  

  À la lecture :
  - un `recv()` peut renvoyer moins d'octets que demandé, donc on boucle jusqu'à obtenir exactement les 8 octets fixes 
  - puis exactement LENGTH  octets.
  - Toute trame dont LENGTH dépasse 1 Mo est rejetée.

## 7. La cryptographie
- **Hachage :** SHA-256
- **Signature :** RSA 2048 bits, padding PKCS#1 v1.5, hachage interne SHA-256
- Librairie utilisée `cryptography` 
- message signé: `sign_message(SK_SHA-256, octets bruts du message)`
- la clé privée ne quitte jamais le client -> uniquement utiliser pour signer

## 8. Les limites: Intégrité n'est pas égal à Identité
- La clé public est encapsulé dans le payload
- la vérification `verify_signature(public_key, message_bytes, signature)` prouve l'intégrité
- elle ne prouve pas l'identité (le champs `sender` n'est pas vérifié) donc
  n'importe qui peut générer une paire
- Pour vérifier l'identité, il faudrait un `PKI` (Public Key Infrastructure)
  qui lie un clé publique <-> identité

## 9. Fichiers signés
- signe le fichier au lieu d'un message tapé
- la seule différence est la source des octets: le contenu d'un fichier au lieu d'un texte tapé
- `/send_file <username> <fichier>` : lit le fichier depuis `files_storage/to_send/`, le signe, et l'envoie comme un
  objet signé normal. Le nom du fichier sert aussi d'`object_name` (par simplification)
- `/get_file <id> <fichier>` : récupère l'objet, vérifie la signature, et si valide, écrit le contenu dans le fichier

## 10. Pourquoi pas de "RSA maison" en production
- Aucun padding : RSA brut `pow(m, e, n)`, sans PKCS#1 -> signature déterministe et malléable (falsifiable).
- Ne pas chiffrer par caractère (`ord(c)`) : même lettre -> même chiffré, cassable par analyse de fréquence.
- ne pas utiliser `random` (non sûr), mais la fonction `secrets`.

-> donc utiliser `cryptography` qui est optimisé et sécurisé.