import base64
import ctypes
import hashlib
from os import urandom

from pkcs7_padding import padding_size, pkcs7_padding_pad_buffer


def md5bytes(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def set_type_data(ptr, index, data, data_type):
    if data_type == "uint64_t":
        ptr[index * 8: (index + 1) * 8] = data.to_bytes(8, "little")
    else:
        raise ValueError("Invalid data type")


def validate(num):
    return num & 0xFFFFFFFFFFFFFFFF


def __ROR__(value: ctypes.c_ulonglong, count: int) -> ctypes.c_ulonglong:
    nbits = ctypes.sizeof(value) * 8
    count %= nbits
    low = ctypes.c_ulonglong(value.value << (nbits - count)).value
    value = ctypes.c_ulonglong(value.value >> count).value
    return value | low


def encrypt_ladon_input(hash_table, input_data):
    data0 = int.from_bytes(input_data[:8], byteorder="little")
    data1 = int.from_bytes(input_data[8:], byteorder="little")

    for i in range(0x22):
        hash = int.from_bytes(hash_table[i * 8: (i + 1) * 8], byteorder="little")
        data1 = validate(hash ^ (data0 + ((data1 >> 8) | (data1 << (64 - 8)))))
        data0 = validate(data1 ^ ((data0 >> 0x3D) | (data0 << (64 - 0x3D))))

    output_data = bytearray(16)
    output_data[:8] = data0.to_bytes(8, byteorder="little")
    output_data[8:] = data1.to_bytes(8, byteorder="little")
    return bytes(output_data)


def encrypt_ladon(md5hex: bytes, data: bytes, size: int):
    hash_table = bytearray(272 + 16)
    hash_table[:32] = md5hex

    temp = []
    for i in range(4):
        temp.append(int.from_bytes(hash_table[i * 8: (i + 1) * 8], byteorder="little"))

    buffer_b0 = temp[0]
    buffer_b8 = temp[1]
    temp.pop(0)
    temp.pop(0)

    for i in range(0x22):
        x9 = buffer_b0
        x8 = buffer_b8
        x8 = validate(__ROR__(ctypes.c_ulonglong(x8), 8))
        x8 = validate(x8 + x9)
        x8 = validate(x8 ^ i)
        temp.append(x8)
        x8 = validate(x8 ^ __ROR__(ctypes.c_ulonglong(x9), 61))
        set_type_data(hash_table, i + 1, x8, "uint64_t")
        buffer_b0 = x8
        buffer_b8 = temp[0]
        temp.pop(0)

    new_size = padding_size(size)

    input_buf = bytearray(new_size)
    input_buf[:size] = data
    pkcs7_padding_pad_buffer(input_buf, size, new_size, 16)

    output = bytearray(new_size)
    for i in range(new_size // 16):
        output[i * 16: (i + 1) * 16] = encrypt_ladon_input(hash_table, input_buf[i * 16: (i + 1) * 16])

    return output


def ladon_encrypt(timestamp: int, license_id: int = 1611921764, aid: int = 1233, random_bytes: bytes = None) -> str:
    if random_bytes is None:
        random_bytes = urandom(4)

    data = f"{timestamp}-{license_id}-{aid}"
    keygen = random_bytes + str(aid).encode()
    md5hex = md5bytes(keygen)

    size = len(data)
    new_size = padding_size(size)

    output = bytearray(new_size + 4)
    output[:4] = random_bytes
    output[4:] = encrypt_ladon(md5hex.encode(), data.encode(), size)

    return base64.b64encode(output).decode()


class Ladon:
    @staticmethod
    def encrypt(timestamp: int, license_id: int = 1611921764, aid: int = 1233) -> str:
        return ladon_encrypt(timestamp, license_id, aid)


if __name__ == "__main__":
    import time

    print("=== X-Ladon Encryptor ===\n")

    try:
        ts = int(input("Enter timestamp (or leave blank for current): ") or int(time.time()))
        license_id = int(input("Enter license ID (default 1611921764): ") or "1611921764")
        aid = int(input("Enter AID (default 1233): ") or "1233")
    except Exception as e:
        print(f"[!] Invalid input: {e}")
        exit(1)

    ladon = ladon_encrypt(timestamp=ts, license_id=license_id, aid=aid)

    print("\n=== Result ===")
    print("X-Ladon:", ladon)
