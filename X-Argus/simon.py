from ctypes import c_ulonglong

def rotate_left(v, n):
    return ((v << n) | (v >> (64 - n))) & 0xFFFFFFFFFFFFFFFF

def rotate_right(v, n):
    return ((v >> n) | (v << (64 - n))) & 0xFFFFFFFFFFFFFFFF

def key_expansion(key):
    for i in range(4, 72):
        tmp = rotate_right(key[i - 1], 3)
        tmp ^= key[i - 3]
        tmp ^= rotate_right(tmp, 1)
        key.append(c_ulonglong(~key[i - 4]).value ^ tmp ^ ((0x3DC94C3A046D678B >> ((i - 4) % 62)) & 1) ^ 3)
    return key

def simon_enc(pt, k):
    key = key_expansion(k.copy())
    x, y = pt
    for i in range(72):
        tmp = x
        f = rotate_left(x, 1) & rotate_left(x, 8)
        x = y ^ f ^ rotate_left(x, 2) ^ key[i]
        y = tmp
    return [x, y]
