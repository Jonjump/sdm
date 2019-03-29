from iso4217 import Currency


def getCurrencyFromString(s: str):
    assert isinstance(s, str)
    s = s.strip()
    try:
        return Currency(CURRENCYSYMBOLS[s.strip()])
    except KeyError:
        return Currency(s)


CURRENCYSYMBOLS = {
    "£": Currency('GBP'),
    "$": Currency('USD'),
    "€": Currency('EUR')
}
