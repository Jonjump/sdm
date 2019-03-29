from enum import Enum, unique


@unique
class Delivery(Enum):
    ONLINE = 1
    OFFLINE = 2
