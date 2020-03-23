from processor.feed_handler import FeedHandler

test = FeedHandler(exchanges=["kraken"], private_feeds=["ownTrades", "openOrders"], public_feeds=["trade"], pairs=["XBT/USD"])

test.run()
