import re

# Regex patterns for common PII
# Note: These are examples and may need refinement for specific use cases and edge cases.

EMAIL_PATTERN = re.compile(
    r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
)

# Corrected PHONE_PATTERN using re.VERBOSE properly
PHONE_PATTERN = re.compile(r"""
    (?:\+?1[ -]?)?        # Optional country code +1
    (?:\(?\d{3}\)?[-. ]?)? # Optional area code (e.g., (123) or 123)
    \d{3}[-. ]?            # First 3 digits of main number
    \d{4}                  # Last 4 digits of main number
    \b                     # Word boundary to avoid partial matches
""", re.VERBOSE)

SSN_PATTERN = re.compile(
    r'\b\d{3}-?\d{2}-?\d{4}\b' # Matches XXX-XX-XXXX or XXXXXXXXX
)

# Simple Date Pattern (various formats like YYYY-MM-DD, MM/DD/YYYY, Month D, YYYY)
# This is very basic and will have false positives/negatives. Needs refinement.
DATE_PATTERN = re.compile(r"""
    \b(?:
        \d{4}-\d{1,2}-\d{1,2} | # YYYY-MM-DD
        \d{1,2}[/-]\d{1,2}[/-]\d{2,4} | # MM/DD/YYYY or MM-DD-YY etc.
        (?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},\s+\d{4} | # Month D, YYYY
        \d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?),\s+\d{4}   # D Month, YYYY
    )\b
""", re.IGNORECASE | re.VERBOSE)

# Basic Credit Card Pattern (detects sequences matching common lengths/formats)
# WARNING: High chance of false positives (matching other numbers). Luhn check often needed.
CREDIT_CARD_PATTERN = re.compile(r"""
    \b(?:
        (?:\d{4}[- ]?){3}\d{4} | # Visa, Mastercard, Discover (16 digits, optional separators)
        \d{4}[- ]?\d{6}[- ]?\d{5}   # Amex (15 digits, optional separators)
    )\b
""", re.VERBOSE)

# US ZIP Code Pattern (5 digit or ZIP+4)
ZIP_CODE_PATTERN = re.compile(
    r'\b\d{5}(?:-\d{4})?\b' # Matches 12345 or 12345-6789
)

# --- NEW/IMPROVED PATTERNS --- #

# Basic URL Pattern (matches http, https, ftp, www.)
# Still relatively simple, might miss complex URLs or have false positives
URL_PATTERN = re.compile(
    r'\b(?:(?:https?|ftp):\/\/|www\.)[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)'
)

# Slightly Improved US Address Pattern (Still Heuristic)
# Separates components slightly better, allows for more street name variety
ADDRESS_PATTERN = re.compile(r"""
    \b
    \d+\s+                                    # Street number
    (?:[A-Z][a-zA-Z'.-]+\s+)+                   # Street name (1+ words, allowing ', ., -)
    (?:(?:Suite|Apt|Unit|Bldg|Floor)\.?\s+[\w-]+)? # Optional Apt/Suite/etc.
    ,?\s*                                     # Optional comma separator
    [A-Z][a-zA-Z.-]+(?:\s+[A-Z][a-zA-Z.-]+)*?,?\s* # City (1+ words, allows ., -), optional comma
    (?:AL|AK|AZ|AR|CA|CO|CT|DE|DC|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY)\s+ # State abbreviation (added DC)
    \d{5}(?:-\d{4})?                           # ZIP or ZIP+4
    \b
""", re.VERBOSE)

# ----------------------------- #

# Potentially add patterns for addresses, specific ID numbers (driver's license - very state dependent), etc.

PII_PATTERNS = {
    'EMAIL': EMAIL_PATTERN,
    'PHONE': PHONE_PATTERN,
    'SSN': SSN_PATTERN,
    'DATE_PATTERN': DATE_PATTERN, # Use a distinct name from spaCy's DATE
    'CREDIT_CARD': CREDIT_CARD_PATTERN,
    'ZIP_CODE': ZIP_CODE_PATTERN,
    'ADDRESS': ADDRESS_PATTERN,
    'URL': URL_PATTERN,           # Added URL
    # 'USERNAME': USERNAME_PATTERN, # Removed USERNAME due to poor performance/overlaps
} 