'''
global config file, needs to be imported in each module of the app for us to
be able to instantiate the global variables at startup
'''
import os
import redis

from dotenv import load_dotenv
load_dotenv()



# Redis config
REDIS = redis.Redis(host='localhost', port=6379, db=0)
REDIS_POOL = None

# Strategy to run ==> what if we want to run multiple strategies at the same time ?
#                 ==> we will need to find a way to share the ws data
# STRAT = strats.mesa

# Strat interval 
STRAT_TF = "1-minute"

# Target exchange
STRAT_EXCHANGE = "kraken"

# Target pair 
STRAT_PAIR = ""     # ==> we have not integrated this variable in our code yet

# Exchange IDs
EXCHANGE_IDS_FROM_NAME = {
    "kraken": 1,
    }

EXCHANGE_NAME_FROM_IDS = {v:k for k,v in EXCHANGE_IDS_FROM_NAME.items()}

# Uvicorn
UVICORN_RUNNING = False

# Tick Interval for Uvicorn main loop
TICK_INTERVAL = 0.05

# List of tasks to pass to main loop
ASYNCIO_TASKS = []

# Kafka Consumer
CONSUMER = None

# HTTPX Session ==> should be sent to cache
SESSION = None

# App root path
# HOME = os.environ["APP_PATH"]
# ROOT = f"{HOME}/server"