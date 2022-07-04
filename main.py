import requests
import hashlib
import os
import binascii
import base58
import ecdsa
import discord
import json
import decimal
from decouple import config
from requests import Session


token = config('token')
client = discord.Client()
headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': config('api_key'),
}


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$random'):
        content = message.content.split(' ')
        if len(content) > 1 and content[1].isdigit() and int(content[1]) > 0:
            msg = random(int(content[1]))
        else:
            msg = random()
        await message.channel.send(msg)

    if message.content.startswith('$p'):
        msg = message.content.split(' ')
        url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'

        parameters = {
            'symbol': msg[1]
        }

        session = Session()
        session.headers.update(headers)

        try:
            response = session.get(url, params=parameters)
            data = json.loads(response.text)
            info = data['data'][msg[1].upper()]
            price = (round(info['quote']['USD']['price'], 2) if info['quote']['USD']['price'] >= 1 else decimal.Decimal(info['quote']['USD']['price']))
            await message.channel.send(f'{msg[1]} {price}$\n'
                                       f"1h change: {info['quote']['USD']['percent_change_1h']}%\n"
                                       f"24h change: {info['quote']['USD']['percent_change_24h']}%")
        except Exception as e:
            await message.channel.send(f'error: {e}')


def ripemd160(x):
    d = hashlib.new('ripemd160')
    d.update(x)
    return d


def random(number=10):
    wallets = {}

    for i in range(number):
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
