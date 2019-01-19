#!/usr/bin/env python

# http://qiita.com/teitei_tk/items/0b8bae99a8700452b718
# Change1: BUG fixed in if branch in AESCipher.encrypt
# Change2: change formats of returned value to binary.

CHECK_BLOCK_INFLUENCE = False

import base64
from Crypto import Random
from Crypto.Cipher import AES
import binascii
import string, random


class AESCipher(object):
    def __init__(self, key, block_size=16):
        self.bs = block_size
        #if len(key) >= len(str(block_size)):
        if len(key) >= block_size:
            self.key = key[:block_size]
        else:
            self.key = self._pad(key)

    def encrypt(self, raw):
        raw = self._pad(raw)
        cipher = AES.new(self.key, AES.MODE_ECB)
        result = str(bin(int.from_bytes(cipher.encrypt(raw),
                                        byteorder='big')))[2:]
        if len(result)%128 != 0:
            # 16*n bytes -> str(128*n bits binary)
            result = '0'*(128-(len(result)%128)) + result
        return result

    def decrypt(self, enc):
        #enc = base64.b64decode(enc)
        # str(128bits binary) -> 16 bytes
        enc = int(enc, 2).to_bytes(int(len(enc)/8), byteorder='big')
        cipher = AES.new(self.key, AES.MODE_ECB)
        return self._unpad(cipher.decrypt(enc))

    def _pad(self, s):
        s += ((self.bs - len(s) % self.bs) * chr(self.bs - len(s)
              % self.bs))
        return s

    def _unpad(self, s):
        return s[:-ord(s[len(s)-1:])]


def generate_key(num=50):  # generate key
    return ''.join(
            [random.choice(string.ascii_letters + string.digits)
                for i in range(num)]
            )


if __name__ == '__main__':
    ########## How to Use ##########
    # generate AES environment for key
    cipher = AESCipher(generate_key())

    # encryption
    enc = cipher.encrypt('WESTLaB!WESTLaBWESTLaB!WESTLaB!')
    print(enc)

    if CHECK_BLOCK_INFLUENCE:
        list_enc = list(enc)
        for cnt, l in enumerate(list_enc):
            if cnt == 126:
                break
            rev = int(l)^1
            if cnt%2:
                list_enc[cnt] = str(rev)
        enc = ''.join(list_enc)

    print(cipher.decrypt(enc))  # decryption
