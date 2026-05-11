"""Parse dates from CSV/API strings (ISO and European DD/MM/YYYY)."""
import re
from datetime import date
from typing import Optional

_DMY = re.compile(r"^(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})\b")
_YMD_SEP = re.compile(r"^(\d{4})[/.-](\d{1,2})[/.-](\d{1,2})\b")


def parse_flexible_date(val: Optional[str], *, required: bool = False) -> Optional[date]:
    """
    Accepts:
    - ISO: YYYY-MM-DD
    - Year-first with separators: YYYY/MM/DD, YYYY.MM.DD
    - European day-first: DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY
    """
    if val is None or str(val).strip() == "":
        if required:
            raise ValueError("Date is required")
        return None
    s = str(val).strip().split()[0]

    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return date.fromisoformat(s[:10])

    m = _YMD_SEP.match(s)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return date(y, mo, d)

    m = _DMY.match(s)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return date(y, mo, d)

    raise ValueError(f"Unrecognized date format (use YYYY-MM-DD or DD/MM/YYYY): {val!r}")
