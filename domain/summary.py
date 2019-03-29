from enum import Enum, unique
from typing import List
from . import Total, Money


@unique
class SummaryFields(Enum):
    CURRENCY = "currency"
    SOURCE = "source"
    DATE = "date"
    TYPE = "type"
    WEEK = "week"
    MONTH = "month"
    DONOR = "donor"


def groupByField(donations, field):
    grouped = {}
    for i in donations:
        key = getattr(i, field.value)
        if key in grouped:
            grouped[key].append(i)
        else: 
            grouped[key] = [i]
    return grouped


def getZero(donations):
    return Total(Money(0, donations[0].money.currency), 0)


def addDonations(x, y):
    return x.money + y.money


def sumTotals(x, y):
    return x.total + y.total


class Summary(dict):
    def __init__(self, donations, fields: List[SummaryFields]):
        self.total = Total([x.money for x in donations], len(donations))
        if self._isNode(fields): 
            self.field = fields[0]
            fields = fields[1:]
            self._makeBranches(donations, fields)

    def _isNode(self, fields: List[SummaryFields]):
        return len(fields) != 0

    def _makeBranches(self, donations, fields):
        for key, group in groupByField(donations, self.field).items():
            self[key] = Summary(group, fields)
