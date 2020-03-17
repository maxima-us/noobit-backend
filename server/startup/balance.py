'''
Make sure we have the correct balances when starting the bot, and cache them


!!!!!!!!!!!!!!!!!!!
Should we make a separate file for the updates run on shutdown ?
Should we calculate the delta in case there is a balance update ?
(How much the value has changed + or - for each key)

!!!!!!!!!!!!!!!!!!!
'''
from server import settings
import json
import logging
import stackprinter

from models.orm_models.balance import Balance
from models.orm_models.exchange import Exchange


from exchanges.mappings import rest_api_map
from exchanges.base.rest.api import BaseRestAPI

# need to make this dynamic too
from exchanges.kraken.utils.clean_data import open_positions_aggregated_by_pair, balance_remove_zero_values

# Check if there are empty balances in the database 
# If empty we fetch the balance from API and write to the DB
# If not empty we cache Balance value to settings


async def instantiate_exchange_table(exchanges: dict):
    '''
    instantiate table if the passed dict is empty \t
    ==> we will need to define which exchanges need to be passed somehow and 
    what their ids should be 
    '''
    logging.warning(f"Exchange DBTable is empty") 

    for exchange_name, exchange_id in settings.EXCHANGE_IDS_FROM_NAME.items():
        await Exchange.create(
            name=exchange_name,
            exchange_id=exchange_id
        )
        await Balance.create(
            exchange_id=exchange_id,
            holdings={},
            positions={}
        )
        logging.warning(f"Added {exchange_name.upper()} to Exchange DBTable -- Exchange ID:{exchange_id}")
    
    logging.warning("Exchange DBTable instantiated")


async def instantiate_balance_table(exchange: int):
    '''
    create an element in the balance table \t
    input: exchange id (int)
    '''
    try:
        await Balance.create(
            # we need to append "id" to field name with foreign key: 
            # https://github.com/tortoise/tortoise-orm/issues/259
            exchange_id=exchange["exchange_id"],
            holdings={},
            positions={}
        )
        logging.warning(f"Instantiated Balance Table for exchange : {exchange['name'].upper()}")
    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))


async def update_balance_holdings(balance: dict):
    '''
    check if holdings in balance dict are empty, if they are, fetch balance value from API
    and update the database

    balance input format : dict with column names as dict keys, column values as dict values
    '''
    try:
        
        exchange_id = balance["exchange_id"]
        query_values = await Exchange.all().filter(exchange_id=exchange_id).values()
        
        exchange_name = query_values[0]["name"]
        api = rest_api_map[exchange_name]()

        # ==== UPDATE HOLDINGS ====

        resp = await api.get_account_balance()
        resp = resp["data"]
        
        # if holdings column is empty
        if not balance["holdings"]:

            logging.warning(f"{exchange_name.upper()} Holdings missing")

            await Balance.filter(exchange_id=exchange_id).update(
                holdings=resp
                )

            logging.warning(f"{exchange_name.upper()} Holdings set to {resp}")

        # if it isnt empty, audit it 
        else:
            if balance["holdings"] == resp:
                logging.info(f"{exchange_name.upper()} Holdings up to date")
            else:
                logging.warning(f"{exchange_name.upper()} Holdings not up to date")
                await Balance.filter(exchange_id=exchange_id).update(
                    holdings=resp
                    )
                logging.warning(f"{exchange_name.upper()} Holdings updated to {resp}")

    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))



async def update_balance_positions(balance: dict):

    try:
        
        exchange_id = balance["exchange_id"]
        query_values = await Exchange.all().filter(exchange_id=exchange_id).values()
        
        exchange_name = query_values[0]["name"]
        api = rest_api_map[exchange_name]()
    
        # ==== UPDATE POSITIONS ====

        #   TODO fix this
        req = await api.query_private(method="open_positions")
        open_positions = open_positions_aggregated_by_pair(req)
        # open_positions = await api.get_open_positions()
        # open_positions = open_positions["data"]
        
        
        # if positions column is empty
        if not balance["positions"]:

            logging.warning(f"{exchange_name.upper()} Positions missing")

            await Balance.filter(exchange_id=exchange_id).update(
                positions=open_positions
                )

            logging.warning(f"{exchange_name.upper()} Positions set to {open_positions}")
        
        # if it isnt empty, audit it 
        else:
            if balance["positions"] == open_positions:
                logging.info(f"{exchange_name.upper()} Positions up to date")
            else:
                logging.warning(f"{exchange_name.upper()} Positions not up to date")
                await Balance.filter(exchange_id=exchange_id).update(
                    positions=open_positions
                    )
                logging.warning(f"{exchange_name.upper()} Positions updated to {open_positions}")


    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))


async def startup_balances(redis_instance):
    try:
        exch_balances = await Balance.all().values()
        # returns a list of dicts of the format {id: int , holdings:{}, exchange_id: int}

        # if Balance table is empty:
        if not exch_balances:
            logging.warning(f"{exch_balances} Balance DBTable is empty")

            try:
                exchanges = await Exchange.all().values()
                # returns a list of dicts of format {exchange_id: int, name: str}

                if not exchanges:
                    await instantiate_exchange_table(exchanges)

                else:
                    for exchange in exchanges:
                        await instantiate_balance_table(exchange)
            
            except Exception as e:
                logging.error(stackprinter.format(e, style="darkbg2"))

        # if Balance table is not empty:
        # this code will not execute if balance table is initially empty
        # since exch_value will be == []
        # we need to fetch the balance values from db again after they are updated :
        exch_balances = await Balance.all().values()
       
        for balance in exch_balances:
            await update_balance_holdings(balance)
            await update_balance_positions(balance)
    
    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))
    

    raw_dictlist = await Balance.all().values()
    # returns list of dicts of format {id: int, holdings: dict, positions: dict, exchange_id: int}

    #iterate over raw dictlist, for each item pull out exchange_name from exchange id
    updated_balances = {settings.EXCHANGE_NAME_FROM_IDS[dic["exchange_id"]]:dic for dic in raw_dictlist}

    # separate steps to better visualise how to set up the dict comprehension
    # new_dict = {}
    # for dic in raw_dictlist:
    #     exchange_name = settings.EXCHANGE_NAME_FROM_IDS[dic["exchange_id"]]
    #     new_dict[exchange_name]=dic
        
    try:
        redis_instance.set("balances", json.dumps(updated_balances))
    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))


