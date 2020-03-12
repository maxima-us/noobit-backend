'''
helper functions to clean up data etc \t
function needs to start with the name of the exchange endpoint
'''

#! use pd.df.map.(mapping dict) function from pandas to convert pairs from exchange format to normalized 
import logging
from decimal import Decimal
import json
import pandas as pd

from .pairs import normalize_currency, normalize_pair

def map_currencies():
    pass

def open_positions_aggregated_by_pair(response: dict):
    '''Aggregate open positions by type and pair

    Args:
        response (dict): response from "open_positions" api query

    Returns:
        dict : new dict of format {"buy":{"XBT": float}, "sell":{"XBT": float}}
    '''
    
    clean_dict = {"buy":{}, "sell":{}}

    for k,v in response.items():
        pair = (v["pair"])
        cost = float(v["cost"])         # we need this to be float to be serializable
        side = v["type"]

        if not pair in list(clean_dict[side].keys()):
            clean_dict[side][pair] = cost

        else:
            clean_dict[side][pair] += cost


    return clean_dict

def balance_remove_zero_values(response: dict):
    '''Remove all zero values balances and normalize currency names

    Args:
        response (dict): response from "account_balance" api query

    Returns:
        dict :  
            format {"BTC": balance}
    '''

    result = {normalize_currency(k):v for k,v in response.items() if float(v)!=0}

    return result 


def ohlc_to_pandas(response: dict):
    '''Convert ohlc response to a pandas dataframe

    Args:
        response (dict): response from "ohlc" api query

    Returns:
        pandas.DataFrame
    '''

    df = pd.DataFrame(response, columns=["timestamp", "open", "high", "low", "close", "vwap", "volume", "count"])
    df["open"] = pd.to_numeric(df["open"])
    df["high"] = pd.to_numeric(df["high"])
    df["low"] = pd.to_numeric(df["low"])
    df["close"] = pd.to_numeric(df["close"])
    df["vwap"] = pd.to_numeric(df["vwap"])
    df["volume"] = pd.to_numeric(df["volume"])
    # df["hl2"] = (df["high"] + df["low"]) / 2

    return df 

def open_orders_aggregated_by_pair(response: dict):
    '''Remove all zero values from passed balance dict

    Args:
        response (dict): response from "open_orders" api query

    Returns:
        dict
            format {"buy": {"XBT-USD": dict}, "sell": {"XBT-USD": dict}}
    '''

    clean_dict = {"buy":{}, "sell":{}}

    for k,v in response.items():
        pair = v["descr"]["pair"]
        volume = float(v["vol"])
        cost = float(v["cost"])         # we need this to be float to be serializable
        executed_volume = float(v["vol_exec"])
        side = v["descr"]["type"]
        price = v["price"]
        time = v["opentm"]
        status = v["status"]


        if not pair in list(clean_dict[side].keys()):
            clean_dict[side][pair]= [{"volume" : volume,
                                       "cost" : cost,
                                       "executed_volume": executed_volume,
                                       "side": side,
                                       "price": price,
                                       "time": time,
                                       "status": status
                                       }]

        else:
            clean_dict[side][pair] += cost


    return clean_dict

def open_orders_flattened(response: dict) :

    return flatten_response_dict(response)

def open_positions_flattened(response: dict):
    
    return flatten_response_dict(response)

def ticker_flattened(response: dict):

    return flatten_response_dict(response)


def flatten_response_dict(response: dict):
    '''Flatten nested dict into a pandas dataframe

    Args:
        response (dict): response from api query

    Returns:
        pandas.DataFrame

    Todo:
        Check if we have a column named pair or asset in our flattened df and normalize
    '''

    df = pd.DataFrame.from_dict(response, orient="columns")

    return df
    json_struct = json.loads(df.to_json())   
    df_flat = pd.io.json.json_normalize(json_struct)

    # check if response "main" key is a pair
    # ==> if first letter is X and fourth is Z

    # normalize kraken pairs
    if "pair" in df_flat.columns.values.tolist():
        df_flat["pair"] = df_flat["pair"].apply(normalize_pair)

    # normalize kraken currency
    if "currency" in df_flat.columns.values.tolist():
       df_flat["currency"] = df_flat["currency"].apply(normalize_currency) 

    return df_flat

