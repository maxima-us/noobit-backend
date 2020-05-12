from noobit.models.data.response.orderbook import OrderBook as OBRestModel


# for now we just use the same model, maybe later we will change ?
# seems to be easier to have the same models across the app
class OrderBook(OBRestModel):
    is_snapshot: bool
    is_update: bool