from .public import PublicFeedReaderBase
from .public_abc import PublicFeedReaderABC

from .private import PrivateFeedReaderBase
from .private_abc import PrivateFeedReaderABC

class BasePublicFeedReader(PublicFeedReaderBase, PublicFeedReaderABC):
    pass


class BasePrivateFeedReader(PrivateFeedReaderBase, PrivateFeedReaderABC):
    pass