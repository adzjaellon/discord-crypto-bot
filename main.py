import requests
import hashlib
import os
import binascii
import base58
import ecdsa
import discord
from decouple import config

token = config('token')

client = discord.Client()


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$random'):
        msg = random()
        await message.channel.send(msg)


def ripemd160(x):
    d = hashlib.new('ripemd160')
    d.update(x)
    return d


def random():
    wallets = {}

    for i in range(10):
        priv_key = os.urandom(32)
        fullkey = '80' + binascii.hexlify(priv_key).decode()
        sha256a = hashlib.sha256(binascii.unhexlify(fullkey)).hexdigest()
        sha256b = hashlib.sha256(binascii.unhexlify(sha256a)).hexdigest()
        WIF = base58.b58encode(binascii.unhexlify(fullkey+sha256b[:8]))

        sk = ecdsa.SigningKey.from_string(priv_key, curve=ecdsa.SECP256k1)
        vk = sk.get_verifying_key()
        publ_key = '04' + binascii.hexlify(vk.to_string()).decode()
        hash160 = ripemd160(hashlib.sha256(binascii.unhexlify(publ_key)).digest()).digest()
        publ_addr_a = b"\x00" + hash160
        checksum = hashlib.sha256(hashlib.sha256(publ_addr_a).digest()).digest()[:4]
        publ_addr_b = base58.b58encode(publ_addr_a + checksum)
        priv = WIF.decode()
        pub = publ_addr_b.decode()
        wallets[priv] = pub

    result = ''

    for (nr, w) in enumerate(wallets):
        result += f"[ {w} ](<https://www.blockchain.com/btc/address/{wallets[w]}>) lol{str(nr)}\n\n"

    balances = []

    for w1 in wallets:
        r = requests.get("https://www.blockchain.com/btc/address/" + wallets[w1])

        if 'The current value of this address is 0.00000000 BTC ($0.00)' in r.text:
            balances.append("(Empty)")
        elif not 'The current value of this address is' in r.text:
            pass
        else:
            print("(Not Empty)", wallets[w1])
            balances.append("(Not Empty)")

    for (nr, b) in enumerate(balances):
        result = result.replace("lol" + str(nr), balances[nr])

    result = result.replace(")0", ")")

    return result


client.run(token)
