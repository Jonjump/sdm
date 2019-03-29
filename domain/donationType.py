from enum import Enum, unique


@unique
class DonationType(Enum):
    ONEOFF = 1
    MONTHLY = 2
    ANNUAL = 3
    @classmethod
    def fromString(cls, s):
        s = s.strip().upper()
        if s.find("MONTH") > -1:
            return cls.MONTHLY
        if s.find("YEAR") > -1:
            return cls.ANNUAL
        return cls[s]
