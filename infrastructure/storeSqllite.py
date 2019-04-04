from typing import List
from sqlite3 import dbapi2 as sqlite, OperationalError
from datetime import date, datetime
from domain import Benefit, Donor, Donation, DonationType, Money, Delivery, Currency, PaymentProvider, rndDate, BenefitType, DonorDetail
from .store import Store, StoreType, StoreConfig, StoreDuplicate, StoreNotFound


def months(start, end):
    return (end.year - start.year) * 12 + end.month - start.month + 1


def sqlNames(fields):
    return ','.join(fields)


def sqlValues(fields):
    return "?,"*(len(fields)-1) + "?"


def setCmd(fields):
    updateFields = [f"{field}=?" for field in fields]
    return 'SET ' + ','.join(updateFields)


CMD_INIT_DONATIONS = """
    CREATE TABLE donations(
        source TEXT NOT NULL,
        paymentId TEXT NOT NULL,
        donor TEXT NOT NULL,
        date TEXT NOT NULL,
        type TEXT NOT NULL,
        amount INT NOT NULL,
        currency TEXT NOT NULL,
        PRIMARY KEY(source, paymentId)
    );"""
DONATION_FIELDS = [
    "source",
    "paymentId",
    "donor",
    "date",
    "type",
    "amount",
    "currency",
]

CMD_INIT_BENEFITS = """
    CREATE TABLE benefits(
        id INTEGER PRIMARY KEY,
        type TEXT NOT NULL,
        reward TEXT NOT NULL,
        startDate TEXT NOT NULL,
        endDate TEXT NOT NULL,
        delivery TEXT NOT NULL,
        minAmount FLOAT NULL,
        minAmountCurrency TEXT NULL,
        completed INT NOT NULL
    );"""
BENEFIT_FIELDS = [
    "type",
    "reward",
    "startDate",
    "endDate",
    "delivery",
    "minAmount",
    "minAmountCurrency",
    "completed"
]
CMD_GET_BENEFITS = f"SELECT id,{sqlNames(BENEFIT_FIELDS)} FROM benefits where endDate>=? AND startDate<=?"
CMD_GET_BENEFIT = f"SELECT id,{sqlNames(BENEFIT_FIELDS)} FROM benefits WHERE id=?"
CMD_INSERT_BENEFIT = f"INSERT INTO benefits ({sqlNames(BENEFIT_FIELDS)}) VALUES ({sqlValues(BENEFIT_FIELDS)});"
CMD_DELETE_BENEFIT = "DELETE FROM benefits WHERE id=?"
CMD_UPDATE_BENEFIT = f"UPDATE benefits {setCmd(BENEFIT_FIELDS)} WHERE id=?"

CMD_GET_DONATIONS = f"SELECT {sqlNames(DONATION_FIELDS)} FROM donations WHERE date>=? AND date<=?"
CMD_GET_DONATION = f"SELECT {sqlNames(DONATION_FIELDS)} FROM donations WHERE source = ? AND paymentId = ?"
CMD_INSERT_DONATION = f"INSERT INTO donations ({sqlNames(DONATION_FIELDS)}) VALUES ({sqlValues(DONATION_FIELDS)});"


def getQualifyingQuery(benefit):
    minAmount = benefit.minAmount.amount
    minAmountCurrency = benefit.minAmount.currency.name
    if benefit.type == BenefitType.AMOUNT:
        cmd = """
            Select donor FROM
            ( SELECT donor, SUM(amount) AS total FROM DONATIONS WHERE date>=? AND date<=? and currency=? GROUP BY donor)
            WHERE total>=?
            ORDER BY donor
            """
        args = (
            benefit.startDate,
            benefit.endDate,
            minAmountCurrency,
            minAmount
            )
    elif benefit.type == BenefitType.AMOUNTPERMONTH:
        startDate = rndDate(benefit.startDate, "month", "down")
        endDate = rndDate(benefit.endDate, "month", "up")
        cmd = """
SELECT
    donor
FROM (
    SELECT
        donor, STRFTIME('%Y-%m', date) AS month ,SUM(amount) AS monthTotal
    FROM donations
    WHERE date>=? AND date<=? AND currency=?
    GROUP BY donor,month
    HAVING monthTotal>=?
)
GROUP BY donor
HAVING COUNT(1) >=?
"""
        args = (
            startDate,
            endDate,
            minAmountCurrency,
            minAmount,
            months(startDate, endDate)
            )

    elif benefit.type == BenefitType.NEWDONOR:
        cmd = """
SELECT
    donor
FROM (
    SELECT donor,date
        FROM donations
    WHERE currency=? AND amount>?
    GROUP BY donor
    ORDER BY date
)
WHERE date>=? and date <=?
"""
        args = (
            minAmountCurrency,
            minAmount,
            benefit.startDate,
            benefit.endDate
            )

    else:
        raise Exception
    return (cmd, args)


def isTrue(dbValue: int):
    return dbValue != 0


def parseDate(dbValue):
    try:
        d = datetime.strptime(dbValue, '%Y-%m-%d')
        return date(d.year, d.month, d.day)
    except:  # noqa: E722
        return None


def donorDetailFromRow(row):
    return DonorDetail(
        donor=row[0],
        firstPaymentDate=parseDate(row[1]),
        lastPaymentDate=parseDate(row[2])
    )


