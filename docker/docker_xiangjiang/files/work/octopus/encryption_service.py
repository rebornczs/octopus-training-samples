# -*- coding: utf-8 -*-
from Crypto.Cipher import PKCS1_v1_5 as cipher_pkcs1_v1_5
from Crypto.PublicKey import RSA
import base64
from conf.common.global_logger import logger


class OctpsEncryptor:
    """
    本类使用RSA进行加解密， 并可产生公钥和私钥文件
    """

    def __init__(self, length=1024):
        self.rsa = RSA.generate(length)

    def gen_keys(self, public_key_file_path, private_key_file_path):
        try:
            # 生成私钥
            private_pem = self.rsa.exportKey()
            with open(private_key_file_path, 'wb') as f:
                f.write(private_pem)
                f.close()
            # 生成公钥
            public_pem = self.rsa.publickey().exportKey()
            with open(public_key_file_path, 'wb') as f:
                f.write(public_pem)
                f.close()
            return True
        except Exception as e:
            logger.error('Error when generating public and private rsa keys')
            logger.exception(e)
            return False

    # 将密文(私钥)解密成明文(公钥)
    @staticmethod
    def decrypt(private_key_file_path, encrypted_message):
        with open(private_key_file_path) as f:
            private_pem = f.read()
            f.close()
        private_key = RSA.importKey(private_pem)
        cipher = cipher_pkcs1_v1_5.new(private_key)
        content = cipher.decrypt(base64.b64decode(encrypted_message), None)
        return content.decode('utf-8')

    # 将明文(公钥)加密成密文(私钥)
    @staticmethod
    def encrypt(public_key_file_path, message):
        with open(public_key_file_path) as f:
            public_pem = f.read()
            f.close()
        public_key = RSA.importKey(public_pem)
        cipher = cipher_pkcs1_v1_5.new(public_key)
        encrypted_message = base64.b64encode(cipher.encrypt(message))
        return encrypted_message.decode('utf-8')
