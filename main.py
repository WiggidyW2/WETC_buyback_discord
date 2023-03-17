#!/usr/bin/env python3

import discord

import subprocess
import itertools
import json
import os

LOCATIONS = {
    '1dq': '1DQ',
    'dlv': 'Delve',
    'qur': 'Querious',
    'pbs': 'Period Basis',
    'snd': 'Senda',
}

def client():
    intents = discord.Intents.default()
    intents.message_content = True
    return discord.Client(intents=intents)
CLIENT = client()

def help_message():
    s = '```"!pricehash 16char_hash_code": list the appraisal linked to ' +\
        'this hashcode\n"!pricehelp": list available commands\n'
    for location_code, location in LOCATIONS.items():
        s += '"!price{} paste_items_here": make an appraisal in {}\n'.format(
            location_code,
            location,
        )
    s += '```'
    return s
HELP_MESSAGE = help_message()

def price_message(data, contract=True):
    total_price = 0.0

    spacing = [4, 4, 4]

    for item in itertools.chain(data['accepted'], data['rejected']):
        name = item['name']
        quantity = '{:,}'.format(item['quantity'])
        price_per = '{:,.2f}'.format(item.get('price_per', 0.0))
        if len(name) > spacing[0]:
            spacing[0] = len(name)
        if len(quantity) > spacing[1]:
            spacing[1] = len(quantity)
        if len(price_per) > spacing[2]:
            spacing[2] = len(price_per)

    s = '```ACCEPTED ITEMS\nITEM{}QUANTITY{}PRICE PER{}PRICE TOTAL\n'.format(
        ' ' * spacing[0],
        ' ' * (spacing[1] - 4),
        ' ' * (spacing[2] - 5),
    )
    for item in data['accepted']:
        total_price += item['price_total']
        name = item['name']
        quantity = '{:,}'.format(item['quantity'])
        price_per = '{:,.2f}'.format(item['price_per'])
        price_total = '{:,.2f}'.format(item['price_total'])
        s += '{}{}{}{}{}{}{}\n'.format(
            name,
            ' ' * (spacing[0] + 4 - len(name)),
            quantity,
            ' ' * (spacing[1] + 4 - len(quantity)),
            price_per,
            ' ' * (spacing[2] + 4 - len(price_per)),
            price_total,
        )

    s += '\nREJECTED ITEMS\nITEM{}QUANTITY\n'.format(
        ' ' * spacing[0],
    )
    for item in data['rejected']:
        name = item['name']
        quantity = '{:,}'.format(item['quantity'])
        s += '{}{}{}\n'.format(
            name,
            ' ' * (spacing[0] + 4 - len(name)),
            quantity,
        )

    s += '\nLOCATION: {}\nTOTAL: {:,.2f}\nHASH: {}```'.format(
        data['location'],
        total_price,
        data['hash'],
    )

    if contract and total_price > 0.0:
        s += '\nContract to "**War Eagle Trading Co.**" for the amount ' +\
            '"**{:,.2f}**" and put "**{}**" in the note.'.format(
                total_price,
                data['hash'],
            )
    
    return s

def try_calculate(data, contract=True):
    try:
        return price_message(run_backend(data), contract)
    except Exception as e:
        # raise e
        return 'ERROR\n{}'.format(e)

def run_backend(data):
    p = subprocess.Popen(
        './backend.exe',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
        env=os.environ,
    )
    data = bytes(json.dumps(data, separators=(',', ':')), 'utf8')
    out, err = p.communicate(input=data, timeout=60)
    if p.returncode != 0:
        raise Exception(err.decode('utf8'))
    else:
        return json.loads(out.decode('utf8'))

@CLIENT.event
async def on_message(message):
    if not message.content.startswith('!price'):
        return

    elif message.author == CLIENT.user:
        return

    elif message.content.startswith('help', 6):
        await message.channel.send(HELP_MESSAGE)
        return

    elif message.content.startswith('hash', 6):
        if len(message.content) >= 27:
            out_message = try_calculate({
                'hash': message.content[11:27],
            })
            await message.channel.send(out_message)
            return

    elif len(message.content) >= 9:
        location = LOCATIONS.get(message.content[6:9])
        if location is not None:
            out_message = try_calculate({
                'location': location,
                'raw': message.content[9:].replace('    ', '\t'),
            })
            await message.channel.send(out_message)
            return

    await message.channel.send(
        'Invalid command. To see available commands, type "!pricehelp".'
    )

def main():
    token = os.environ['BBDI_DISCORDTOKEN']
    CLIENT.run(token)

if __name__ == '__main__':
    main()
