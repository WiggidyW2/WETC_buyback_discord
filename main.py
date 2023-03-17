#!/usr/bin/env python3
import discord

import subprocess
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

def try_calculate(data, contract=True):
    try:
        return price_message(run_backend(data), contract)
    except Exception as e:
        return 'ERROR\n'.format(e)

def run_backend(data):
    p = subprocess.Popen(
        'backend.exe',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
        env=os.environ,
    )
    data = bytes(json.dumps(data, separators=(',', ':')))
    out, err = p.communicate(input=data, timeout=60)
    if p.returncode != 0:
        raise Exception(err.decode('utf8'))
    else:
        return json.loads(out.decode('utf8'))

def price_message(data, contract=True):
    total_price = 0.0

    s = '```accepted items\nitem\tquantity\tprice per\tprice total\n'
    for item in data['accepted']:
        total_price += item['price_total']
        s += '{}\t{}\t{:.2f}\t{:.2f}\n'.format(
            item['name'],
            item['quantity'],
            item['price_per'],
            item['price_total'],
        )

    s += '\nrejected items\nitem\tquantity\n'
    for item in data['rejected']:
        s += '{}\t{}\n'.format(item['name'], item['quantity'])

    s += '\ntotal: {:.2f}\nhash: {}```'.format(total_price, data['hash'])

    if contract and total_price > 0.0:
        s += '\nContract to "War Eagle Trading Co." for the amount ' +\
            '"{:.2f}" and put "{}" in the note.'.format(
                total_price,
                data['hash']
            )

def help_message():
    s = '```"!pricehash": list the appraisal linked to this hashcode\n' +\
        '"!pricehelp": list available commands\n'
    for location_code, location in LOCATIONS.items():
        s += '"!price{}": make an appraisal in {}\n'.format(
            location_code,
            location,
        )
    s += '```\nfor all price appraisals, please followup the command by ' +\
        'pasting the items into the same message.'

HELP_MESSAGE = help_message()

@CLIENT.event
async def on_message(message):
    if not message.content.startswith('!price'):
        return

    elif message.author == CLIENT.user:
        return

    elif message.content.startswith('help', 6):
        message.channel.send(HELP_MESSAGE)
        return

    elif message.content.startswith('hash', 6):
        if message.content.len() >= 27:
            out_message = try_calculate({
                'hash': message.content[11:27],
            })
            await message.channel.send(out_message)
            return

    elif message.content.len() >= 9:
        location = LOCATIONS.get(message.content[6:9])
        if location is not None:
            out_message = try_calculate({
                'location': location,
                'raw': message.content[9:],
            })
            await message.channel.send(out_message)
            return

    await message.channel.send(
        'Invalid command. To see available commands, type "!pricehelp".'
    )

def main():
    CLIENT.run(os.environ['BBD_DISCORDTOKEN'])

if __name__ == '__main__':
    main()
