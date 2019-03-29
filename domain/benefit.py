from datetime import datetime, date
from abc import ABC, abstractproperty
from enum import Enum
from . import Delivery, Money

DATEPRINTFORMAT = "%e %b %Y"


class BenefitType(Enum):
    AMOUNT = "Amount"
    AMOUNTPERMONTH = "AmountPerMonth"
    NEWDONOR = "NewDonor"


class BenefitException(Exception):
    def __init__(self, key, message):
        self.key = key
        self.message = message


class BenefitStatus(Enum):
    CURRENT = "current",
    PENDING = "pending",
    DELIVERED = "delivered"


class Benefit(ABC):
    """
    a benefit is something that is provided to a donor
    as a result of their donations
    """
    _storeId: str
    reward: str
    startDate: date
    endDate: date
    delivery: Delivery
    minAmount: Money
    @property
    def status(self):
        if self.completed:
            return BenefitStatus.DELIVERED
        if self.endDate <= datetime.now().date():
            return BenefitStatus.PENDING
        return BenefitStatus.CURRENT

    @property
    def _betweenDatesText(self):
        return f"between {self.startDate.strftime(DATEPRINTFORMAT)} and {self.endDate.strftime(DATEPRINTFORMAT)}"

    @property
    def csvFileName(self):
        return f"{self.type.name}_{self._storeId}_{datetime.now().strftime('%y%m%d_%H%M%S')}.csv"

    @abstractproperty
    def text(self):
        pass

    @abstractproperty
    def type(self):
        pass

    def __init__(self, storeId, reward: str, startDate: date, endDate: date, delivery: Delivery, minAmount: Money, completed: bool):
        if completed is None:
            completed = False

        self._storeId = storeId
        self.reward = reward
        self.startDate = startDate
        self.endDate = endDate
        self.delivery = delivery
        self.minAmount = minAmount
        self.completed = completed
        self._validate()

    def setStoreId(self, storeId: str):
        if self._storeId is not None:
            raise Exception('Cannot reset store id')
        self._storeId = storeId

    def __iter__(self):
        """
        iterator is used to convert class into a tuple
        when it is stored or tramsferred
        """
        yield self.type.name
        yield self.reward
        yield self.startDate
        yield self.endDate
        yield self.delivery.name
        try:
            yield self.minAmount.amount
        except:  # noqa: E722
            yield None
        try:
            yield self.minAmount.currency.name
        except:  # noqa: E722
            yield None
        yield self.completed

    def _validate(self):
        if not self.reward:
            raise BenefitException("reward", "a reward is required")
        if len(self.reward) < 5:
            raise BenefitException("reward", " reward must be at least 5 characters")
        if not isinstance(self.startDate, date):
            raise BenefitException("startDate", "a start date is required")
        if not isinstance(self.endDate, date):
            raise BenefitException("endDate", "an end date is required")
        if not isinstance(self.minAmount, Money):
            raise BenefitException("minAmount", "a minimum amount is required")
        if not isinstance(self.delivery, Delivery):
            raise BenefitException("delivery", "a delivery type must be specified")

    def getMonths(self):
        return self.endDate.month - self.startDate.month + 1

    @staticmethod
    def Factory(storeId, type, reward: str, startDate: date, endDate: date, delivery: Delivery, minAmount: Money, completed: bool):
        if type == BenefitType.AMOUNT:
            return Benefit_Amount(storeId, reward, startDate, endDate, delivery, minAmount, completed)
        if type == BenefitType.AMOUNTPERMONTH:
            return Benefit_AmountPerMonth(storeId, reward, startDate, endDate, delivery, minAmount, completed)
        if type == BenefitType.NEWDONOR:
            return Benefit_NewDonor(storeId, reward, startDate, endDate, delivery, minAmount, completed)
        raise BenefitException("type", f'{type} not implemented')


class Benefit_Amount(Benefit):
    @property
    def text(self):
        return f"We give you {self.reward} if you donate at least {self.minAmount} {self._betweenDatesText}"

    @property
    def type(self):
        return BenefitType.AMOUNT


class Benefit_AmountPerMonth(Benefit):
    @property
    def text(self):
        return f"We give you {self.reward} if you donate at least {self.minAmount} a month {self._betweenDatesText}"

    @property
    def type(self):
        return BenefitType.AMOUNTPERMONTH


class Benefit_NewDonor(Benefit):
    @property
    def text(self):
        return f"We give new donors who donate at least {self.minAmount} {self._betweenDatesText} {self.reward}"

    @property
    def type(self):
        return BenefitType.NEWDONOR

# MinAmount
# NewDonorMinAmount
# MinMonthlyDonations
# MinNumberDonations
