from noobit.models.data.response.trade import (
    Trade as TradeRestModel,
    TradesList as TradesListRest
)


# for now we just use the same model, maybe later we will change ?
# seems to be easier to have the same models across the app
class Trade(TradeRestModel):
    pass


class TradesList(TradesListRest):
    pass