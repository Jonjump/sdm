import re
from dataclasses import dataclass
from . import Amount, Currency, getCurrencyFromString

CURRENCYFIRST = re.compile(r'(?P<currency>[^\.0-9]+)(?P<amount>[\.0-9]+)')
CURRENCYLAST = re.compile(r'(?P<amount>[\.0-9]+)(?P<currency>[^\.0-9]*)')


@dataclass(frozen=True, init=False)
class Money ():
    amount: Amount
    currency: Currency
    @property
    def amountInt(self):
        return int(self.amount)

    def __init__(self, amount, currency):
        if isinstance(amount, int):
            object.__setattr__(self, 'amount', float(amount))
        else:
            object.__setattr__(self, 'amount', amount)

        if isinstance(currency, Currency):
            object.__setattr__(self, 'currency', currency)
        else:
            object.__setattr__(self, 'currency', getCurrencyFromString(currency))

    def __post_init__(self):
        assert isinstance(self.amount, float) 
        assert isinstance(self.currency, Currency) 

    def __add__(self, another):
        if (self.currency != another.currency): 
            raise TypeError(f"cannot add amounts with different currencies - {self.currency},{another.currency}")
        return Money(self.amount + another.amount, self.currency)

    def __ge__(self, another):
        if (self.currency != another.currency): 
            raise TypeError(f"cannot compare amounts with different currencies - {self.currency},{another.currency}")
        return self.amount >= another.amount

    def __str__(self):
        return f"{self.amount} {self.currency.value}"

    @classmethod
    def fromString(cls, s):
        s = s.replace(" ", "").upper()
        if str.isnumeric(s[0]): 
            matched = CURRENCYLAST.match(s)
        else:
            matched = CURRENCYFIRST.match(s)

        currency = getCurrencyFromString(matched.group('currency'))
        amount = Amount(float(matched.group('amount')))

        return cls(amount=amount, currency=currency)
