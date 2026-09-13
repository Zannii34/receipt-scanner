import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ocr import parse_total, parse_vat, parse_subtotal, parse_date, categorize


def test_parse_total_basic():
    assert parse_total('Total: R123.45') == 123.45


def test_parse_total_amount_due():
    assert parse_total('Amount Due: R250.00') == 250.00


def test_parse_vat():
    assert parse_vat('VAT (15%): R15.00') == 15.00


def test_parse_subtotal():
    assert parse_subtotal('Subtotal: R100.00') == 100.00


def test_parse_date_iso():
    result = parse_date('Date: 2026-09-12')
    assert result is not None
    assert result.year == 2026


def test_categorize_food():
    assert categorize('Woolworths', 'groceries') == 'food'


def test_categorize_transport():
    assert categorize('Uber', '') == 'transport'


def test_categorize_unknown():
    assert categorize('Random', '') == 'other'