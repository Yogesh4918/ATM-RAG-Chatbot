"""
Transaction Engine — ATM transaction simulation with mock banking data.
Framework-agnostic: accepts and returns plain dicts.
"""

from datetime import datetime, timedelta
from typing import Optional
import random
import logging

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────
DAILY_WITHDRAWAL_LIMIT: int = 20000
PER_TRANSACTION_LIMIT: int = 10000
MIN_WITHDRAWAL: int = 100
INITIAL_BALANCE: int = 25000


def generate_mock_history() -> list:
    """Generate mock transaction history for the account."""
    tx_types = [
        ("Credit", "Salary Credited", 2000, 50000),
        ("Debit", "ATM Withdrawal", 500, 10000),
        ("Credit", "UPI Transfer Received", 100, 5000),
        ("Debit", "Online Purchase", 200, 15000),
        ("Debit", "Bill Payment", 100, 5000),
        ("Credit", "Refund", 50, 2000),
        ("Debit", "Fund Transfer", 500, 25000),
    ]

    history: list = []
    running_balance = INITIAL_BALANCE
    base_date = datetime.now()

    for i in range(10):
        tx_type, desc, min_amt, max_amt = random.choice(tx_types)
        amount = random.randrange(min_amt, max_amt, 100)

        if tx_type == "Credit":
            running_balance += amount
        else:
            if running_balance >= amount:
                running_balance -= amount
            else:
                continue

        history.append({
            "date": (base_date - timedelta(days=i, hours=random.randint(1, 23))).strftime("%d-%b-%Y %H:%M"),
            "type": tx_type,
            "description": desc,
            "amount": amount,
            "balance": running_balance,
        })

    return list(reversed(history))


def check_balance(account: dict) -> dict:
    """
    Check account balance.
    Returns: {"success": True, "balance": int, ...}
    """
    return {
        "success": True,
        "balance": account["balance"],
        "account_type": account.get("account_type", "Savings"),
        "card_number": account["card_number"],
    }


def withdraw(account: dict, amount: int) -> dict:
    """
    Process a withdrawal request.
    Mutates the account dict on success.
    Returns result dict with success status.
    """
    today = datetime.now().date()
    if account.get("last_withdrawal_date") != str(today):
        account["daily_withdrawn"] = 0

    # Validate amount is positive
    if amount <= 0:
        return _error(account, "invalid_amount", amount)

    # Validate multiples of 100
    if amount % MIN_WITHDRAWAL != 0:
        return _error(account, "invalid_amount", amount)

    # Check per-transaction limit
    if amount > PER_TRANSACTION_LIMIT:
        return _error(account, "exceed_limit", amount, limit=PER_TRANSACTION_LIMIT)

    # Check daily limit
    if account["daily_withdrawn"] + amount > DAILY_WITHDRAWAL_LIMIT:
        remaining = DAILY_WITHDRAWAL_LIMIT - account["daily_withdrawn"]
        return _error(account, "exceed_limit", amount, limit=remaining)

    # Check sufficient balance
    if amount > account["balance"]:
        return _error(account, "insufficient_funds", amount)

    # Process withdrawal
    account["balance"] -= amount
    account["daily_withdrawn"] += amount
    account["last_withdrawal_date"] = str(today)

    ref = f"ATM{random.randint(100000, 999999)}"
    tx_record = {
        "date": datetime.now().strftime("%d-%b-%Y %H:%M"),
        "type": "Debit",
        "description": "ATM Cash Withdrawal",
        "amount": amount,
        "balance": account["balance"],
    }
    account["transaction_history"].append(tx_record)
    logger.info("Withdrawal processed: amount=%d, ref=%s", amount, ref)

    receipt = {
        "card_number": account["card_number"],
        "date_time": datetime.now().strftime("%d-%b-%Y %H:%M:%S"),
        "transaction_type": "Cash Withdrawal",
        "amount": amount,
        "available_balance": account["balance"],
        "reference_no": ref,
    }

    return {
        "success": True,
        "message": "withdraw_success",
        "amount": amount,
        "balance": account["balance"],
        "receipt": receipt,
    }


def get_mini_statement(account: dict) -> dict:
    """Get the last 5 transactions."""
    return {
        "success": True,
        "transactions": account["transaction_history"][-5:],
        "balance": account["balance"],
        "card_number": account["card_number"],
    }


def format_currency(amount: int) -> str:
    """Format an integer amount as Indian currency string (₹1,25,000)."""
    s = str(abs(int(amount)))
    if len(s) <= 3:
        return f"₹{s}"
    last_three = s[-3:]
    remaining = s[:-3]
    groups: list = []
    while len(remaining) > 2:
        groups.insert(0, remaining[-2:])
        remaining = remaining[:-2]
    if remaining:
        groups.insert(0, remaining)
    return f"₹{','.join(groups)},{last_three}"


def _error(account: dict, message: str, amount: int, **kwargs) -> dict:
    """Helper to build error response."""
    result = {
        "success": False,
        "message": message,
        "amount": amount,
        "balance": account["balance"],
        "receipt": None,
    }
    result.update(kwargs)
    return result
