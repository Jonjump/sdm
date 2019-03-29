from domain import PaymentProvider
from .store import Store, StoreConfig, StoreType, StoreDuplicate, StoreNotFound  # noqa: F401
from .storeSqllite import StoreSqlLite
from .transactionimporter import GocardlessTransactionImporter, PaypalTransactionImporter, StripeTransactionImporter


def StoreFactory(config: StoreConfig) -> Store:
    if (config.type == StoreType.SQLLITE):
        return StoreSqlLite(config)


def TransactionImporterFactory(paymentProvider, csvfile):
    if paymentProvider == PaymentProvider.PAYPAL:
        return PaypalTransactionImporter(csvfile)
    elif paymentProvider == PaymentProvider.GOCARDLESS:
        return GocardlessTransactionImporter(csvfile)
    elif paymentProvider == PaymentProvider.STRIPE:
        return StripeTransactionImporter(csvfile)
    else:
        raise Exception


__all__ = [PaymentProvider, Store, StoreConfig, StoreType, StoreDuplicate, StoreNotFound, StoreSqlLite, GocardlessTransactionImporter,
           PaypalTransactionImporter, StripeTransactionImporter, StoreFactory, TransactionImporterFactory
           ]