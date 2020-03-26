[![Build Status](https://travis-ci.com/maxima-us/noobit-backend.svg?branch=master)](https://travis-ci.com/maxima-us/noobit-backend)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/ee5a7cf93c65477db5bd675f8979aa9d)](https://www.codacy.com/manual/maximousse/noobit-backend?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=maxima-us/noobit-backend&amp;utm_campaign=Badge_Grade)

# NooBit Backend

## Services 

**API Server** :   
Based on Uvicorn and FastAPI  
OpenAPI interface accessible at localhost:8000/docs  
Interfaces with sqlite db via Tortoise ORM  
Listens to redis channels to automatically update db  

**Feed Handler** :  
Receive data from websocket, sort and publish to appropriate redis channels

**Trading Engine** :  
Handle signals and execution logic (not implemented yet)

## Usage

### Credentials and environment variables

For each exchange, you will need to provide an .env file with a list of API keys.  
Place them in the same folder as the one containing the exchange rest api code.  
For Kraken for ex : noobit-backend/exchanges/kraken/rest/.env  
Make sure to follow the following format (env key for API KEY needs to at least contain <exchange_name> and "API_KEY",
env key for API SECRET needs to at least contain <exchange_name> and "API_SECRET") :
```
KRAKEN_BTC_USD_API_KEY=[YOUR KEY]
KRAKEN_BTC_USD_API_SECRET=[YOUR SECRET]
KRAKEN_BTC_EUR_API_KEY=[YOUR KEY]
KRAKEN_BTC_EUR_API_SECRET=[YOUR SECRET]
```

### Services

From within noobit-backend folder :

To start api server:
```python
python start_server.py
```

To start websocket feed handler (publish all incoming websocket data to appropriate redis channel) :
```python
python start_feedhandler.py
```

### Testing

From within noobit-backend folder :
```python
python -m pytest -vv
```

## To Do

-  data validation + testing for placing & closing orders
-  implement cancel all orders / positions methods
-  command line 
-  trading engine



