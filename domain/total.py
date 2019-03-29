from . import Money


class Total(dict):
    count: int

    def __init__(self, monies, count):
        self.count = count
        for money in monies:
            self._addMoney(money)

    def _addMoney(self, money: Money):
        key = money.currency
        if key in self:
            self[key] += money
        else:
            self[key] = money

    def addMoney(self, money: Money):
        self._addMoney(money)
        self.count += 1

    def __add__(self, another):
        monies = [x for x in self.values()]
        monies += [x for x in another.values()]
        return Total(monies, self.count + another.count)
