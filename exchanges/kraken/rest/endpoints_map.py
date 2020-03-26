base_endpoints = {
        #! deprecated
                
                "Binance": None,
                "Bitfinex": "https://api-pub.bitfinex.com/v2/" ,
                "Bitmex": 'https://www.bitmex.com',
                "Coinbase": "https://api.pro.coinbase.com",
                "Deribit": "https://www.deribit.com/api/v2/public/",
                "FTX": None,
                "Gemini": "https://api.gemini.com",
                "Kraken": "https://api.kraken.com", #! Do not include 0 in base endpoint as we need to include it in the hmac sig
                "Krakenfutures": None,
        }


mapping = {
        #! exchanges need to be in title format
        "Kraken": {
                    "base_url": "https://api.kraken.com",
                    "public_endpoint": "/0/public",
                    "private_endpoint": "/0/private",
                        
                    "public_methods":{
                        "time": "Time",
                        "assets": "Assets",
                        "tradable_pairs": "AssetPairs",
                        "ticker": "Ticker",
                        "ohlc": "OHLC",
                        "orderbook": "Depth",
                        "trades": "Trades",
                        "spread": "Spread",

                    },

                    "private_methods":{
                        "account_balance": "Balance",
                        "trade_balance": "TradeBalance",
                        "open_positions": "OpenPositions",
                        "open_orders": "OpenOrders",
                        "closed_orders": "ClosedOrders",
                        "trades_history": "TradesHistory",
                        "ledger": "Ledgers",
                        "order_info": "QueryOrders",
                        "trades_info": "QueryTrades",
                        "ledger_info": "QueryLedgers",
                        "volume": "TradeVolume",
                        "place_order": "AddOrder",
                        "cancel_order": "CancelOrder",
                        "ws_token": "GetWebSocketsToken" 
                    }
                },

        "Bitfinex": {
                    "public":{

                            },

                    "private":{

                            }
                }

        }