from Crypto.Util import number
from secrets import randbelow
from generator_function import find_g
p = number.getPrime(256)
g = find_g(p)
q = p-1

def generate_secret_key(q):
    return randbelow(q)

def generate_nonce(q):
    return randbelow(q)

def generate_public_key(secret_key,generator):
    return pow(generator,secret_key,p)


def generate_t(r):
    return pow(g,r,p)

def generate_c():
    return c

def compute_value_s(c):
    return r + (c*x)%(p-1)

def Verify(gs, tycmodp):
    if gs == tycmodp:
        return True
    else:
        return False

