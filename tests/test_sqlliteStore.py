import unittest
from datetime import date, timedelta
from domain import Benefit, Currency, Delivery, Donation, DonationType, Money, PaymentProvider, BenefitType
from infrastructure import StoreConfig, StoreDuplicate, StoreFactory, StoreNotFound, StoreType


class TestStoreSqlLite(unittest.TestCase):
    @property
    def config(self):
        return StoreConfig(StoreType.SQLLITE, ":memory:")

    def getStore(self):
        s = StoreFactory(self.config)
        s.setupStore()
        return s

    @property
    def donation(self):
        return Donation(PaymentProvider.GOCARDLESS, 'ksdjhf', 'test@test.com', date(1990, 11, 11), DonationType.ANNUAL, Money(1, Currency('GBP')))

    def test_insertDonation_DoesNotThrow(self):
        s = self.getStore()
        s.insertDonation(self.donation)
        self.assertTrue(True)

    def test_insertDonation_Raises_StoreDuplicate(self):
        with self.assertRaises(StoreDuplicate):
            s = self.getStore()
            s.insertDonation(self.donation)
            s.insertDonation(self.donation)

    def test_getDonation_Raises_StoreNotFound(self):
        with self.assertRaises(StoreNotFound):
            s = self.getStore()
            s.insertDonation(self.donation)
            s.getDonation(self.donation.source, 'unknownpaymentidkjsdfhkajsdf')

    def test_getDonation_gets_Donation(self):
        s = self.getStore()
        donation = self.donation
        s.insertDonation(donation)
        donation2 = s.getDonation(donation.source, donation.paymentId)
        self.assertEqual(donation, donation2)

    def test_getDonations_gets_Donation(self):
        d = date(1900, 1, 2)
        expectedDonation = Donation(PaymentProvider.GOCARDLESS, '2', 'test@test.com', d, DonationType.ANNUAL, Money(1, Currency('GBP')))
        s = self.getStore()
        s.insertDonation(Donation(PaymentProvider.GOCARDLESS, '1', 'test@test.com', d + timedelta(days=7), DonationType.ANNUAL, Money(1, Currency('GBP'))))
        s.insertDonation(expectedDonation)
        s.insertDonation(Donation(PaymentProvider.GOCARDLESS, '3', 'test@test.com', d - timedelta(days=7), DonationType.ANNUAL, Money(1, Currency('GBP'))))
        result = s.getDonations(startDate=d-timedelta(days=1), endDate=d+timedelta(days=1))
        self.assertEqual(len(result), 1)
        self.assertEqual(expectedDonation, result[0])

    def test_getDonations_returnsEmptyList(self):
        d = date(1900, 1, 2)
        expectedDonation = Donation(PaymentProvider.GOCARDLESS, '2', 'test@test.com', d, DonationType.ANNUAL, Money(1, Currency('GBP')))
        s = self.getStore()
        s.insertDonation(expectedDonation)
        result = s.getDonations(startDate=d-timedelta(days=14), endDate=d-timedelta(days=10))
        self.assertEqual(len(result), 0)

    @property
    def BENEFIT_AMOUNT1(self):
        return Benefit.Factory(None, BenefitType.AMOUNT, "REWARD", date(2018, 1, 1), date(2018, 2, 28), Delivery.ONLINE, Money(50, Currency.gbp), False)

    @property
    def BENEFIT_AMOUNT2(self):
        return Benefit.Factory(None, BenefitType.AMOUNT, "NEW REWARD", date(2017, 1, 1), date(2017, 2, 28), Delivery.ONLINE, Money(50, Currency.gbp), False)

    def test_addBenefit_DoesNotThrow(self):
        self.getStore().addBenefit(self.BENEFIT_AMOUNT1)
        self.assertTrue(True)

    def test_getBenefit_getsByRowId(self):
        s = self.getStore()
        s.addBenefit(self.BENEFIT_AMOUNT1)
        new = s.getPendingBenefits()[0]
        result = s.getBenefit(new._storeId)
        self.assertEqual(tuple(new), tuple(result))
        self.assertEqual(new._storeId, result._storeId)

    def test_updateBenefit_updates(self):
        s = self.getStore()
        benefit1 = Benefit.Factory(None, BenefitType.AMOUNT, "reward1", date(2018, 1, 1), date(2018, 2, 28), Delivery.ONLINE, Money(50, Currency.gbp), False)
        s.addBenefit(benefit1)
        existing = s.getPendingBenefits()[0]

        s.updateBenefit(Benefit.Factory(existing._storeId, BenefitType.AMOUNTPERMONTH,
                        "reward2", date(2019, 1, 1), date(2019, 2, 28), Delivery.OFFLINE, Money(100, Currency.gbp), True))

        updated = s.getDeliveredBenefits()[0]
        self.assertEqual(updated._storeId, existing._storeId)
        self.assertNotEqual(updated.startDate, existing.startDate)
        self.assertNotEqual(updated.endDate, existing.endDate)
        self.assertNotEqual(updated.delivery, existing.delivery)
        self.assertNotEqual(updated.minAmount, existing.minAmount)
        self.assertNotEqual(updated.completed, existing.completed)

    def test_deleteBenefit_deletesBenefit(self):
        s = self.getStore()
        benefit = self.BENEFIT_AMOUNT1
        s.addBenefit(benefit)
        s.deleteBenefit("1")
        result = s.getCurrentBenefits()
        self.assertEqual(0, len(result))

    def getQualifyingDonorsResult(self, benefit):
        donations = [
            Donation(
                PaymentProvider.GOCARDLESS,
                "atstart",
                "atstart@test.com",
                date(1990, 1, 1),
                DonationType.ONEOFF,
                Money.fromString('£10')
            ),
            Donation(
                PaymentProvider.GOCARDLESS,
                "split1",
                "split@test.com",
                date(1990, 1, 1),
                DonationType.ONEOFF,
                Money.fromString('£5')
            ),
            Donation(
                PaymentProvider.GOCARDLESS,
                "split2",
                "split@test.com",
                date(1990, 1, 2),
                DonationType.MONTHLY,
                Money.fromString('£5')
            ),
            Donation(
                PaymentProvider.GOCARDLESS,
                "atend",
                "atend@test.com",
                date(1990, 1, 2) - timedelta(microseconds=1),
                DonationType.ONEOFF,
                Money.fromString('£10')
            ),
            Donation(
                PaymentProvider.GOCARDLESS,
                "toolow",
                "toolow@test.com",
                date(1990, 1, 2),
                DonationType.ONEOFF,
                Money.fromString('£9.99')
            )
        ]
        s = self.getStore()
        for d in donations:
            s.insertDonation(d)
        s.addBenefit(benefit)
        return s.getQualifyingDonors(benefit)

    def test_getQualifyingDonors_AMOUNT_ignores_earlier(self):
        benefit = Benefit.Factory(
            None, BenefitType.AMOUNT,
            "reward",
            date(1991, 1, 1),
            date(1991, 12, 31),
            Delivery.ONLINE,
            Money.fromString("£10"),
            False
        )
        result = self.getQualifyingDonorsResult(benefit)
        self.assertEqual(len(result), 0)

    def test_getQualifyingDonors_AMOUNT_ignores_later(self):
        benefit = Benefit.Factory(
            None, BenefitType.AMOUNT,
            "reward",
            date(1989, 1, 1),
            date(1989, 12, 31),
            Delivery.ONLINE,
            Money.fromString("£10"),
            False
        )
        result = self.getQualifyingDonorsResult(benefit)
        self.assertEqual(len(result), 0)

    def test_getQualifyingDonors_AMOUNT_ignores_too_low(self):
        benefit = Benefit.Factory(
            None, BenefitType.AMOUNT,
            "reward",
            date(1990, 1, 1),
            date(1990, 2, 1),
            Delivery.ONLINE,
            Money.fromString("£10"),
            False
        )
        result = self.getQualifyingDonorsResult(benefit)
        self.assertFalse('toolow@test.com' in result)

    def test_getQualifyingDonors_AMOUNT_getsSplitDonations(self):
        benefit = Benefit.Factory(
            None, BenefitType.AMOUNT,
            "reward",
            date(1990, 1, 1),
            date(1990, 2, 1),
            Delivery.ONLINE,
            Money.fromString("£10"),
            False
        )
        self.assertIn('split@test.com', self.getQualifyingDonorsResult(benefit))

    def test_getQualifyingDonors_AMOUNTPERMONTH_ignores_earlier(self):
        benefit = Benefit.Factory(
            None, BenefitType.AMOUNTPERMONTH,
            "reward",
            date(1991, 2, 1),
            date(1991, 12, 31),
            Delivery.ONLINE,
            Money.fromString("£10"),
            False
        )
        result = self.getQualifyingDonorsResult(benefit)
        self.assertEqual(len(result), 0)

    def test_getQualifyingDonors_AMOUNTPERMONTH_ignores_later(self):
        benefit = Benefit.Factory(
            None, BenefitType.AMOUNTPERMONTH,
            "reward",
            date(1989, 1, 1),
            date(1989, 12, 31),
            Delivery.ONLINE,
            Money.fromString("£10"),
            False
        )
        result = self.getQualifyingDonorsResult(benefit)
        self.assertEqual(len(result), 0)

    def test_getQualifyingDonors_AMOUNTPERMONTH_uses_start_of_month(self):
        benefit = Benefit.Factory(
            None, BenefitType.AMOUNTPERMONTH,
            "reward",
            date(1990, 1, 28),
            date(1990, 1, 1),
            Delivery.ONLINE,
            Money.fromString("£10"),
            False
        )
        donors = self.getQualifyingDonorsResult(benefit)
        self.assertIn('atstart@test.com', donors)

    def test_getQualifyingDonors_AMOUNTPERMONTH_uses_end_of_month(self):
        benefit = Benefit.Factory(
            None, BenefitType.AMOUNTPERMONTH,
            "reward",
            date(1990, 1, 28),
            date(1990, 1, 1),
            Delivery.ONLINE,
            Money.fromString("£10"),
            False
        )
        donors = self.getQualifyingDonorsResult(benefit)
        self.assertIn('atend@test.com', donors)

    def test_getQualifyingDonors_AMOUNTPERMONTH_uses_split_payments(self):
        benefit = Benefit.Factory(
            None, BenefitType.AMOUNTPERMONTH,
            "reward",
            date(1990, 1, 28),
            date(1990, 1, 1),
            Delivery.ONLINE,
            Money.fromString("£10"),
            False
        )
        donors = self.getQualifyingDonorsResult(benefit)
        self.assertIn('split@test.com', donors)

    def test_getQualifyingDonors_AMOUNTPERMONTH_ignores_too_low(self):
        benefit = Benefit.Factory(
            None, BenefitType.AMOUNTPERMONTH,
            "reward",
            date(1990, 1, 28),
            date(1990, 1, 1),
            Delivery.ONLINE,
            Money.fromString("£10"),
            False
        )
        donors = self.getQualifyingDonorsResult(benefit)
        self.assertNotIn('toolow@test.com', donors)

    def test_getQualifyingDonors_AMOUNTPERMONTH_works_across_multiple_months(self):
        s = self.getStore()
        benefit = Benefit.Factory(
            None, BenefitType.AMOUNTPERMONTH,
            "reward",
            date(1990, 1, 1),
            date(1990, 2, 1),
            Delivery.ONLINE,
            Money.fromString("£10"),
            False
        )
        s.addBenefit(benefit)
        s.insertDonation(Donation(
                PaymentProvider.GOCARDLESS,
                "1",
                "acrossmonths@test.com",
                date(1990, 1, 1),
                DonationType.ONEOFF,
                Money.fromString('£10')
            )
        )
        s.insertDonation(Donation(
                PaymentProvider.GOCARDLESS,
                "2",
                "acrossmonths@test.com",
                date(1990, 2, 1),
                DonationType.ONEOFF,
                Money.fromString('£10')
            )
        )
        donors = s.getQualifyingDonors(benefit)
        self.assertIn('acrossmonths@test.com', donors)

    def test_getQualifyingDonors_NEWDONOR_getsNewDonor(self):
        s = self.getStore()
        benefit = Benefit.Factory(
            None, BenefitType.NEWDONOR,
            "reward",
            date(1990, 2, 1),
            date(1990, 3, 1),
            Delivery.ONLINE,
            Money.fromString("£10"),
            False
        )
        s.addBenefit(benefit)
        s.insertDonation(Donation(
                PaymentProvider.GOCARDLESS,
                "1",
                "newDonor@test.com",
                date(1990, 2, 1),
                DonationType.ONEOFF,
                Money.fromString('£10')
            )
        )
        s.insertDonation(Donation(
                PaymentProvider.GOCARDLESS,
                "2",
                "notNewDonor@test.com",
                date(1990, 2, 1),
                DonationType.ONEOFF,
                Money.fromString('£10')
            )
        )
        s.insertDonation(Donation(
                PaymentProvider.GOCARDLESS,
                "3",
                "notNewDonor@test.com",
                date(1990, 1, 1),
                DonationType.ONEOFF,
                Money.fromString('£10')
            )
        )
        donors = s.getQualifyingDonors(benefit)
        self.assertListEqual(donors, [])

    def test_getQualifyingDonors_NEWDONOR_ignoresInsertOrder(self):
        s = self.getStore()
        benefit = Benefit.Factory(
            None, BenefitType.NEWDONOR,
            "reward",
            date(1990, 2, 1),
            date(1990, 3, 1),
            Delivery.ONLINE,
            Money.fromString("£10"),
            False
        )
        s.addBenefit(benefit)
        s.insertDonation(Donation(
                PaymentProvider.GOCARDLESS,
                "1",
                "insertFirst@test.com",
                date(1990, 2, 1),
                DonationType.ONEOFF,
                Money.fromString('£10')
            )
        )
        s.insertDonation(Donation(
                PaymentProvider.GOCARDLESS,
                "2",
                "insertSecond@test.com",
                date(1990, 1, 1),
                DonationType.ONEOFF,
                Money.fromString('£10')
            )
        )
        donors = s.getQualifyingDonors(benefit)
        self.assertEqual(len(donors), 0)

    def test_getQualifyingDonors_NEWDONOR_ignorestooearly(self):
        s = self.getStore()
        benefit = Benefit.Factory(
            None, BenefitType.NEWDONOR,
            "reward",
            date(1990, 2, 1),
            date(1990, 3, 1),
            Delivery.ONLINE,
            Money.fromString("£1"),
            False
        )
        s.addBenefit(benefit)
        s.insertDonation(Donation(
                PaymentProvider.GOCARDLESS,
                "1",
                "newDonor@test.com",
                date(1990, 1, 31),
                DonationType.ONEOFF,
                Money.fromString('£10')
            )
        )
        donors = s.getQualifyingDonors(benefit)
        self.assertEqual(len(donors), 0)

    def test_getQualifyingDonors_NEWDONOR_ignorestoolate(self):
        s = self.getStore()
        benefit = Benefit.Factory(
            None, BenefitType.NEWDONOR,
            "reward",
            date(1990, 2, 1),
            date(1990, 3, 1),
            Delivery.ONLINE,
            Money.fromString("£1"),
            False
        )
        s.addBenefit(benefit)
        s.insertDonation(Donation(
                PaymentProvider.GOCARDLESS,
                "1",
                "newDonor@test.com",
                date(1990, 3, 2),
                DonationType.ONEOFF,
                Money.fromString('£10')
            )
        )
        donors = s.getQualifyingDonors(benefit)
        self.assertEqual(len(donors), 0)

    def test_getDetailDonors_getsFirstAndLastDate(self):
        s = self.getStore()
        s.insertDonation(Donation(
                PaymentProvider.GOCARDLESS,
                "1",
                "newDonor@test.com",
                date(1990, 1, 1),
                DonationType.ONEOFF,
                Money.fromString('£10')
            )
        )
        s.insertDonation(Donation(
                PaymentProvider.GOCARDLESS,
                "2",
                "newDonor@test.com",
                date(1990, 2, 3),
                DonationType.ONEOFF,
                Money.fromString('£10')
            )
        )
        details = s.getDetailDonors()
        self.assertEqual(len(details), 1)
        self.assertEqual(details[0].donor, "newDonor@test.com")
        self.assertEqual(details[0].firstPaymentDate, date(1990, 1, 1))
        self.assertEqual(details[0].lastPaymentDate, date(1990, 2, 3))

