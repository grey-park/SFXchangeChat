"""
RSA textbook par codepoint Unicode.
Cles : n = p.q, e coprime avec phi(n), d = e^-1 mod phi(n).
Signe : s = m^d mod n (cle privee).  Verifie : m = s^e mod n (cle publique).
"""

import secrets
import math

def _is_prime(n: int, k: int = 10) -> bool:
    """Test de primalite Miller-Rabin."""
    if n < 2:
        return False
    if n == 2 or n == 3:
        return True
    if n % 2 == 0:
        return False

    r, d = 0, n - 1
    while d % 2 == 0:
        r += 1
        d //= 2

    for _ in range(k):
        a = secrets.randbelow(n - 3) + 2
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True

def _generate_prime(bits: int) -> int:
    while True:
        n = secrets.randbits(bits) | (1 << (bits - 1)) | 1
        if _is_prime(n):
            return n


def rsa_generate(bits: int = 512) -> dict:
    """Genere une paire RSA. `bits` = taille du modulus n (chaque premier = bits/2)."""
    half = bits // 2
    p = _generate_prime(half)
    q = _generate_prime(half)
    while q == p:
        q = _generate_prime(half)

    n = p * q
    phi = (p - 1) * (q - 1)
    e = 65537
    if math.gcd(e, phi) != 1:
        e = 3
        while math.gcd(e, phi) != 1:
            e += 2
    d = pow(e, -1, phi)   # inverse modulaire : d = e^-1 mod phi
    return {"n": n, "e": e, "d": d}

def rsa_sign(m: int, d: int, n: int) -> int:
    """Signe avec la cle privee : s = m^d mod n."""
    return pow(m, d, n)

def rsa_verify(s: int, e: int, n: int) -> int:
    """Verifie avec la cle publique : m = s^e mod n (a comparer a l'original)."""
    return pow(s, e, n)


if __name__ == "__main__":
    cle = rsa_generate(512)

    m = ord("H")  # 72, a signer
    s = rsa_sign(m, cle["d"], cle["n"])   # signature
    print("signature valide :", rsa_verify(s, cle["e"], cle["n"]) == m)
    print("detecte une modification :", rsa_verify(s, cle["e"], cle["n"]) != ord("X"))