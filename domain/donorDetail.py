from datetime import date
from dataclasses import dataclass
from . import Donor,  isnotemptyinstance


@dataclass(frozen=True)
class DonorDetail():
    donor: Donor
    firstPaymentDate: date
    lastPaymentDate: date

    def __post_init__(self):
        assert isnotemptyinstance(self.donor, Donor)
        assert isinstance(self.firstPaymentDate, date)
        assert isinstance(self.lastPaymentDate, date)

    def __iter__(self):
        yield self.donor
        yield self.firstPaymentDate
        yield self.lastPaymentDate
