import hashlib
import base64
import binascii
import os
import execjs

from base64 import b64decode
from base64 import b64encode
from Crypto.Cipher import DES
from Crypto.PublicKey import RSA
try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad, unpad
except ImportError:
    print('请安装加解密库pycryptodome')

try:
    from Crypto.Cipher import AES
    from Crypto.Cipher import PKCS1_v1_5 as Cipher_pksc1_v1_5
except Exception as e:
    print(e)
    pass

__all__ = ['md5']


def md5(pwd):
    """ md5加密 """
    return hashlib.md5(pwd.encode("utf8")).hexdigest()


def base64_aes_encrypt(plain_text, key):
    """
    base64编码 对称加密 AES_ECB
    :param plain_text: 待加密的明文
    :param key: 秘钥
    :return:  加密后的数据
    """
    aes2 = AES.new(key.encode('utf-8'), AES.MODE_ECB)
    encrypt_text = aes2.encrypt(pad(plain_text.encode('utf-8'), AES.block_size, style='pkcs7'))
    encrypt_text = str(base64.encodebytes(encrypt_text), encoding='utf-8').replace("\n", "")
    return encrypt_text


def base64_rsa_encrypt(plain_text, public_key):
    """
    base64编码非对称加密
    :param plain_text: 明文
    :type plain_text:str
    :param public_key:公钥
    :type public_key:str
    :return:公钥加密后的密文
    :rtype:str
    """
    rsa_key = RSA.importKey(public_key)
    cipher = Cipher_pksc1_v1_5.new(rsa_key)
    cipher_text = base64.b64encode(cipher.encrypt(plain_text.encode()))
    return cipher_text.decode()


BLOCK_SIZE = 8  # Bytes

class DESCipher:
    """ 进行 des 加密 解密 """

    def __init__(self, key, model='ECB', iv=''):
        self.key = key.encode('utf-8')
        self.mode = model
        self.iv = iv.encode()
        if model == 'ECB':
            self.des = DES.new(self.key, DES.MODE_ECB)  # 创建一个aes对象
        elif model == 'CBC':
            self.des = DES.new(self.key, DES.MODE_CBC, self.iv)

    def pad(self, s):
        return s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * chr(BLOCK_SIZE - len(s) % BLOCK_SIZE)

    def unpad(self, s):
        return s[:-ord(s[len(s) - 1:])]

    def encrypt(self, raw):
        raw = self.pad(raw).encode('utf8')
        cipher = self.des
        EncryptStr = cipher.encrypt(raw)
        return base64.b64encode(EncryptStr).decode()  # 转base64编码返回

    def decrypt(self, enc):
        crypted_str = base64.b64decode(enc)
        cipher = self.des
        result = cipher.decrypt(crypted_str)
        result = self.unpad(result).decode('utf8')
        return result


class AESCipher(object):
    """ 进行 aes 加密 解密 """
    def __init__(self, key, model='ECB', iv=''):
        self.mode = model
        self.key = key.encode('utf-8')
        self.iv = iv.encode()
        if model == 'ECB':
            self.aes = AES.new(self.key, AES.MODE_ECB)  # 创建一个aes对象
        elif model == 'CBC':
            self.aes = AES.new(self.key, AES.MODE_CBC, self.iv)

    def add_16(self,par):
        # python3字符串是unicode编码，需要 encode才可以转换成字节型数据
        par = par.encode('utf-8')
        while len(par) % 16 != 0:
            par += b'\x00'
        return par

    def encrypt(self, data):
        # pad_pkcs7 = pad(data.encode('utf-8'), AES.block_size, style='pkcs7')
        pad_pkcs7 = pad(data.encode('utf-8'), AES.block_size, style='pkcs7')
        result = base64.encodebytes(self.aes.encrypt(pad_pkcs7))
        encrypted_text = str(result, encoding='utf-8').replace('\n', '')
        return encrypted_text

    def decrypt(self, data):
        base64_decrypted = base64.decodebytes(data.encode('utf-8'))
        una_pkcs7 = unpad(self.aes.decrypt(base64_decrypted), AES.block_size, style='pkcs7')
        decrypted_text = str(una_pkcs7, encoding='utf-8')
        return decrypted_text


class RsaEncrypt:
    def __init__(self, public_key):
        public_key = '-----BEGIN PUBLIC KEY-----\n' + public_key + '\n-----END PUBLIC KEY-----'
        rsa_key = RSA.importKey(public_key)
        self.rsa_encrypt = Cipher_pksc1_v1_5.new(rsa_key)

    def encrypt(self, text, encode_type='base64'):
        text = text.encode("utf-8")

        if encode_type == "hex":  # hex 编码
            cipher_text = binascii.hexlify(self.rsa_encrypt.encrypt(text))
        else:  # 默认使用 base64 编码
            cipher_text = base64.b64encode(self.rsa_encrypt.encrypt(text))
        return str(cipher_text, encoding="utf-8")

    # def decrypt(self, text, private_key, encode_type='base64'):
    #     if encode_type == "hex":  # hex 编码
    #         cipher_text = binascii.unhexlify(text)
    #
    #     else:  # 默认使用 base64 编码
    #         cipher_text = base64.b64decode(text)
    #     cipher_text = self.rsa_encrypt.decrypt(cipher_text, private_key)
    #     return str(cipher_text, encoding="utf-8")


class JsSm4Cipher:
    def __init__(self):
        sm4_js_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "sm4_cipher.js")
        with open(sm4_js_path, 'r', encoding='utf-8') as fp:
            js1 = fp.read()
        self.sm4_cipher = execjs.compile(js1)

    def encrypt(self, data, key):
        enc_text = self.sm4_cipher.call("sm4_encrypt", data, key)
        return enc_text

    def encrypt_captchcode(self, data, key, token):
        enc_text = self.sm4_cipher.call("sm4_encrypt_captchcode", data, key, token)
        return enc_text



def get_client_aes_cipher(encrypt_str, type="ECB"):
    aes_Cipher = AESCipher("ab$2efghi826mnop", type)
    encrypt_str = aes_Cipher.encrypt(encrypt_str)
    return encrypt_str


def des_decrypt_str(encrypt_str, type="CBC"):
    key = 'efghi826mnop'
    if len(key) > BLOCK_SIZE:
        _key = key[0:BLOCK_SIZE]
    else:
        _key = key + '0' * (BLOCK_SIZE - len(key))
    des_client = DESCipher(_key, type, _key)
    return des_client.decrypt(encrypt_str)


def des_encrypt_str(decrypt_str, type="CBC"):
    key = 'efghi826mnop'
    if len(key) > BLOCK_SIZE:
        _key = key[0:BLOCK_SIZE]
    else:
        _key = key + '0' * (BLOCK_SIZE - len(key))
    des_client = DESCipher(_key, type, _key)
    return des_client.encrypt(decrypt_str)