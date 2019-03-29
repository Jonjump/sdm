from typing import NewType, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod
from domain import Donor, Donation, Benefit, PaymentId, PaymentProvider


class StoreException(Exception):
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class StoreDuplicate(StoreException):
    pass


class StoreNotFound(StoreException):
    pass


class StoreType(Enum):
    SQLLITE = 1


ConnectionString = NewType('ConnectionString', str)


@dataclass(frozen=True)
class StoreConfig():
    type: StoreType
    connnectionString: ConnectionString


class Store(ABC):

    @property
    @abstractmethod
    def type(self) -> StoreType:
        pass

    @abstractmethod
    def __init__(self, config: StoreConfig) -> None:
        pass

    @abstractmethod
    def insertDonation(self, donation: Donation) -> None:
        pass

    @abstractmethod
    def getDonations(self, startDate: datetime, endDate: datetime):
        pass

    @abstractmethod
    def getDonation(self, source: PaymentProvider, paymentId: PaymentId) -> Donation:
        pass

    @abstractmethod
    def addBenefit(self, benefit: Benefit) -> None:
        pass

    @abstractmethod
    def getCurrentBenefits(self) -> List[Benefit]:
        pass

    @abstractmethod
    def getDeliveredBenefits(self) -> List[Benefit]:
        pass

    @abstractmethod
    def getPendingBenefits(self) -> List[Benefit]:
        pass

    @abstractmethod
    def getBenefit(self, storeId) -> Benefit:
        pass

    @abstractmethod
    def deleteBenefit(self, benefit) -> None:
        pass

    @abstractmethod
    def updateBenefit(self, benefit: Benefit) -> None:
        pass

    @abstractmethod
    def getQualifyingDonors(self, benefit: Benefit) -> List[Donor]:
        pass

    @abstractmethod
    def setupStore(self):
        pass

    @abstractmethod
    def close(self):
        pass
