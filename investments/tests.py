import datetime

import pytz

from investments.model import Company, Account, add_saving, DebitTransaction, Saving, add_investment, CreditTransaction


def test_adds_new_saving():
    company = Company(name="Santander")
    account = Account(name="Debit account", company=company, balance=0)

    source_of_fund = "Company salary"
    amount = 100
    date = pytz.utc.localize(datetime.datetime.utcnow())
    saving = add_saving(source_of_funds=source_of_fund, amount=amount, date=date, account=account)

    expected_debit_transaction = DebitTransaction(amount=amount, date=date, destination_account=account)
    assert saving is not None
    assert saving.transactions[0] == expected_debit_transaction
    assert account.balance == amount


def test_adds_new_investment_with_bank_as_source():
    bank = Company(name="Santander")
    bank_account = Account(name="Debit account", company=bank)
    bank_balance = 100
    utc_now = pytz.utc.localize(datetime.datetime.utcnow())
    add_saving(source_of_funds="Company salary", amount=bank_balance, date=utc_now, account=bank_account)

    investment_company = Company(name="Cetes Directo")
    investment_account = Account(name="Cetes 28 días", company=investment_company)
    investment_initial_amount = 100
    investment_start_date = utc_now

    investment = add_investment(destination_account=investment_account, source_account=bank_account, rate=4.22,
                                days=28, initial_amount=investment_initial_amount, start_date=investment_start_date,
                                end_date=utc_now + datetime.timedelta(days=28), final_amount_before_taxes=100.33,
                                final_amount_after_taxes=100.22)

    # THOUGHTS: es muy redundante? ayuda a ser explicito?
    expected_bank_account_balance = bank_balance - investment_initial_amount
    assert bank_account.balance == expected_bank_account_balance

    expected_bank_credit_transaction = CreditTransaction(amount=-investment_initial_amount, date=investment_start_date,
                                                         destination_account=investment_account, source_account=bank_account)
    expected_investment_debit_transaction = DebitTransaction(amount=investment_initial_amount,
                                                             date=investment_start_date,
                                                             destination_account=investment_account,
                                                             source_account=bank_account)
    assert investment is not None
    assert investment.transactions[0] == expected_bank_credit_transaction
    assert investment.transactions[1] == expected_investment_debit_transaction
    assert investment.amount == investment_initial_amount


# TODO: repo de github con ramas para ir plasamando el progreso/pensamientos

# TODO: caso de uso que se encargue de agregar una nueva inversion, añadiendo el saving correpsoindinete,
# en este punto el usuario sera agnostico acerca de la cuenta de banco (el proposito del sistema es manejar inversiones, no ahorros)
# el ahorro nos interesa por fines estadisticos de saber de donde viene la plata y para mantener armonia con la partida doble de la contabilidad