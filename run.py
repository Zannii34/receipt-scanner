from app import create_app
import os
from pathlib import Path

# Point pytesseract at the bundled binary (if present)
tess_home = Path.home() / "tesseract" / "squashfs-root" / "usr" / "bin" / "tesseract"
if tess_home.exists():
    os.environ.setdefault("TESSERACT_CMD", str(tess_home))

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
