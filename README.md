# Receipt Scanner

Scan receipts with OCR + camera, extract merchant, VAT, and total, and build expense lists for tax.

## Features

- 📷 Live camera capture OR file upload
- 🔍 OCR extracts merchant, total, VAT, date automatically
- ✏️ Review and edit before saving
- 📋 Group receipts into named lists (e.g., "September 2026", "Client X")
- 💰 VAT handling — subtotal, VAT amount, total, and VAT rate (15% SA default)
- 📊 Dashboard with category + monthly charts
- 📈 VAT summary per list for tax purposes

## Tech Stack

- Flask + SQLAlchemy + SQLite
- Tesseract OCR (via pytesseract)
- Chart.js for dashboard
- Vanilla JS for camera (getUserMedia)

## Local Setup

Prerequisites: Tesseract OCR installed at ``C:\Program Files\Tesseract-OCR`` on Windows.

```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python run.py
```

Open http://localhost:5001

## Usage

1. Create an expense list
2. Scan a receipt with camera or upload
3. Review the auto-extracted data
4. Save to a list
5. Check the dashboard for totals + VAT

## What I Learned

- OCR with Tesseract — pattern matching across receipt formats
- Camera capture in the browser (getUserMedia)
- VAT calculations (included vs excluded)
- Data modeling for multi-list expense tracking
- File upload + processing pipeline

## What is Next

- Receipt image storage on S3
- Multi-user accounts
- CSV / Excel export per list
- Monthly PDF reports for tax

## License

MIT
