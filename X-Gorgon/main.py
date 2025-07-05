# coding:utf-8
import hashlib
import json
from time import time
from hashlib import md5
from copy import deepcopy
from random import choice
from termcolor import colored

# Banner
secure_tools = """                                                                                              
E F U S S Y O 
    X-GORGON ^ X-KHRONOS
"""

print(colored(secure_tools, "cyan"))
print(colored("X-Gorgon / X-Khronos Generator", "green"))
print(colored("by @efussyo", "yellow"))

# Utilities
def hex_string(num):
    return hex(num)[2:].zfill(2)

def reverse(num):
    tmp = hex(num)[2:].zfill(2)
    return int(tmp[1:] + tmp[:1], 16)

def RBIT(num):
    bits = bin(num)[2:].zfill(8)
    return int(bits[::-1], 2)

# Gorgon Generator
class XG:
    def __init__(self, debug):
        self.length = 0x14
        self.debug = debug
        self.hex_CE0 = [
            0x05, 0x00, 0x50,
            choice(range(0, 0xFF)),
            0x47, 0x1E, 0x00,
            8 * choice(range(0, 0x1F)),
        ]

    def addr_BA8(self):
        tmp = ""
        hex_BA8 = list(range(256))
        for i in range(256):
            A = hex_BA8[i - 1] if i != 0 else 0
            B = self.hex_CE0[i % 8]
            if A == 0x05 and i != 1 and tmp != 0x05:
                A = 0
            C = (A + i + B) % 256
            tmp = C if C < i else ""
            hex_BA8[i] = hex_BA8[C]
        return hex_BA8

    def initial(self, debug, hex_BA8):
        tmp_hex = deepcopy(hex_BA8)
        tmp_add = []
        for i in range(self.length):
            A = debug[i]
            B = tmp_add[-1] if tmp_add else 0
            C = (hex_BA8[i + 1] + B) % 256
            tmp_add.append(C)
            D = tmp_hex[C]
            tmp_hex[i + 1] = D
            E = (D * 2) % 256
            F = tmp_hex[E]
            debug[i] = A ^ F
        return debug

    def calculate(self, debug):
        for i in range(self.length):
            A = debug[i]
            B = reverse(A)
            C = debug[(i + 1) % self.length]
            D = B ^ C
            E = RBIT(D)
            F = E ^ self.length
            G = (~F + (1 << 32)) % (1 << 32)
            debug[i] = int(hex(G)[-2:], 16)
        return debug

    def main(self):
        result = "".join(hex_string(i) for i in self.calculate(self.initial(self.debug, self.addr_BA8())))
        return "8402{}{}{}{}{}".format(
            hex_string(self.hex_CE0[7]),
            hex_string(self.hex_CE0[3]),
            hex_string(self.hex_CE0[1]),
            hex_string(self.hex_CE0[6]),
            result,
        )

# Final public function
def getxg(param="", stub="", cookie=""):
    gorgon = []
    ttime = int(time())

    url_md5 = md5(param.encode()).hexdigest()
    gorgon += [int(url_md5[2 * i:2 * i + 2], 16) for i in range(4)]

    stub_md5 = md5(stub.encode()).hexdigest() if stub else "00000000000000000000000000000000"
    gorgon += [int(stub_md5[2 * i:2 * i + 2], 16) for i in range(4)]

    cookie_md5 = md5(cookie.encode()).hexdigest() if cookie else "00000000000000000000000000000000"
    gorgon += [int(cookie_md5[2 * i:2 * i + 2], 16) for i in range(4)]

    gorgon += [0x0, 0x8, 0x10, 0x9]

    Khronos = hex(ttime)[2:].zfill(8)
    gorgon += [int(Khronos[2 * i:2 * i + 2], 16) for i in range(4)]

    return {
        "X-Gorgon": XG(gorgon).main(),
        "X-Khronos": str(ttime),
    }

# Example usage
def main():
    param = input(colored("Enter URL parameters (e.g., device_id=123...): ", "yellow"))
    stub = input(colored("Enter POST data (or leave blank): ", "yellow"))
    cookie = input(colored("Enter cookie string (or leave blank): ", "yellow"))
    headers = getxg(param, stub, cookie)
    print(colored("\nGenerated Headers:", "cyan"))
    print(colored(f"X-Gorgon  : {headers['X-Gorgon']}", "green"))
    print(colored(f"X-Khronos : {headers['X-Khronos']}", "green"))

if __name__ == "__main__":
    main()
