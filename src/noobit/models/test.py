from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, condecimal, ValidationError
import stackprinter


#================================================================================
#================================================================================

class Order:

    def __init__(self, price: float):
        try:
            price = Decimal(price)
            self.price = price.quantize(Decimal('0.01'))
        except Exception as e:
            print(stackprinter.format(e, style="darkbg2"))

        self.validated_data = self._validate()

    def _validate(self):
        try:
            pydantic = OrderPydantic(price=self.price)
            return pydantic.dict()
        except ValidationError as e:
            raise e

    @property
    def data(self):
        return self.validated_data


class OrderPydantic(BaseModel):

    price: condecimal(multiple_of=Decimal('0.01'))
    opt: Optional[str]


#================================================================================
#================================================================================

class Orders:

    def __init__(self, orders: List[Order]):
        self.orders = orders
        self.validated_data = self._validate()

    def _validate(self):
        try:
            pydantic = _OrdersPydantic(data=self.orders)
            return pydantic.dict()["data"]
        except ValidationError as e:
            raise e

    @property
    def data(self):
        return self.validated_data


class _OrdersPydantic(BaseModel):

    data: List[OrderPydantic]


#================================================================================
#================================================================================

# pydord = OrderPydantic(price='130.44')
# print(pydord)

# order = Order(price=130.33442534325)._validate()
# print(order)

# testorders = Orders(orders=[order, order, order])
# print(testorders.data)



class BaseError(Exception):

    def __init__(self, endpoint: str, data: dict):
        self.endpoint = endpoint
        self.data = data
        self.accept = True
        self.sleep = None

        msg = f"Endpoint: {self.endpoint} - Data: {self.data}"
        super().__init__(msg)


class DDoSProtection(BaseError):
    accept = False
    sleep = 60


# try:
#     raise BaseError(endpoint="kraken.com", data={"orderID": "lol"})
# except Exception as e:
#     print(stackprinter.format(e, style="darkbg2"))


if True:
    err = BaseError(endpoint="kraken.com", data={"1 == 2"})
    print("message: ", err)
    raise err
    # raise ValueError("Constant Value not accepted in conditional statement")
