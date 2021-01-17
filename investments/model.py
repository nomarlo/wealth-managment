from __future__ import annotations

import datetime
import typing
from dataclasses import dataclass

from investments.exceptions import InsufficientFunds


@dataclass
class Company:
    name: str


class Account:
    def __init__(self, name: str, company: Company, balance: int = 0):
        self.name = name
        self.company = company
        # hacerlo un property con un setter que haga raise d euna excepcion indicando queno sepude modificar y que seusen los metodos
        self.balance = balance

    def add_funds(self, debit_transaction: DebitTransaction):
        self.balance += debit_transaction.amount

    def withdraw_funds(self, credit_transaction: CreditTransaction):
        if credit_transaction.amount > self.balance:
            raise InsufficientFunds
        # THOUGHTS: el sumar el monto de una transaccion cuando se estan retirando fondos,
        # se siente anti natural. ¿Los montos de las transacciones deberian ser absolutos?
        # Si son absolutos el tipo de transaccion deberia encargarse del signo?,
        # tal vez una property que devuelva (-),
        # aunque con eso tendriamos el mismo de que no se siente natural, sumar cuando estas restando (retirando fondos)
        self.balance += credit_transaction.amount


@dataclass(frozen=True, unsafe_hash=True)
class Transaction:
    amount: float
    date: datetime.datetime
    destination_account: Account
    source_account: Account = None


@dataclass(frozen=True, unsafe_hash=True)
class DebitTransaction(Transaction):
    def __post_init__(self):
        if self.amount <= 0:
            raise ValueError("Amount for debit transaction have to be positive and different than zero")


@dataclass(frozen=True, unsafe_hash=True)
class CreditTransaction(Transaction):
    def __post_init__(self):
        if self.amount >= 0:
            raise ValueError("Amount for credit transaction have to be negative and different than zero")


class EconomicOperation:
    def __init__(self, amount: float, date: datetime.datetime, transactions: list[Transaction], account: Account):
        self.amount = amount
        self.date = date
        self.transactions = transactions
        self.account = account


class Saving(EconomicOperation):
    def __init__(self, source_of_funds: str, amount: float, date: datetime.datetime, transaction: DebitTransaction,
                 account: Account):
        super().__init__(amount=amount, date=date, transactions=[transaction], account=account)
        self.source_of_funds = source_of_funds


class Investment(EconomicOperation):
    def __init__(self, rate: float, days: int, initial_amount: float, final_amount_before_taxes: float,
                 final_amount_after_taxes: float, start_date: datetime.datetime, end_date: datetime.datetime,
                 transactions: tuple[CreditTransaction, DebitTransaction], account: Account):
        super().__init__(amount=initial_amount, date=start_date, transactions=list(transactions), account=account)
        self.rate = rate
        self.days = days
        self.final_amount_before_taxes = final_amount_before_taxes
        self.final_amount_after_taxes = final_amount_after_taxes
        self.end_date = end_date


def add_saving(source_of_funds: str, amount: float, date: datetime.datetime, account: Account) -> Saving:
    debit = _add_funds_without_source_account(amount=amount, date=date, destination_account=account)
    return Saving(source_of_funds=source_of_funds, amount=amount, date=date, transaction=debit, account=account)


def _add_funds_without_source_account(amount: float, date: datetime.datetime,
                                      destination_account: Account) -> DebitTransaction:
    debit_transaction = DebitTransaction(amount=amount, date=date, destination_account=destination_account)
    destination_account.add_funds(debit_transaction=debit_transaction)
    return debit_transaction


def add_investment(destination_account: Account, source_account: Account, rate: float, days: int,
                   initial_amount: float, start_date: datetime.datetime, end_date: datetime.datetime,
                   final_amount_before_taxes: float, final_amount_after_taxes: float):
    # THOUGHTS: las dos transacciones (credito y debito) le pertenecen a la inversion porque se necistan dos movimientos para que esta se genere
    transactions = _transfer_funds(amount=initial_amount, date=start_date, source_account=source_account,
                                   destination_account=destination_account)
    return Investment(rate=rate, days=days, initial_amount=initial_amount,
                      final_amount_before_taxes=final_amount_before_taxes,
                      final_amount_after_taxes=final_amount_after_taxes, start_date=start_date, end_date=end_date,
                      transactions=transactions, account=destination_account)


def _transfer_funds(amount: float, date: datetime.datetime, source_account: Account,
                    destination_account: Account) -> tuple[CreditTransaction, DebitTransaction]:
    credit_transaction = CreditTransaction(amount=-amount, date=date, source_account=source_account,
                                           destination_account=destination_account)
    source_account.withdraw_funds(credit_transaction=credit_transaction)

    debit_transaction = DebitTransaction(amount=amount, date=date, source_account=source_account,
                                         destination_account=destination_account)
    destination_account.add_funds(debit_transaction=debit_transaction)

    return credit_transaction, debit_transaction
