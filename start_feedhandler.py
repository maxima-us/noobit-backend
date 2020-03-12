from processor.feed_handler import FeedHandler

test = FeedHandler(exchanges=["kraken"], feeds=["ownTrades", "openOrders"])

test.run()
