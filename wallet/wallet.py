from binascii import a2b_hex, b2a_hex
from hashlib import new, sha256
from os import mkdir, path
from keys import get_pub_key_hex, get_priv_key_hex
from base58 import b58encode, b58decode
from qrcode import make as qr_make
from constants import PUBKEY_HASH, TESTNET_PUBKEY_HASH, WIF, TESTNET_WIF, OP_DUP, OP_HASH_160, OP_EQUALVERIFY, \
    OP_CHECKSIG


def hash_160(pk):
    """ Calculates the RIPEMD-160 hash of a given elliptic curve key.

    :param pk: elliptic curve public key (in hexadecimal format).
    :type pk: hex str
    :return: The RIPEMD-160 hash.
    :rtype: bytes
    """

    # Calculate the RIPEMD-160 hash of the given public key.
    md = new('ripemd160')
    h = sha256(a2b_hex(pk)).digest()
    md.update(h)
    h160 = md.digest()

    return h160


def hash_160_to_btc_address(h160, v):
    """ Calculates the Bitcoin address of a given RIPEMD-160 hash from an elliptic curve public key.

    :param h160: RIPEMD-160 hash.
    :type h160: bytes
    :param v: version (prefix) used to calculate the Bitcoin address.

     Possible values:

        - 0 for main network (PUBKEY_HASH).
        - 111 For testnet (TESTNET_PUBKEY_HASH).
    :type v: int
    :return: The corresponding Bitcoin address.
    :rtype: hex str
    """

    # Add the network version leading the previously calculated RIPEMD-160 hash.
    vh160 = chr(v) + h160
    # Double sha256.
    h = sha256(sha256(vh160).digest()).digest()
    # Add the two first bytes of the result as a checksum tailing the RIPEMD-160 hash.
    addr = vh160 + h[0:4]
    # Obtain the Bitcoin address by Base58 encoding the result
    addr = b58encode(addr)

    return addr


def btc_address_to_hash_160(btc_addr):
    """ Calculates the RIPEMD-160 hash from a given Bitcoin address

    :param btc_addr: Bitcoin address.
    :type btc_addr: str
    :return: The corresponding RIPEMD-160 hash.
    :rtype: hex str
    """

    # Base 58 decode the Bitcoin address.
    decoded_addr = b58decode(btc_addr)
    # Covert the address from bytes to hex.
    decoded_addr_hex = b2a_hex(decoded_addr)
    # Obtain the RIPEMD-160 hash by removing the first and four last bytes of the decoded address, corresponding to
    # the network version and the checksum of the address.
    h160 = decoded_addr_hex[2:-8]

    return h160


def public_key_to_btc_address(pk, v='main'):
    """ Calculates the Bitcoin address of a given elliptic curve public key.

    :param pk: elliptic curve public key.
    :type pk: hex str
    :param v: version used to calculate the Bitcoin address.
    :type v: str
    :return: The corresponding Bitcoin address.

        - main network address if v is 'main.
        - testnet address otherwise
    :rtype: hex str
    """

    # Choose the proper version depending on the provided 'v'.
    if v is 'main':
        v = PUBKEY_HASH
    elif v is 'test':
        v = TESTNET_PUBKEY_HASH
    else:
        raise Exception("Invalid version, use either 'main' or 'test'.")

    # Calculate the RIPEMD-160 hash of the given public key.
    h160 = hash_160(pk)
    # Calculate the Bitcoin address from the chosen network.
    btc_addr = hash_160_to_btc_address(h160, v)

    return btc_addr


def generate_btc_addr(pk, v='main'):
    """ Calculates Bitcoin address associated to a given elliptic curve public key and a given network.

    :param pk: DER encoded public key
    :type pk: bytes
    :param v: version (prefix) used to calculate the WIF, it depends on the type of network.
    :type v: str
    :return: The Bitcoin address associated to the given public key and network.
    :rtype: str
    """

    # Get the hex representation of the provided DER encoded public key.
    public_key_hex = get_pub_key_hex(pk)
    # Generate the Bitcoin address of de desired network.
    btc_addr = public_key_to_btc_address(public_key_hex, v)

    return btc_addr


def private_key_to_wif(sk, mode='image', v='main'):
    """ Generates a Wallet Import Format (WIF) representation of a provided elliptic curve private key.

    :param sk: elliptic curve private key.
    :type sk: hex str
    :param mode: defines the type of return.
    :type mode: str
    :param v: version (prefix) used to calculate the WIF, it depends on the type of network.
    :type v: str
    :return: The WIF representation of the private key.

        - main network WIF if v is 'main'.
        - testnet WIF otherwise.
    :rtype:

        - qrcode is mode is 'image'.
        - str otherwise.
    """

    # Choose the proper version depending on the provided 'v'.
    if v is 'main':
        v = WIF
    elif v is 'test':
        v = TESTNET_WIF
    else:
        raise Exception("Invalid version, use either 'main' or 'test'.")

    # Add the network version leading the private key (in hex).
    e_pkey = chr(v) + a2b_hex(sk)
    # Double sha256.
    h = sha256(sha256(e_pkey).digest()).digest()
    # Add the two first bytes of the result as a checksum tailing the encoded key.
    wif = e_pkey + h[0:4]
    # Enconde the result in base58.
    wif = b58encode(wif)

    # Choose the proper return mode depending on 'mode'.
    if mode is 'image':
        response = qr_make(wif)
    elif mode is 'text':
        response = wif
    else:
        raise Exception("Invalid mode, used either 'image' or 'text'.")

    return response


def generate_wif(btc_addr, mode='image', v='main'):
    """ Generates a Wallet Import Format (WIF) file into disk. Uses an elliptic curve private key from disk as an input
    using the btc_addr associated to the public key of the same key pair as an identifier.

    :param btc_addr: Bitcoin address associated to the public key of the same key pair as the private key.
    :type btc_addr: hex str
    :param mode: defines the type of return.
    :type mode: str
    :param v: version (prefix) used to calculate the WIF, it depends on the type of network.
    :type v: str
    :return: None.
    :rtype: None
    """

    # Get a private key in hex format and create the WIF representation.
    wif = private_key_to_wif(get_priv_key_hex(btc_addr + '/sk.pem'), mode, v)

    # Store the result depending on the selected mode.
    if not path.exists(btc_addr):
        mkdir(btc_addr)

    if mode is 'image':
        wif.save(btc_addr + "/WIF.png")
    elif mode is 'text':
        f = file(btc_addr + "/WIF.txt", 'w')
        f.write(wif)
    else:
        raise Exception("Invalid mode, used either 'image' or 'text'.")


def sign(tx, i, priv, hashcode='SIGHASH_ALL'):
    # ToDo
    pass


def generate_std_scriptpubkey(target_btc_addr):
    """ Generates a standard Bitcoin ScriptPubKey (AKA P2PKH) bound to a target Bitcoin address. A signature from
    the later will be mandatory to redeem the funds locked by the script.

    :param target_btc_addr: A target Bitcoin address necessary to redeem the funds.
    :type target_btc_addr: str
    :return: A hex representation of the desired script.
    :rtype: hex str
    """

    # Obtain the RIPEMD-160 hash of the target Bitcoin address
    h160 = btc_address_to_hash_160(target_btc_addr)
    # Encode the obtained RIPEMD-160 hash in the P2PKH script
    scriptpubkey = format(OP_DUP, 'x') + format(OP_HASH_160, 'x') + format(len(h160) / 2, 'x') + h160 + \
                   format(OP_EQUALVERIFY, 'x') + format(OP_CHECKSIG, 'x')

    return scriptpubkey
