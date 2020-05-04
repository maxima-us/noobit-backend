from typing import Optional


def user_trades(trdMatchID: Optional[str] = None):

    # KRAKEN INPUT FORMAT (for all trades)
    # type = type of trade (optional)
    #   all = all types (default)
    #   any position = any position (open or closed)
    #   closed position = positions that have been closed
    #   closing position = any trade closing all or part of a position
    #   no position = non-positional trades
    # trades = whether or not to include trades related to position in output (optional.  default = false)
    # start = starting unix timestamp or trade tx id of results (optional.  exclusive)
    # end = ending unix timestamp or trade tx id of results (optional.  inclusive)
    # ofs = result offset

    # KRAKEN INPUT FORMAT (for single trade)
    # txid = comma delimited list of transaction ids to query info about (20 maximum)
    # trades = whether or not to include trades related to position in output (optional.  default = false)
    if trdMatchID:
        return {"txid": trdMatchID, "trades": "true"}

    return {"trades": "true"}