def donationFromRow(row):
    return Donation(
        source=PaymentProvider[row[0]],
        paymentId=row[1],
        donor=row[2],
        paymentDate=parseDate(row[3]),
        type=DonationType[row[4]],
        money=Money(amount=row[5], currency=Currency(row[6].upper()))
    )


def benefitFromRow(row):
    try:
        minAmount = Money(row[6], Currency[row[7]])
    except:  # noqa: E722
        minAmount = None
    if row[8] == 1:
        completed = True
    else:
        completed = False
    return Benefit.Factory(
        storeId=str(row[0]),
        type=BenefitType[row[1]],
        reward=row[2],
        startDate=parseDate(row[3]),
        endDate=parseDate(row[4]),
        delivery=Delivery[row[5]],
        minAmount=minAmount,
        completed=completed
    )


class StoreSqlLite(Store):
    def type(self):
        return StoreType.Sqllite

    def __init__(self, config: StoreConfig) -> None:
        connectionString = config.connnectionString
        try:
            self._connection = sqlite.connect(database=f"file:{connectionString}?mode=rw", uri=True, check_same_thread=False)
        except OperationalError:
            self._connection = sqlite.connect(database=f"file:{connectionString}?mode=rwc", uri=True, check_same_thread=False)
            self.setupStore()

    def insertDonation(self, donation) -> None:
        try:
            self._connection.cursor().execute(CMD_INSERT_DONATION, tuple(donation))
            self._connection.commit()
        except sqlite.IntegrityError as error:
            raise StoreDuplicate(inner=error)

    def getDonations(self, startDate, endDate):
        if startDate > endDate:
            raise ValueError("startdate gt enddate")
        rows = self._connection.cursor().execute(CMD_GET_DONATIONS, (startDate, endDate)).fetchall()
        return [donationFromRow(row) for row in rows]

    def getDonation(self, source: PaymentProvider, paymentId):
        rows = self._connection.cursor().execute(CMD_GET_DONATION, (source.name, paymentId)).fetchall()
        count = len(rows)
        if count == 1:
            return donationFromRow(rows[0])
        elif count == 0:
            raise StoreNotFound(source=source, paymentId=paymentId)
        else:
            raise StoreDuplicate()

    def addBenefit(self, benefit) -> Benefit:
        t = tuple(benefit)
        try:
            id = self._connection.cursor().execute(CMD_INSERT_BENEFIT, t).lastrowid
            benefit.setStoreId(str(id))
            self._connection.commit()
            return benefit
        except sqlite.IntegrityError as error:
            raise StoreDuplicate(inner=error)

    @property
    def endToday(self):
        now = datetime.now()
        return datetime(now.year, now.month, now.day, 23, 59, 59, 999999)

    def getCurrentBenefits(self):
        args = self.endToday,
        rows = self._connection.cursor().execute("SELECT * FROM benefits WHERE completed=0 AND endDate>=?", args).fetchall()
        return [benefitFromRow(row) for row in rows]

    def getDeliveredBenefits(self):
        rows = self._connection.cursor().execute("SELECT * FROM benefits WHERE completed=1").fetchall()
        return [benefitFromRow(row) for row in rows]

    def getPendingBenefits(self):
        args = self.endToday,
        rows = self._connection.cursor().execute("SELECT * FROM benefits WHERE completed=0 AND endDate<?", args).fetchall()
        return [benefitFromRow(row) for row in rows]

    def getBenefit(self, storeId) -> List[Benefit]:
        id = int(storeId)
        return benefitFromRow(self._connection.cursor().execute(CMD_GET_BENEFIT, (id,)).fetchone())

    def updateBenefit(self, benefit) -> None:
        t = tuple(benefit) + (int(benefit._storeId),)
        try:
            self._connection.cursor().execute(CMD_UPDATE_BENEFIT, t)
            self._connection.commit()
            return benefit
        except sqlite.IntegrityError as error:
            raise StoreDuplicate(inner=error)

    def deleteBenefit(self, storeId) -> None:
        self._connection.cursor().execute(CMD_DELETE_BENEFIT, (storeId))
        self._connection.commit()
        self._connection.commit()

    def getQualifyingDonors(self, benefit) -> List[Donor]:
        cmd, args = getQualifyingQuery(benefit)
        rows = self._connection.cursor().execute(cmd, args).fetchall()
        return [row[0] for row in rows]

    def getDetailDonors(self) -> List[DonorDetail]:
        cmd = """
SELECT first.donor, firstDate, lastDate
FROM (
    SELECT donor,date as firstDate
    FROM donations
    GROUP BY DONOR
    HAVING MIN(ROWID)
    ORDER BY date
) first
JOIN (
    SELECT donor,date as lastDate
    FROM donations
    GROUP BY DONOR
    HAVING MAX(ROWID)
    ORDER BY date
) last
ON first.donor=last.donor
"""
        rows = self._connection.cursor().execute(cmd).fetchall()
        return [donorDetailFromRow(row) for row in rows]

    def setupStore(self):
        cursor = self._connection.cursor()
        cursor.execute(CMD_INIT_BENEFITS)
        cursor.execute(CMD_INIT_DONATIONS)
        self._connection.commit()

    def close(self):
        self._connection.close()
