"""Tests for NLP intent classification and entity extraction."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.nlp_engine import classify_intent, extract_amount


class TestIntentClassification:
    def test_withdraw_english(self):
        r = classify_intent("I want to withdraw 500 rupees", "English")
        assert r["intent"] == "withdraw"

    def test_balance_english(self):
        r = classify_intent("check my balance", "English")
        assert r["intent"] == "balance"

    def test_statement_english(self):
        r = classify_intent("show mini statement", "English")
        assert r["intent"] == "mini_statement"

    def test_greeting_english(self):
        r = classify_intent("hello", "English")
        assert r["intent"] == "greeting"

    def test_goodbye_english(self):
        r = classify_intent("bye", "English")
        assert r["intent"] == "goodbye"

    def test_withdraw_hindi(self):
        r = classify_intent("मुझे पैसे निकालने हैं", "Hindi")
        assert r["intent"] == "withdraw"

    def test_balance_hindi(self):
        r = classify_intent("बैलेंस चेक करें", "Hindi")
        assert r["intent"] == "balance"

    def test_greeting_gujarati(self):
        r = classify_intent("નમસ્તે", "Gujarati")
        assert r["intent"] == "greeting"

    def test_withdraw_tamil(self):
        r = classify_intent("பணம் எடுக்க வேண்டும்", "Tamil")
        assert r["intent"] == "withdraw"

    def test_balance_bengali(self):
        r = classify_intent("ব্যালেন্স দেখান", "Bengali")
        assert r["intent"] == "balance"


class TestAmountExtraction:
    def test_rupee_symbol(self):
        assert extract_amount("₹500") == 500

    def test_rs_prefix(self):
        assert extract_amount("Rs 1000") == 1000

    def test_plain_number(self):
        assert extract_amount("withdraw 2000") == 2000

    def test_number_with_commas(self):
        assert extract_amount("₹10,000") == 10000

    def test_no_amount(self):
        assert extract_amount("check balance") is None

    def test_devanagari_numerals(self):
        assert extract_amount("₹५००") == 500
