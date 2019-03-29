Amount = float
BenefitName = str
Email = str
Donor = Email
PaymentId = str


def isnotemptyinstance(value, type):
    if not isinstance(value, type):
        return False  # None returns false

    if isinstance(value, str):
        return (len(value.strip()) != 0)
    elif isinstance(value, int):
        return (value != 0)
    elif isinstance(value, float):
        return (value != 0.0)
    else:
        raise NotImplementedError
