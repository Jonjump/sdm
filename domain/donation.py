from datetime import date
from dataclasses import dataclass
from . import DonationType, Donor,  isnotemptyinstance, Money, PaymentId, PaymentProvider, rndDate


@dataclass(frozen=True)
class Donation():
    source: PaymentProvider
    paymentId: PaymentId
    donor: Donor
    paymentDate: date
    type: DonationType
    money: Money
    @property
    def currency(self):
        return self.money.currency

    @property
    def week(self):
        return rndDate(self.paymentDate, "week", "up")

    @property
    def month(self):
        return rndDate(self.paymentDate, "month", "up")

    def __post_init__(self):
        assert isinstance(self.source, PaymentProvider)
        assert isnotemptyinstance(self.paymentId, PaymentId)
        assert isnotemptyinstance(self.donor, Donor)
        assert isinstance(self.paymentDate, date)
        assert isinstance(self.type, DonationType)
        assert isinstance(self.money, Money)

    def __iter__(self):
        yield self.source.name
        yield self.paymentId
        yield self.donor
        yield self.paymentDate
        yield self.type.name
        yield self.money.amount
        yield self.money.currency.name
