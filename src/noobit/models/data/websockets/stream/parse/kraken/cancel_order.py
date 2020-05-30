from noobit.logging.structlogger import get_logger, log_exception
from noobit.models.data.request.cancel_order import CancelOrder


logger = get_logger(__name__)


def parse_cancel_order(validated_data: CancelOrder , token: str):

    try:
        parsed = {
            "event": "cancelOrder",
            "token": token,
            "reqid": validated_data.clOrdID if validated_data.clOrdID else "null",
            "txid": validated_data.orderID
        }

    except Exception as e:
        log_exception(logger, e)

    return parsed