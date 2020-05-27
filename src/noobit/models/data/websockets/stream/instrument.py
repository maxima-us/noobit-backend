from typing_extensions import Literal

from noobit.models.data.response.instrument import Instrument as InstrRestModel


# for now we just use the same model, maybe later we will change ?
# seems to be easier to have the same models across the app
class Instrument(InstrRestModel):
    # As defined in bitmex ws api: https://www.bitmex.com/app/wsAPI
    #   The type of the message. Types:
    #   'partial'; This is a table image, replace your data entirely.
    #   'update': Update a single row.
    #   'insert': Insert a new row.
    #   'delete': Delete a row.
    #   "action": 'partial' | 'update' | 'insert' | 'delete',
    action: Literal["partial", "update", "insert", "delete"] = "insert"