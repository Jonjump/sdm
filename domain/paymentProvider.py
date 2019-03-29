from enum import Enum, unique


@unique
class PaymentProvider(Enum):
    STRIPE = 1
    PAYPAL = 2
    GOCARDLESS = 3
