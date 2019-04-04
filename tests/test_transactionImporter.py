# encoding: utf-8
import os
import unittest
from datetime import date
from domain import Donation, DonationType, Money, PaymentProvider
from infrastructure import GocardlessTransactionImporter, PaypalTransactionImporter, StripeTransactionImporter


class Test_TransactionImporter(unittest.TestCase):
    directory = os.path.join(os.path.dirname(__file__), 'paymentProviderTransactionFiles')
    paypalfile = os.path.join(directory, 'paypal.csv')
    paypalBadRows = os.path.join(directory, 'paypalWithBadRows.csv')
    stripefile = os.path.join(directory, 'stripe.csv')
    stripesubscriptionsfile = os.path.join(directory, 'stripe_subscriptions.csv')
    gocardlessfile = os.path.join(directory, 'gocardless.csv')

    def test_GoCardlessImporter_returns_MonthlyDonation(self):
        with open(self.gocardlessfile, newline='') as csvfile:
            csvfile.seek(0)
            expected = Donation(
                source=PaymentProvider.GOCARDLESS,
                paymentId='PM0037CY8EZAGW',
                donor='donor1@test.com',
                paymentDate=date(2018, 11, 26),
                type=DonationType.MONTHLY,
                money=Money.fromString("£50")
            )
            importer = GocardlessTransactionImporter(csvfile=csvfile)
            donations = [donation for donation in importer]
            self.assertIn(expected, donations)

    def test_GoCardlessImporter_returnsCorrectNumberOfLines(self):
        with open(self.gocardlessfile, newline='') as csvfile:
            importer = GocardlessTransactionImporter(csvfile=csvfile)
            result = 0
            for _ in importer:
                result += 1
            self.assertEqual(3, result)

    def test_PaypalImporter_returns_OneOffDonation(self):
        with open(self.paypalfile, newline='') as csvfile:
            csvfile.seek(0)
            expected = Donation(
                source=PaymentProvider.PAYPAL,
                paymentId='9PJ98647WE715635M',
                donor='donor1@test.com',
                paymentDate=date(2019, 1, 1),
                type=DonationType.ONEOFF,
                money=Money.fromString("£10")
            )
            importer = PaypalTransactionImporter(csvfile=csvfile)
            donations = [donation for donation in importer]
            self.assertIn(expected, donations)

    def test_PaypalImporter_parses_GeneralPayment(self):
        with open(self.paypalfile, newline='') as csvfile:
            csvfile.seek(0)
            expected = Donation(
                source=PaymentProvider.PAYPAL,
                paymentId='41U96238575808349',
                donor='donor2@test.com',
                paymentDate=date(2018, 10, 1),
                type=DonationType.ONEOFF,
                money=Money.fromString("£5")
            )
            importer = PaypalTransactionImporter(csvfile=csvfile)
            donations = [donation for donation in importer]
            self.assertIn(expected, donations)

    def test_PaypalImporter_returns_MonthlyDonation(self):
        with open(self.paypalfile, newline='') as csvfile:
            csvfile.seek(0)
            expected = Donation(
                source=PaymentProvider.PAYPAL,
                paymentId='5DE230869C8753128',
                donor='donor3@test.com',
                paymentDate=date(2019, 1, 2),
                type=DonationType.MONTHLY,
                money=Money.fromString("£2")
            )
            importer = PaypalTransactionImporter(csvfile=csvfile)
            donations = [donation for donation in importer]
            self.assertIn(expected, donations)

    def test_PaypalImporter_ReturnsCorrectNumberOfLines(self):
        with open(self.paypalfile, newline='') as csvfile:
            importer = PaypalTransactionImporter(csvfile=csvfile)
            donations = [x for x in importer]
            self.assertEqual(3, len(donations))
            self.assertEqual(1, len(importer.badRows))

    def test_StripeImporter_Returns_Monthly_Donation(self):
        with open(self.stripefile, newline='') as csvfile:
            expected = Donation(
                source=PaymentProvider.STRIPE,
                paymentId='ch_1E5OVoKQq0uhWMx04O3cLzGY',
                donor='monthly@test.com',
                paymentDate=date(2019, 2, 19),
                type=DonationType.MONTHLY,
                money=Money.fromString("£20")
            )
            importer = StripeTransactionImporter(csvfile=csvfile)
            donations = [x for x in importer]
            self.assertIn(expected, donations)

    def test_StripeImporter_Returns_Oneoff_Donation(self):
        with open(self.stripefile, newline='') as csvfile:
            expected = Donation(
                source=PaymentProvider.STRIPE,
                paymentId='ch_1E5WV0KQq0uhWMx0sQGwf2s3',
                donor='oneoff@test.com',
                paymentDate=date(2019, 2, 19),
                type=DonationType.ONEOFF,
                money=Money.fromString("£50")
            )
            importer = StripeTransactionImporter(csvfile=csvfile)
            donations = [x for x in importer]
            self.assertIn(expected, donations)

    def test_StripeImporter_IgnoresFailedPayments(self):
        pass

    def test_StripeImporter_IgnoresRefundedPayments(self):
        pass

    def test_StripeImporter_Returns_Correct_Number_Of_Lines(self):
        with open(self.stripefile, newline='') as csvfile:
            importer = StripeTransactionImporter(csvfile=csvfile)
            result = 0
            for _ in importer:
                result += 1
            self.assertEqual(2, result)
