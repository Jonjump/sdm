import sys
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Dict
from dataclasses import dataclass
from email.utils import parseaddr
from domain import PaymentProvider, Donation, DonationType, Money
import csv


def isEmail(s):
    return '@' in parseaddr(s)[1]


class FilteredRow(Exception):
    pass


@dataclass(frozen=True)
class CsvConfig():
    delimiter: str
    doublequote: bool
    escapechar: bool
    lineterminator: str
    quotechar: str
    quoting: int
    skipinitialspace: bool


class TransactionImporter(ABC):
    CSVCONFIG: CsvConfig

    def __init__(self, csvfile):
        """
        open file handle with newline='
        """
        self._reader = csv.DictReader(
            csvfile,
            delimiter=self.CSVCONFIG.delimiter,
            doublequote=self.CSVCONFIG.doublequote,
            escapechar=self.CSVCONFIG.escapechar,
            lineterminator=self.CSVCONFIG.lineterminator,
            quotechar=self.CSVCONFIG.quotechar,
            quoting=self.CSVCONFIG.quoting,
            skipinitialspace=self.CSVCONFIG.skipinitialspace,
        )
        self.badRows = []

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            row = self._reader.__next__()
            try:
                return self.parser(self._filter(row))
            except StopIteration as e:
                raise e
            except Exception:
                self.badRows.append((self._reader.line_num, sys.exc_info()[0], row))

    @abstractmethod
    def parser(self, row):
        pass

    @abstractmethod
    def _filter(self, row):
        return row


class GocardlessTransactionImporter (TransactionImporter):
    SOURCE = PaymentProvider.GOCARDLESS
    HEADER = 'id,created_at,charge_date,amount,description,currency,status,amount_refunded,reference,transaction_fee,payout_date,app_fee,links.mandate,links.creditor,links.customer,links.payout,links.subscription,customers.id,customers.created_at,customers.email,customers.given_name,customers.family_name,customers.company_name,customers.address_line1,customers.address_line2,customers.address_line3,customers.city,customers.region,customers.postal_code,customers.country_code,customers.language,customers.swedish_identity_number,customers.active_mandates\n'
    CSVCONFIG = CsvConfig(
        delimiter=',',
        doublequote=True,
        escapechar=None,
        lineterminator='\r\n',
        quotechar='"',
        quoting=csv.QUOTE_MINIMAL,
        skipinitialspace=False,
    )

    def parser(self, row):
        return Donation(
            source=self.SOURCE,
            paymentId=row["id"],
            donor=row["customers.email"],
            paymentDate=datetime.strptime(row["charge_date"], '%d/%m/%Y').date(),
            type=DonationType.MONTHLY,
            money=Money.fromString(row["currency"]+row["amount"])
        )

    def _filter(self, row):
        if float(row["amount"]) <= 0:
            raise FilteredRow('gross le 0')
        return row


class PaypalTransactionImporter (TransactionImporter):
    SOURCE = PaymentProvider.PAYPAL
    HEADER = '"Date","Time","Time zone","Name","Type","Status","Currency","Gross","Fee","Net","From Email Address","To Email Address","Transaction ID","Counterparty Status","Shipping Address","Address Status","Option 1 Name","Reference Txn ID","Quantity","Receipt ID","Country","Contact Phone Number","Subject","Balance Impact","Buyer Wallet"\n'
    CSVCONFIG = CsvConfig(
        delimiter=',',
        doublequote=True,
        escapechar=None,
        lineterminator='\r\n',
        quotechar='"',
        quoting=csv.QUOTE_MINIMAL,
        skipinitialspace=False,
    )
    DONATIONTYPES: Dict[str, DonationType] = {
        "General Payment": DonationType.ONEOFF,
        "Donation Payment": DonationType.ONEOFF,
        "Subscription Payment": DonationType.MONTHLY,
    }

    def parser(self, row) -> Donation:
        return Donation(
            source=self.SOURCE,
            paymentId=row["Transaction ID"],
            donor=row["From Email Address"],
            paymentDate=datetime.strptime(row["Date"], '%d/%m/%Y').date(),
            type=self.DONATIONTYPES[row["Type"]],
            money=Money.fromString(row["Currency"]+row["Gross"])
        )

    def _filter(self, row):
        if float(row["Gross"]) <= 0:
            raise FilteredRow('gross le 0')
        if row["Status"] != 'Completed':
            raise FilteredRow('not completed status')
        return row


class StripeTransactionImporter (TransactionImporter):
    SOURCE = PaymentProvider.STRIPE
    HEADER = "id,Description,Seller Message,Created (UTC),Amount,Amount Refunded,Currency,Converted Amount,Converted Amount Refunded,Fee,Tax,Converted Currency,Mode,Status,Statement Descriptor,Customer ID,Customer Description,Customer Email,Captured,Card ID,Card Last4,Card Brand,Card Funding,Card Exp Month,Card Exp Year,Card Name,Card Address Line1,Card Address Line2,Card Address City,Card Address State,Card Address Country,Card Address Zip,Card Issue Country,Card Fingerprint,Card CVC Status,Card AVS Zip Status,Card AVS Line1 Status,Card Tokenization Method,Disputed Amount,Dispute Status,Dispute Reason,Dispute Date (UTC),Dispute Evidence Due (UTC),Invoice ID,Payment Source Type,Destination,Transfer,Interchange Costs,Merchant Service Charge,Transfer Group,PaymentIntent ID\n"
    CSVCONFIG = CsvConfig(
        delimiter=',',
        doublequote=True,
        escapechar=None,
        lineterminator='\r\n',
        quotechar='"',
        quoting=csv.QUOTE_MINIMAL,
        skipinitialspace=False,
    )

    def __init__(self, csvfile):
        super().__init__(csvfile)

    def _getDonationType(self, row):
        if row["Description"][:19].lower().strip() == "payment for invoice":
            return DonationType.MONTHLY
        return DonationType.ONEOFF

    def _filter(self, row):
        if float(row["Amount"]) <= 0:
            raise FilteredRow('gross le 0')
        if row["Status"].lower().strip() != "paid":
            raise FilteredRow('not paid')
        return row

    def _getEmail(self, row):
        if isEmail(row["Customer Email"]):
            return row["Customer Email"]
        if isEmail(row["Card Name"]):
            return row["Card Name"]
        raise Exception("No Email found")

    def parser(self, row) -> Donation:
        return Donation(
                source=self.SOURCE,
                paymentId=row["id"],
                donor=self._getEmail(row),
                paymentDate=datetime.strptime(row["Created (UTC)"], '%d/%m/%Y %H:%M').date(),
                type=self._getDonationType(row),
                money=Money.fromString(row["Currency"].upper()+row["Amount"])
            )
