from noobit.logger.structlogger import get_logger, log_exception

logger = get_logger(__name__)


def parse_connection_status(message):
    try:
        parsed = {
            "connection_id": message["connectionID"],
            "status": "online" if message["status"] == "online" else "offline",
            "version": message["version"]
        }
        return parsed

    except Exception as e:
        log_exception(logger, e)

# EXAMPLE OF PAYLOAD
# {
#   "connectionID": 8628615390848610000,
#   "event": "systemStatus",
#   "status": "online",
#   "version": "1.0.0"
# }


MAP_FEED = {
    "book": "orderbook",
    "ticker": "instrument",
    "trade": "trade",
    "ohlc": "ohlc",
    "spread": "spread"
}

def parse_subscription_status(message):

    try:
        parsed = {
            "feed": MAP_FEED[message["subscription"]["name"]],
            "symbol": message["pair"].replace("/", "-"),
            "status": message["status"] if message["status"] in ["subscribed", "unsubscribed", "error"] else "error",
            "args": {k: v for k, v in message["subscription"].items() if not k == "name"}
        }
        return parsed

    except Exception as e:
        log_exception(logger, e)

# EXAMPLE OF PAYLOAD ON SUB
# {
#   "channelID": 10001,
#   "channelName": "ticker",
#   "event": "subscriptionStatus",
#   "pair": "XBT/EUR",
#   "status": "subscribed",
#   "subscription": {
#     "name": "ticker"
#   }
# }

# EXAMPLE OF PAYLOAD ON UNSUB
# {
#   "channelID": 10001,
#   "channelName": "ohlc-5",
#   "event": "subscriptionStatus",
#   "pair": "XBT/EUR",
#   "reqid": 42,
#   "status": "unsubscribed",
#   "subscription": {
#     "interval": 5,
#     "name": "ohlc"
#   }
# }

# EXAMPLE OF PAYLOAD ON ERROR
# {
#   "errorMessage": "Subscription depth not supported",
#   "event": "subscriptionStatus",
#   "pair": "XBT/USD",
#   "status": "error",
#   "subscription": {
#     "depth": 42,
#     "name": "book"
#   }
# }