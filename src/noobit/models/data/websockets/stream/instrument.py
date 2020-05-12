from noobit.models.data.response.instrument import Instrument as InstrRestModel


# for now we just use the same model, maybe later we will change ?
# seems to be easier to have the same models across the app
class Instrument(InstrRestModel):
    pass