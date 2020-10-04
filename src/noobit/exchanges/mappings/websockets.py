from noobit.exchanges.kraken.websockets.private import KrakenPrivateFeedReader
from noobit.exchanges.kraken.websockets.public import KrakenPublicFeedReader

# careful: can only ever be one instance of each in dict
# if we assign same instance to multiple keys we will get an error
private_ws_map = {"kraken": KrakenPrivateFeedReader}
public_ws_map = {"kraken": KrakenPublicFeedReader}