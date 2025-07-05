import hashlib
import time
import base64
import struct
from urllib.parse import parse_qs
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from sm3 import sm3_hash  # from earlier SM3 implementation
from simon import simon_enc
from protobuf import ProtoBuf

def encrypt_enc_pb(data: bytes) -> bytes:
    return data[::-1]

class Argus:
    @staticmethod
    def get_bodyhash(stub):
        return sm3_hash(b'')[0:6] if not stub else sm3_hash(bytes.fromhex(stub))[0:6]

    @staticmethod
    def get_queryhash(query):
        return sm3_hash(b'')[0:6] if not query else sm3_hash(query.encode())[0:6]

    @staticmethod
    def encrypt(xargus_bean):
        pb = ProtoBuf(xargus_bean).toBuf()
        padded = pad(pb, AES.block_size)
        sm3_out = sm3_hash(padded)
        key = sm3_out[:32]
        k0, k1 = struct.unpack('<QQ', key[:16]), struct.unpack('<QQ', key[16:32])

        enc = bytearray()
        for i in range(0, len(padded), 16):
            block = padded[i:i+16]
            pt = struct.unpack('<QQ', block)
            ct = simon_enc(list(pt), [k0[0], k0[1], k1[0], k1[1]])
            enc += ct[0].to_bytes(8,'little') + ct[1].to_bytes(8,'little')

        data = b'\xf2\xf7\xfc\xff\xf2\xf7\xfc\xff' + enc
        data = b'\xa6n\xad\x9fw\x01\xd0\x0c\x18' + data + b'ao'

        sign_key = bytes(range(32))  # replace with your key
        cipher = AES.new(hashlib.md5(sign_key[:16]).digest(), AES.MODE_CBC,
                         hashlib.md5(sign_key[16:]).digest())
        x = b'\xf2\x81' + cipher.encrypt(pad(data, AES.block_size))
        return base64.b64encode(x).decode()

    @staticmethod
    def get_sign(params, stub, timestamp, aid, license_id, platform, sdk_version, sdk_version_int, sec_device_id):
        qs = parse_qs(params)
        bean = {
            1: (0x20200929 << 1),
            2: 2,
            3: randint(0, 0x7FFFFFFF),
            4: str(aid),
            5: qs.get('device_id',[''])[0],
            6: str(license_id),
            7: qs.get('version_name',[''])[0],
            8: sdk_version,
            9: sdk_version_int,
            10: b'\x00'*8,
            11: platform,
            12: timestamp << 1,
            13: Argus.get_bodyhash(stub),
            14: Argus.get_queryhash(params),
            15: {1:1,2:1,3:1,7:3348294860},
            16: sec_device_id,
            20: "none",
            21: 738,
            23: {1:"NX551J",2:8196,4:2162219008},
            25:2
        }
        return Argus.encrypt(bean)

if __name__ == "__main__":
    from random import randint
    print("=== X-Argus Generator ===")
    params = input("Enter query string params: ")
    stub = input("Enter stub hex (or blank): ")
    ts = int(input("Timestamp (leave blank = now): ") or time.time())
    aid = int(input("AID (default 1233): ") or "1233")
    lid = int(input("License ID (default 1611921764): ") or "1611921764")
    plat = int(input("Platform ID (default 0): ") or "0")
    sdk = input("SDK version (default 'v04.04.05-ov-android'): ") or "v04.04.05-ov-android"
    sdk_int = int(input("SDK version int (default 134744640): ") or "134744640")
    secdev = input("secDeviceID (blank for none): ")

    xargus = Argus.get_sign(params, stub, ts, aid, lid, plat, sdk, sdk_int, secdev)
    print("\nX-Argus:", xargus)
