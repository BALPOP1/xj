"""
config.py
---------
Central configuration for the ZM Elite Bot Suite.

All sensitive credentials are read from environment variables so the
application can run securely on Railway (or any cloud platform) without
embedding secrets in the source code.  For local development, values
fall back to the hardcoded defaults below.
"""

import os

# ---------------------------------------------------------------------------
# Bot tokens
# ---------------------------------------------------------------------------
AVIATOR_BOT_TOKEN = os.environ.get(
    'AVIATOR_BOT_TOKEN',
    '8702904944:AAHyqaQPy3YZpKeKH1wppuFFdWHWsrBeUyo'
)

CHICKEN_BOT_TOKEN = os.environ.get(
    'CHICKEN_BOT_TOKEN',
    '8646851354:AAEQEIAEpWu_ezYnyfCpnr_JEhLYhffUCA8'
)

# ---------------------------------------------------------------------------
# Google Spreadsheet IDs  (the long string in the sheet URL)
# ---------------------------------------------------------------------------
AVIATOR_SHEET_ID = os.environ.get(
    'AVIATOR_SHEET_ID',
    '1jvmYKRb7Iyw00GviMh9niBX4rdnPs6eqQ8ObUqzaMuU'
)

CHICKEN_SHEET_ID = os.environ.get(
    'CHICKEN_SHEET_ID',
    '1zQi7GmVp7jp28SptV0WC5L7JXgljiEhQULlQNYp5x5s'
)

# ---------------------------------------------------------------------------
# Telegram group IDs where verification requests are forwarded for admin review
# ---------------------------------------------------------------------------
AVIATOR_GROUP_ID = int(os.environ.get('AVIATOR_GROUP_ID', '-1003862525815'))
CHICKEN_GROUP_ID = int(os.environ.get('CHICKEN_GROUP_ID', '-1003714771655'))

# ---------------------------------------------------------------------------
# Google Service Account credentials
#
# Railway / production  → set GOOGLE_CREDENTIALS_JSON to the full JSON string
#   of your service account key file (paste the entire file content as one
#   environment variable).
#
# Local development     → leave GOOGLE_CREDENTIALS_JSON empty and place the
#   key file at the path specified by GOOGLE_CREDENTIALS_FILE.
# ---------------------------------------------------------------------------
GOOGLE_CREDENTIALS_JSON = os.environ.get('GOOGLE_CREDENTIALS_JSON', '')
GOOGLE_CREDENTIALS_FILE = os.environ.get(
    'GOOGLE_CREDENTIALS_FILE',
    'fluted-catalyst-490220-v7-d4ad8dc5425e.json'
)
