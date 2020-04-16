import os
import subprocess

import click

import noobit.exchanges
import noobit.models.templates
import noobit_user.strategies

@click.command()
@click.option("--exchange", default="kraken", help="Lowercase exchange")
@click.option("--ide",
              default="code",
              help='Name of IDE (only supports vim and vscode so far)',
              type=click.Choice(["vim", "code"], case_sensitive=False)
              )
def open_env_file(exchange, ide):
    dir_path = os.path.dirname(noobit.exchanges.__file__)
    full_path = f"{dir_path}/{exchange}/rest/.env"
    subprocess.call([ide, full_path])


@click.command()
@click.option("--name", help="File name of strategy to create")
@click.option("--ide",
              default="code",
              help='Name of IDE (only supports vim and vscode so far)',
              type=click.Choice(["vim", "code"], case_sensitive=False)
              )
def create_user_strategy(name, ide):
    template_strat_dir = os.path.dirname(noobit.models.templates.__file__)
    user_strat_dir = os.path.dirname(noobit_user.strategies.__file__)

    destination_path = f"{user_strat_dir}/{name}.py"
    with open(f"{template_strat_dir}/strategy.py", mode="r") as source:
        with open(destination_path, mode="w") as destination:
            for line in source:
                destination.write(line)

    subprocess.call([ide, destination_path])
