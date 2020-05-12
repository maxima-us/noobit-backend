from noobit.models.data.response.order import Order as OrderRestModel



# for now we just use the same model, maybe later we will change ?
# seems to be easier to have the same models across the app
class Order(OrderRestModel):
    pass