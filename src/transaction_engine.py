"""
Transaction Engine — ATM transaction simulation with mock banking data.
"""

import streamlit as st
from datetime import datetime, timedelta
import random


# ─────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────
DAILY_WITHDRAWAL_LIMIT = 20000
PER_TRANSACTION_LIMIT = 10000
MIN_WITHDRAWAL = 100
INITIAL_BALANCE = 25000


def _generate_mock_history() -> list:
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

    history = []
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


def init_transaction_state():
    """Initialize transaction-related session state."""
    if "account" not in st.session_state:
        st.session_state.account = {
            "card_number": "XXXX-XXXX-XXXX-1234",
            "account_type": "Savings",
            "holder_name": "Demo User",
            "balance": INITIAL_BALANCE,
            "daily_withdrawn": 0,
            "last_withdrawal_date": None,
            "transaction_history": _generate_mock_history(),
        }


def _reset_daily_limit():
    """Reset daily withdrawal counter if it's a new day."""
    today = datetime.now().date()
    last_date = st.session_state.account.get("last_withdrawal_date")
    if last_date != today:
        st.session_state.account["daily_withdrawn"] = 0
        st.session_state.account["last_withdrawal_date"] = today


def check_balance() -> dict:
    """
    Check account balance.
    Returns: {"success": True, "balance": int}
    """
    return {
        "success": True,
        "balance": st.session_state.account["balance"],
        "account_type": st.session_state.account["account_type"],
        "card_number": st.session_state.account["card_number"],
    }


def withdraw(amount: int) -> dict:
    """
    Process a withdrawal request.
    Returns: {
        "success": bool,
        "message": str,        # success/error message key
        "amount": int,
        "balance": int,
        "receipt": dict | None
    }
    """
    _reset_daily_limit()
    account = st.session_state.account

    # Validate amount is positive
    if amount <= 0:
        return {
            "success": False,
            "message": "invalid_amount",
            "amount": amount,
            "balance": account["balance"],
            "receipt": None,
        }

    # Validate multiples of 100
    if amount % MIN_WITHDRAWAL != 0:
        return {
            "success": False,
            "message": "invalid_amount",
            "amount": amount,
            "balance": account["balance"],
            "receipt": None,
        }

    # Check per-transaction limit
    if amount > PER_TRANSACTION_LIMIT:
        return {
            "success": False,
            "message": "exceed_limit",
            "amount": amount,
            "balance": account["balance"],
            "receipt": None,
            "limit": PER_TRANSACTION_LIMIT,
        }

    # Check daily limit
    if account["daily_withdrawn"] + amount > DAILY_WITHDRAWAL_LIMIT:
        remaining = DAILY_WITHDRAWAL_LIMIT - account["daily_withdrawn"]
        return {
            "success": False,
            "message": "exceed_limit",
            "amount": amount,
            "balance": account["balance"],
            "receipt": None,
            "limit": remaining,
        }

    # Check sufficient balance
    if amount > account["balance"]:
        return {
            "success": False,
            "message": "insufficient_funds",
            "amount": amount,
            "balance": account["balance"],
            "receipt": None,
        }

    # Process withdrawal
    account["balance"] -= amount
    account["daily_withdrawn"] += amount
    account["last_withdrawal_date"] = datetime.now().date()

    # Add to transaction history
    tx_record = {
        "date": datetime.now().strftime("%d-%b-%Y %H:%M"),
        "type": "Debit",
        "description": "ATM Cash Withdrawal",
        "amount": amount,
        "balance": account["balance"],
    }
    account["transaction_history"].append(tx_record)

    receipt = {
        "card_number": account["card_number"],
        "date_time": datetime.now().strftime("%d-%b-%Y %H:%M:%S"),
        "transaction_type": "Cash Withdrawal",
        "amount": amount,
        "available_balance": account["balance"],
        "reference_no": f"ATM{random.randint(100000, 999999)}",
    }

    return {
        "success": True,
        "message": "withdraw_success",
        "amount": amount,
        "balance": account["balance"],
        "receipt": receipt,
    }


def get_mini_statement() -> dict:
    """
    Get the last 5 transactions.
    Returns: {"success": True, "transactions": list, "balance": int}
    """
    account = st.session_state.account
    transactions = account["transaction_history"][-5:]

    return {
        "success": True,
        "transactions": transactions,
        "balance": account["balance"],
        "card_number": account["card_number"],
    }


def format_currency(amount: int) -> str:
    """Format an integer amount as Indian currency string."""
    # Indian numbering system: first group of 3, then groups of 2
    s = str(amount)
    if len(s) <= 3:
        return f"₹{s}"

    last_three = s[-3:]
    remaining = s[:-3]

    # Add commas every 2 digits for the remaining part
    groups = []
    while len(remaining) > 2:
        groups.insert(0, remaining[-2:])
        remaining = remaining[:-2]
    if remaining:
        groups.insert(0, remaining)

    return f"₹{','.join(groups)},{last_three}"
