from exchanges.kraken.websockets.private import KrakenPrivateFeedReader
from exchanges.kraken.websockets.public import KrakenPublicFeedReader

private_ws_map = {"kraken": KrakenPrivateFeedReader}
public_ws_map = {"kraken": KrakenPublicFeedReader}