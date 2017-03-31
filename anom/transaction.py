import logging

from enum import Enum, auto
from functools import wraps

from .adapter import get_adapter

_logger = logging.getLogger("transaction")


class Transaction:  # pragma: no cover
    """Abstract base class for Datastore transactions.
    """

    class Propagation(Enum):
        """An enum of the various modes transactions can be run in.
        """

        #: Nested transactions should be grouped together into a single
        #: transaction.
        Nested = auto()

        #: Nested transcations should be run independently of their
        #: parent transactions.
        Independent = auto()

    def begin(self):
        "Start this transaction."
        raise NotImplementedError

    def commit(self):
        "Commit this Transaction to Datastore."
        raise NotImplementedError

    def rollback(self):
        "Roll this Transaction back."
        raise NotImplementedError

    def end(self):
        "Clean up this Transaction object."
        raise NotImplementedError


class TransactionError(Exception):
    """Base class for Transaction errors.
    """


class TransactionFailed(TransactionError):
    """Raised by Adapters when a Transaction cannot be applied.

    Parameters:
      message(str): A message.
      cause(Exception or None): The exception that caused this
        Transaction to fail.
    """

    def __init__(self, message, cause=None):
        self.message = message
        self.cause = cause

    def __str__(self):  # pragma: no cover
        return self.message


class RetriesExceeded(TransactionError):
    """Raised by the transactional decorator when it runs out of
    retries while trying to apply a transaction.

    Parameters:
      cause(TransactionError): The last transaction error that caused
        a retry.
    """

    def __init__(self, cause):
        self.cause = cause

    def __str__(self):  # pragma: no cover
        return str(self.cause)


def transactional(*, adapter=None, retries=3, propagation=Transaction.Propagation.Nested):
    """Decorates functions so that all of their operations (except for
    queries) run inside a Datastore transaction.

    Parameters:
      adapter(Adapter, optional): The Adapter to use when running the
        transaction.  Defaults to the current adapter.
      retries(int, optional): The number of times to retry the
        transaction if it couldn't be committed.
      propagation(Transaction.Propagation, optional): The propagation
        strategy to use. By default, transactions are nested, but you
        can force certain transactions to always run independently.

    Raises:
      anom.RetriesExceeded: When the decorator runbs out of retries
        while trying to commit the transaction.

    Returns:
      callable: The decorated function.
    """
    def decorator(fn):
        @wraps(fn)
        def inner(*args, **kwargs):
            nonlocal adapter
            adapter = adapter or get_adapter()
            attempts, cause = 0, None
            while attempts <= retries:
                attempts += 1
                transaction = adapter.transaction(propagation)

                try:
                    transaction.begin()
                    res = fn(*args, **kwargs)
                    transaction.commit()
                    return res

                except TransactionFailed as e:
                    cause = e
                    continue

                except Exception as e:
                    transaction.rollback()
                    raise e

                finally:
                    transaction.end()

            raise RetriesExceeded(cause)
        return inner
    return decorator
