"""
sheets.py
---------
Google Sheets integration layer for the ZM Elite Bot Suite.

Provides a clean, reusable API for:
  - Authenticating with the Google Sheets API via a service account.
  - Opening spreadsheets by ID and ensuring a "Members" worksheet exists.
  - Looking up, adding, approving, and rejecting member records.

All public functions accept a `sheet_id` so the same module serves both
the Aviator and Chicken Road bots without duplication.

Column layout of the "Members" worksheet (1-indexed for gspread):
  1  Date Added
  2  Telegram ID
  3  Username
  4  First Name
  5  Member ID       ← submitted by the user during verification
  6  Status          ← Pending | Approved | Rejected
  7  Approved Date
"""

import json
from datetime import datetime

import gspread
from oauth2client.service_account import ServiceAccountCredentials

import config

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

WORKSHEET_NAME = "Members"

# Column positions — 0-indexed for Python list access
_C_DATE      = 0
_C_TG_ID     = 1
_C_USERNAME  = 2
_C_FIRSTNAME = 3
_C_MEMBER_ID = 4
_C_STATUS    = 5
_C_APPROVED  = 6

# gspread uses 1-indexed column numbers
_GCOL_STATUS   = _C_STATUS + 1    # 6
_GCOL_APPROVED = _C_APPROVED + 1  # 7

HEADERS = [
    "Date Added", "Telegram ID", "Username",
    "First Name", "Member ID", "Status", "Approved Date",
]

# Status constants
STATUS_APPROVED = "Approved"
STATUS_PENDING  = "Pending"
STATUS_REJECTED = "Rejected"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_gspread_client() -> gspread.Client:
    """
    Creates an authenticated gspread client.

    Prefers GOOGLE_CREDENTIALS_JSON (env var, used on Railway) so that
    the JSON key file does not need to be present on the host machine.
    Falls back to GOOGLE_CREDENTIALS_FILE for local development.

    Returns:
        gspread.Client: Authorised gspread client.
    """
    if config.GOOGLE_CREDENTIALS_JSON:
        creds_dict = json.loads(config.GOOGLE_CREDENTIALS_JSON)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, _SCOPE)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            config.GOOGLE_CREDENTIALS_FILE, _SCOPE
        )
    return gspread.authorize(creds)


def _get_members_sheet(sheet_id: str) -> gspread.Worksheet:
    """
    Opens (or creates) the "Members" worksheet within the given spreadsheet.

    Automatically writes the header row on first use so admins do not need
    to set up the sheet manually.

    Args:
        sheet_id (str): The Google Spreadsheet ID.

    Returns:
        gspread.Worksheet: The "Members" worksheet.
    """
    client = _get_gspread_client()
    spreadsheet = client.open_by_key(sheet_id)

    # Try to open existing worksheet; create it if missing
    try:
        ws = spreadsheet.worksheet(WORKSHEET_NAME)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=WORKSHEET_NAME, rows=1000, cols=len(HEADERS))
        ws.append_row(HEADERS)

    # Write headers if the sheet is completely empty
    if not ws.row_values(1):
        ws.append_row(HEADERS)

    return ws


def _find_user_row(ws: gspread.Worksheet, telegram_id: int):
    """
    Searches the Members worksheet for a user by their Telegram ID.

    Args:
        ws (gspread.Worksheet): The Members worksheet.
        telegram_id (int): The Telegram user ID to search for.

    Returns:
        tuple[int | None, list | None]:
            (1-based row index, row values list) if found,
            (None, None) if not found.
    """
    all_rows = ws.get_all_values()
    for idx, row in enumerate(all_rows):
        # Skip header row (index 0)
        if idx == 0:
            continue
        if len(row) > _C_TG_ID and str(row[_C_TG_ID]) == str(telegram_id):
            return idx + 1, row  # idx+1 because gspread rows are 1-indexed
    return None, None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_user_status(sheet_id: str, telegram_id: int) -> str | None:
    """
    Returns the current approval status for a Telegram user.

    Args:
        sheet_id (str): The Google Spreadsheet ID for this bot.
        telegram_id (int): The Telegram user ID.

    Returns:
        str | None:
            "Approved", "Pending", "Rejected", or None if the user
            is not registered in the sheet at all.
    """
    try:
        ws = _get_members_sheet(sheet_id)
        _, row = _find_user_row(ws, telegram_id)
        if row and len(row) > _C_STATUS:
            return row[_C_STATUS] or None
        return None
    except Exception as exc:
        print(f"[sheets] get_user_status error: {exc}")
        return None


def upsert_pending_user(
    sheet_id: str,
    telegram_id: int,
    username: str,
    first_name: str,
    member_id: str,
) -> None:
    """
    Inserts a new member row with "Pending" status, or updates an existing
    row (resetting status to Pending so re-verification is possible).

    Args:
        sheet_id (str): The Google Spreadsheet ID for this bot.
        telegram_id (int): The Telegram user ID.
        username (str): Telegram @username (or "No Username").
        first_name (str): User's first name from Telegram.
        member_id (str): The membership ID submitted by the user.
    """
    try:
        ws = _get_members_sheet(sheet_id)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row_data = [now, str(telegram_id), username, first_name, member_id, STATUS_PENDING, ""]

        row_idx, _ = _find_user_row(ws, telegram_id)
        if row_idx:
            # Update existing row in-place
            ws.update(f"A{row_idx}:G{row_idx}", [row_data])
        else:
            ws.append_row(row_data)
    except Exception as exc:
        print(f"[sheets] upsert_pending_user error: {exc}")


def approve_user(sheet_id: str, telegram_id: int) -> bool:
    """
    Sets a member's status to "Approved" and records the approval timestamp.

    Args:
        sheet_id (str): The Google Spreadsheet ID for this bot.
        telegram_id (int): The Telegram user ID to approve.

    Returns:
        bool: True on success, False if the user was not found or an error occurred.
    """
    try:
        ws = _get_members_sheet(sheet_id)
        row_idx, _ = _find_user_row(ws, telegram_id)
        if not row_idx:
            return False
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ws.update_cell(row_idx, _GCOL_STATUS, STATUS_APPROVED)
        ws.update_cell(row_idx, _GCOL_APPROVED, now)
        return True
    except Exception as exc:
        print(f"[sheets] approve_user error: {exc}")
        return False


def reject_user(sheet_id: str, telegram_id: int) -> bool:
    """
    Sets a member's status to "Rejected".

    Args:
        sheet_id (str): The Google Spreadsheet ID for this bot.
        telegram_id (int): The Telegram user ID to reject.

    Returns:
        bool: True on success, False if the user was not found or an error occurred.
    """
    try:
        ws = _get_members_sheet(sheet_id)
        row_idx, _ = _find_user_row(ws, telegram_id)
        if not row_idx:
            return False
        ws.update_cell(row_idx, _GCOL_STATUS, STATUS_REJECTED)
        ws.update_cell(row_idx, _GCOL_APPROVED, "")
        return True
    except Exception as exc:
        print(f"[sheets] reject_user error: {exc}")
        return False
