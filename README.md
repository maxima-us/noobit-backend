# NooBit Backend

## Services 

**API Server** :   
Based on Uvicorn and FastAPI  
Accessible from the browser, based on OpenAPI (accessible at localhost:8000/docs)  
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
```
python start_server.py
```

To start websocket feed handler (publish all incoming websocket data to appropriate redis channel) :
```
python start_feedhandler.py
```

