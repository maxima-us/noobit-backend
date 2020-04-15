import asyncio
import os
import subprocess

import aiofiles
import click

import noobit.exchanges

@click.command()
@click.option("--exchange", default="kraken", help="Lowercase exchange")
@click.option("--ide",
              default="code",
              help='Name of ID (only supports vim and vscode so far)',
              type=click.Choice(["vim", "code"], case_sensitive=False)
              )
def open_env_file(exchange, ide):
    dir_path = os.path.dirname(noobit.exchanges.__file__)
    full_path = f"{dir_path}/{exchange}/rest/.env"
    subprocess.call([ide, full_path])



#! BELOW DOEST NOT WORK BECAUSE WE CANT WRITE TO ENV FILES

@click.command()
@click.option("--exchange", default="kraken", help="Lowercase exchange")
def add_key(exchange):
    try:
        asyncio.run(_prompt(exchange))
    except Exception as e:
        print(e)

async def _prompt(exchange):
    api_key_value = input('Enter Api Key:')
    api_secret_value = input('Enter Api Secret:')

    dir_path = os.path.dirname(os.path.abspath(__file__))

    try:
        file_path = f"{dir_path}/keys/{exchange}"
    except:
        os.mkdir(file_path)

    print(file_path)
    print(dir_path)

    async with aiofiles.open(f'{file_path}/.env', mode='a') as f:
        lines = await f.readlines()
        n_lines = (len(lines) + 1) * 0.5

        api_key_name = f"{exchange.upper()}_{n_lines}_API_KEY"
        api_secret_name = f"{exchange.upper()}_{n_lines}_API_SECRET"

        first_line = f"{api_key_name}={api_key_value}"
        second_line = f"{api_secret_name}={api_secret_value}"

        await f.writelines([first_line, second_line])
