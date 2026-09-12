"""OCR + parsing logic for receipts."""
import os
import re
from datetime import datetime
from pathlib import Path
import pytesseract
from PIL import Image

# Tesseract binary location — configurable via env var for Render
TESSERACT_CMD = os.environ.get("TESSERACT_CMD")
if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
elif os.name == "nt":
    # Windows default
    default_win = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if Path(default_win).exists():
        pytesseract.pytesseract.tesseract_cmd = default_win


def extract_text(image_path):
    """Run OCR on an image and return the raw text."""
    img = Image.open(image_path)
    return pytesseract.image_to_string(img)


def _parse_money(s):
    """Parse a money string like '1,234.56' or '1.234,56'."""
    if not s:
        return None
    s = s.strip().replace("R", "").replace("$", "").strip()
    m = re.search(r"(\d{1,3}(?:[,]\d{3})*\.\d{2})", s)
    if m:
        try:
            return float(m.group(1).replace(",", ""))
        except ValueError:
            pass
    m = re.search(r"(\d{1,3}(?:[.]\d{3})*,\d{2})", s)
    if m:
        try:
            return float(m.group(1).replace(".", "").replace(",", "."))
        except ValueError:
            pass
    m = re.search(r"(\d+[\.,]\d{2})", s)
    if m:
        try:
            return float(m.group(1).replace(",", "."))
        except ValueError:
            pass
    return None


def parse_total(text):
    patterns = [
        r"(?:total\s*(?:due|amount|incl|payable)?|amount\s*due|balance\s*due)[:\s]*([\d,\.]+)",
        r"(?:^|\n)\s*total[^\n]*?([\d,\.]+)\s*(?:$|\n)",
        r"(?:R|\$)\s*([\d,\.]+)",
    ]
    candidates = []
    for pat in patterns:
        for m in re.finditer(pat, text, re.IGNORECASE | re.MULTILINE):
            val = _parse_money(m.group(1))
            if val is not None:
                candidates.append(val)
    return max(candidates) if candidates else None


def parse_vat(text):
    patterns = [r"(?:VAT|V\.A\.T\.|Tax|GST)[^\n]*?([\d,\.]+)"]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = _parse_money(m.group(1))
            if val is not None:
                return val
    return None


def parse_subtotal(text):
    patterns = [r"(?:sub\s*-?\s*total|excl\.?\s*VAT|before\s*VAT)[^\n]*?([\d,\.]+)"]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = _parse_money(m.group(1))
            if val is not None:
                return val
    return None


def parse_vat_rate(text):
    m = re.search(r"(\d{1,2})\s*%\s*(?:VAT|V\.A\.T\.|Tax)", text, re.IGNORECASE)
    if m:
        try:
            return int(m.group(1)) / 100.0
        except ValueError:
            pass
    m = re.search(r"(?:VAT|V\.A\.T\.|Tax)\s*(?:at|@)?\s*(\d{1,2})\s*%", text, re.IGNORECASE)
    if m:
        try:
            return int(m.group(1)) / 100.0
        except ValueError:
            pass
    return 0.15


def parse_date(text):
    patterns = [
        r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})",
        r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            try:
                if len(m.group(1)) == 4:
                    return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))).date()
                else:
                    return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1))).date()
            except ValueError:
                continue
    return None


def parse_merchant(text):
    for line in text.splitlines():
        line = line.strip()
        if len(line) > 2 and not re.match(r"^[\d\W]+$", line):
            return line[:100]
    return None


CATEGORY_KEYWORDS = {
    "food": ["restaurant", "cafe", "coffee", "pizza", "burger", "mcdonald", "kfc", "food", "grocer", "market", "spar", "pick n pay", "checkers", "woolworths"],
    "transport": ["uber", "bolt", "taxi", "fuel", "petrol", "gas", "shell", "engen", "parking", "sasol", "bp"],
    "office": ["stationery", "office", "printer", "ink", "paper", "cna", "pna"],
    "utilities": ["electric", "water", "municipal", "internet", "airtime", "vodacom", "mtn", "telkom", "cell c"],
    "entertainment": ["cinema", "movie", "netflix", "spotify", "game", "steam", "ster kinekor"],
    "health": ["pharmacy", "clinic", "hospital", "doctor", "dischem", "medic", "clicks"],
    "shopping": ["shop", "store", "mall", "clothing", "retail", "makro", "takealot"],
}


def categorize(merchant, text):
    combined = ((merchant or "") + " " + (text or "")).lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in combined:
                return category
    return "other"


def process_receipt(image_path):
    text = extract_text(image_path)
    total = parse_total(text)
    vat = parse_vat(text)
    subtotal = parse_subtotal(text)
    vat_rate = parse_vat_rate(text)

    if total and vat and not subtotal:
        subtotal = round(total - vat, 2)
    if subtotal and vat and not total:
        total = round(subtotal + vat, 2)
    if total and not vat and vat_rate:
        vat = round(total * vat_rate / (1 + vat_rate), 2)
        subtotal = round(total - vat, 2)

    return {
        "raw_text": text,
        "merchant": parse_merchant(text),
        "total": total,
        "subtotal": subtotal,
        "vat_amount": vat,
        "vat_included": vat is not None,
        "vat_rate": vat_rate,
        "date": parse_date(text),
        "category": categorize(parse_merchant(text), text),
    }
