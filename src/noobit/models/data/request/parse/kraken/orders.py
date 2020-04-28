from noobit.server import settings


def open_orders(symbol, clOrdID):


    # KRAKEN INPUT FORMAT
    #   trades = whether or not to include trades in output (optional.  default = false)
    #   userref = restrict results to given user reference id (optional)
    if clOrdID is None:
        data = {}
    else:
        data = {"userref": clOrdID}

    return data


def closed_orders(symbol, clOrdID):

    # KRAKEN INPUT FORMAT
    #   trades = whether or not to include trades in output (optional.  default = false)
    #   userref = restrict results to given user reference id (optional)
    #   start = starting unix timestamp or order tx id of results (optional.  exclusive)
    #   end = ending unix timestamp or order tx id of results (optional.  inclusive)
    #   ofs = result offset
    #   closetime = which time to use (optional)
    #       open
    #       close
    #       both (default)

    if clOrdID is None:
        data = {}
    else:
        data = {"userref": clOrdID}

    return data


def order(orderID, clOrdID):

    # KRAKEN INPUT FORMAT
    # trades = whether or not to include trades in output (optional.  default = false)
    # userref = restrict results to given user reference id (optional)
    # txid = comma delimited list of transaction ids to query info about (50 maximum)

    if clOrdID is None:
        data = {"txid": orderID}
    else:
        data = {"userref": clOrdID, "txid": orderID}

    return data