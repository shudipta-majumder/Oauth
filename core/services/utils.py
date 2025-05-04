from pathlib import Path
from typing import Union

from cryptography.hazmat.backends import default_backend as rsa_default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def generate_rsa_key(
    key_size: int = 2048, public_exponent: int = 65537
) -> rsa.RSAPrivateKey:
    """
    Generates a RSA private key with the specified key size and public exponent.

    Args:
        key_size (int, optional): The size of the RSA key in bits. Defaults to 2048.
        public_exponent (int, optional): The public exponent value. Defaults to 65537.

    Returns:
        rsa.RSAPrivateKey: A RSA private key generated with the provided parameters.

    Raises:
        ValueError: If key_size is less than 2048 or not a multiple of 256.
        ValueError: If public_exponent is not an odd integer greater than 2.

    This is a “Hazardous Materials” function. You should ONLY use it if you’re 100% absolutely sure that
    you know what you’re doing because this module is full of land mines, dragons, and dinosaurs with laser guns.

    Reference: `https://cryptography.io/en/latest/hazmat/primitives/asymmetric/rsa/`
    """
    private_key = rsa.generate_private_key(
        public_exponent, key_size, backend=rsa_default_backend()
    )
    return private_key


def save_key(private_key: rsa.RSAPrivateKey, filename: Union[Path, str]):
    pem_file = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )

    with open(filename, "wb") as pemout_file:
        pemout_file.write(pem_file)
