import unittest
from domain import Currency, Donation, Money, PaymentProvider, DonationType, Summary, SummaryFields, rndDate, Total

from datetime import date, timedelta


class TestDomain(unittest.TestCase):

    MONEYUSD1 = Money(50.25, Currency('USD'))
    MONEYGBP1 = Money(50.25, Currency('GBP'))

    def test_Money_fromString_reads_PreSymbol(self):
        s = "$50.25"
        self.assertEqual(Money.fromString(s), self.MONEYUSD1)

    def test_Money_fromString_reads_PostSymbol(self):
        s = "50.25$"
        self.assertEqual(Money.fromString(s), self.MONEYUSD1)

    def test_Money_fromString_reads_PreCode(self):
        s = "USD50.25"
        self.assertEqual(Money.fromString(s), self.MONEYUSD1)

    def test_Money_fromString_reads_PostCode(self):
        s = "50.25 USD"
        self.assertEqual(Money.fromString(s), self.MONEYUSD1)

    def test_Money_add_different_currencies_throws(self):
        with self.assertRaises(TypeError):
            _ = self.MONEYUSD1 + self.MONEYGBP1

    def test_Money_adds(self):
        x = self.MONEYGBP1 + self.MONEYGBP1
        self.assertEqual(x, Money.fromString("£100.50"))

    TOTAL1 = Total([MONEYGBP1, MONEYUSD1], 2)

    def test_Total_initialises_dict(self):
        self.assertEqual(len(self.TOTAL1), 2)
        self.assertTrue(self.TOTAL1[Currency('GBP')], self.MONEYGBP1)
        self.assertTrue(self.TOTAL1[Currency('USD')], self.MONEYUSD1)

    def test_Total_initialises_count(self):
        self.assertEqual(self.TOTAL1.count, 2)

    def test_Total_adds_to_dict(self):
        result = self.TOTAL1 + self.TOTAL1
        self.assertEqual(len(result), 2)
        self.assertTrue(self.TOTAL1[Currency('GBP')], self.MONEYGBP1 + self.MONEYGBP1)
        self.assertTrue(self.TOTAL1[Currency('USD')], self.MONEYUSD1 + self.MONEYUSD1)

    def test_Total_adds_to_count(self):
        result = self.TOTAL1 + self.TOTAL1
        self.assertEqual(result.count, 4)

    WEEKEND = date(2019, 2, 10)
    WEEKSTART = date(2019, 2, 11)

    def test_rndDate_weekdown_crosses_yearend(self):
        result = rndDate(date(2019, 1, 1), "week", "down")
        expected = date(2018, 12, 31)
        self.assertEqual(result, expected)

    def test_rndDate_weekdown_handles_startofweek(self):
        result = rndDate(self.WEEKSTART, "week", "down")
        self.assertEqual(result, self.WEEKSTART)

    def test_rndDateWeekDown_handles_endofweek(self):
        result = rndDate(self.WEEKEND, "week", "down")
        self.assertEqual(result, self.WEEKSTART - timedelta(days=7))

    def test_rndDateWeekUp_crosses_yearend(self):
        result = rndDate(date(2019, 12, 31), "week", "up")
        expected = date(2020, 1, 5)
        self.assertEqual(result, expected)

    def test_rndDateWeekUp_handles_startofweek(self):
        result = rndDate(self.WEEKSTART, "week", "up")
        self.assertEqual(result, self.WEEKEND+timedelta(days=7))

    def test_rndDateWeekUp_handles_endofweek(self):
        result = rndDate(self.WEEKEND, "week", "up")
        self.assertEqual(result, self.WEEKEND)

    DONATION1 = Donation(PaymentProvider.GOCARDLESS, 'ksdjhf', 'test@test.com', WEEKSTART, DonationType.ANNUAL, MONEYGBP1)
    DONATION2 = Donation(PaymentProvider.STRIPE, 'ksdjhf', 'test@test.com', WEEKEND, DonationType.MONTHLY, MONEYUSD1)

    def test_Summary_does_not_throw(self):
        Summary([self.DONATION1], [])
        self.assertTrue(True)

    def test_Summary_leaf_has_correct_total(self):
        summary = Summary([self.DONATION1, self.DONATION1], [])
        self.assertEqual(summary.total, {Currency('GBP'): self.MONEYGBP1 + self.MONEYGBP1})

    def test_Summary_has_branch(self):
        summary = Summary([self.DONATION1], [SummaryFields.SOURCE])
        self.assertTrue(PaymentProvider.GOCARDLESS in summary)

    def test_Summary_branch_has_correct_total(self):
        summary = Summary([self.DONATION1, self.DONATION1], [SummaryFields.SOURCE])
        self.assertEqual(summary[PaymentProvider.GOCARDLESS].total, {Currency('GBP'): self.MONEYGBP1 + self.MONEYGBP1})

    def test_Summary_has_branches_in_correct_order(self):
        summary = Summary([self.DONATION1], [SummaryFields.SOURCE, SummaryFields.TYPE])
        self.assertTrue(DonationType.ANNUAL in summary[PaymentProvider.GOCARDLESS])
