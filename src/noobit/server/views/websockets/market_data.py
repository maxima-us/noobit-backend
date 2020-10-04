import asyncio
from datetime import datetime

import ujson

from noobit.server.views import APIRouter, WebSocket
from noobit import runtime
from noobit.logger.structlogger import get_logger, log_exception

router = APIRouter()
logger = get_logger(__name__)

@router.websocket('/ws/market_data/snapshots')
async def stream_market_data_snapshots(websocket: WebSocket):
    await websocket.accept()

    redis = runtime.Config.redis_pool
    # snapshot_chan = f"ws:public:data:spread:snapshot:{runtime.Config.selected_exchange}:{runtime.Config.selected_symbol}"
    # snapshot_chan = f"ws:public:data:orderbook:snapshot:kraken:XBT-USD"
    orderbook_chan = f"ws:public:data:orderbook:snapshot:*"
    trade_chan = f"ws:public:data:trade:snapshot:*"
    instrument_chan = f"ws:public:data:instrument:snapshot:*"
    spread_chan = f"ws:public:data:spread:snapshot:*"
    ohlc_chan = f"ws:public:data:ohlc:snapshot:*"

    # sub returns list of channels
    try:
        (orderbook, trade, instrument, spread, ohlc) = await redis.psubscribe(orderbook_chan, trade_chan, instrument_chan, spread_chan, ohlc_chan)
    except Exception as e:
        log_exception(logger, e)

    # while True:
    #     if runtime.Config.terminate:
    #         break

    async def stream_orderbook():
        async for _chan, msg in orderbook.iter():
            try:
                if runtime.Config.terminate:
                    break

                message = ujson.loads(msg)
                if message["symbol"] == runtime.Config.requested_symbol_market_data \
                    and message["exchange"] == runtime.Config.requested_exchange_market_data:

                # calculate totals => we need asks in ascending order and bids in descending order
                    sorted_asks = dict(sorted(message["asks"].items(), key=lambda x: float(x[0])))
                    parsed_asks = [{"price": float(k), "size": round(v, 3)} for k, v in sorted_asks.items()]
                    # parsed_asks = [{**elem, "total": elem["size"] if index == 0 else parsed_asks[index-1]["total"]} for index, elem in enumerate(parsed_asks)]
                    for index, elem in enumerate(parsed_asks):
                        if index == 0:
                            elem["total"] = elem["size"]
                        else:
                            elem["total"] = elem["size"] + parsed_asks[index-1]["total"]
                    # resort in descending order for visualization
                    parsed_asks = sorted(parsed_asks, key=lambda x: x["price"], reverse=True)

                    sorted_bids = dict(sorted(message["bids"].items(), key=lambda x: float(x[0]), reverse=True))
                    parsed_bids = [{"price": float(k), "size": round(v, 3)} for k, v in sorted_bids.items()]
                    # parsed_bids = [{**elem, "total": elem["size"] + parsed_bids.get(index-1, {}).get("total", 0)} for index, elem in enumerate(parsed_bids)]
                    for index, elem in enumerate(parsed_bids):
                        if index == 0:
                            elem["total"] = elem["size"]
                        else:
                            elem["total"] = elem["size"] + parsed_bids[index-1]["total"]

                    # replace asks and bids in message but keep rest of metadata
                    message["asks"], message["bids"] = parsed_asks, parsed_bids
                    payload = ujson.dumps(message)
                    await websocket.send_text(payload)

            except Exception as e:
                log_exception(logger, e)


    async def stream_trade():
        async for _chan, msg in trade.iter():
            try:
                if runtime.Config.terminate:
                    break

                message = ujson.loads(msg)

                requested = [trade for trade in message["data"] \
                            if trade["symbol"] == runtime.Config.requested_symbol_market_data \
                            and trade["exchange"] == runtime.Config.requested_exchange_market_data]
                # if message["symbol"] == runtime.Config.requested_symbol_market_data \
                #     and message["exchange"] == runtime.Config.requested_exchange_market_data:

                # sort trades
                sorted_trades = sorted(requested, key=lambda x: x["transactTime"], reverse=True)

                parsed_trades = [{
                    "price": float(trade["avgPx"]),
                    "size": round(float(trade["cumQty"]), 3),
                    # noobit parses timestamp to ns and method requires ms
                    "time": str(datetime.utcfromtimestamp(trade["transactTime"]*10**-9).time().isoformat("seconds")),
                    "side": trade["side"]
                } for trade in sorted_trades]

                message["data"] = parsed_trades
                payload = ujson.dumps(message)
                await websocket.send_text(payload)

                # print(message)
                # payload = ujson.dumps(message)
                # await websocket.send_text(payload)
            except Exception as e:
                log_exception(logger, e)


    async def stream_ohlc():

        # FIXME doesn't seem to work when we have subd to multiple symbols
        async for _chan, msg in ohlc.iter():
            try:
                if runtime.Config.terminate:
                    break

                message = ujson.loads(msg)

                if message["exchange"] == runtime.Config.requested_exchange_market_data:
                    requested = [
                        candle for candle in message["data"] \
                        if candle["symbol"] == runtime.Config.requested_symbol_market_data \
                    ]

                    parsed_ohlc = [
                        [
                            candle["utcTime"]*10**-6,
                            candle["open"],
                            candle["high"],
                            candle["low"],
                            candle["close"]
                        ]
                        for candle in requested
                    ]
                    message["data"] = parsed_ohlc
                    payload = ujson.dumps(message)
                    await websocket.send_text(payload)

            except Exception as e:
                log_exception(logger, e)


    async def stream_instrument():
        async for _chan, message in instrument.iter():
            try:
                # print(message)
                # payload = ujson.dumps(message)
                # await websocket.send_text(payload)
                pass
            except Exception as e:
                log_exception(logger, e)


    async def stream_spread():
        async for _chan, message in spread.iter():
            try:
                # print(message)
                # payload = ujson.dumps(message)
                # await websocket.send_text(payload)
                pass
            except Exception as e:
                log_exception(logger, e)


    results = await asyncio.gather(
        stream_orderbook(),
        stream_trade(),
        stream_instrument(),
        stream_spread(),
        stream_ohlc()
    )
    return results