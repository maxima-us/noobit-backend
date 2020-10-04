class AsyncState():


    def __init__(self, symbol):
        self.current = {
            symbol: {
                "side": None,
                "volume": {"orderQty": 0, "cumQty": 0, "leavesQty": 0},
                "spread": {"best_bid": 0, "best_ask": 0},
                "orders": {"open": {}}
            }
        }

    def __aiter__(self):
        return self

    async def __anext__(self):
        return self.current