"""
aviator_bot.py
--------------
All Telegram bot handlers for the ZM Elite | Aviator Predator AI bot.

Bot flow:
  /start  → checks membership status in Google Sheet and sends a tailored
             welcome message (different for Approved vs. first-time users).

  /signal → checks membership status:
              • Approved   → delivers a fresh Aviator signal immediately.
              • Pending    → informs the user that review is still ongoing.
              • Rejected   → informs the user that access was denied.
              • Unknown    → starts the two-step verification flow
                             (Member ID text → verification photo).

Verification flow:
  1. Bot prompts user to send their Member ID (plain text).
  2. Bot prompts user to send a verification photo.
  3. Both are forwarded to the admin group with ✅ Approve / ❌ Reject buttons.
  4. Admin clicks a button → sheet is updated → user is notified.

Admin group commands (in the group only):
  /getlog → posts a direct link to the Aviator Members spreadsheet.
"""

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

import config
import sheets
import signals

# ---------------------------------------------------------------------------
# Bot instance
# ---------------------------------------------------------------------------
bot = telebot.TeleBot(config.AVIATOR_BOT_TOKEN, parse_mode="Markdown")

_SHEET_ID  = config.AVIATOR_SHEET_ID
_GROUP_ID  = config.AVIATOR_GROUP_ID
_SHEET_URL = f"https://docs.google.com/spreadsheets/d/{_SHEET_ID}"

# Callback-data prefixes for inline buttons
_CB_APPROVE = "av_approve_"
_CB_REJECT  = "av_reject_"


# ---------------------------------------------------------------------------
# /start
# ---------------------------------------------------------------------------

@bot.message_handler(commands=["start"])
def handle_start(message: telebot.types.Message) -> None:
    """
    Sends a personalised welcome message based on the user's membership status.

    Approved users receive a full welcome with available commands.
    All other users receive a general welcome that guides them to /signal.

    Args:
        message (telebot.types.Message): Incoming /start command.
    """
    if message.chat.type != "private":
        return

    user      = message.from_user
    status    = sheets.get_user_status(_SHEET_ID, user.id)
    name      = user.first_name

    if status == sheets.STATUS_APPROVED:
        text = (
            f"✈️ *Welcome back, {name}!*\n\n"
            "You are a *verified ZM Elite member* ✅\n\n"
            "📌 *Available Commands:*\n"
            "▸ /signal — Get your next Aviator prediction\n\n"
            "_Stay focused. Good luck on your next round!_ 🎯"
        )
    elif status == sheets.STATUS_PENDING:
        text = (
            f"✈️ *Welcome, {name}!*\n\n"
            "Your verification request is *currently under review* ⏳\n"
            "Our team will approve your account shortly.\n\n"
            "_You'll receive a notification once you're approved._"
        )
    elif status == sheets.STATUS_REJECTED:
        text = (
            f"✈️ *Welcome, {name}.*\n\n"
            "⚠️ Your previous verification was *not approved*.\n"
            "Please contact our support team for assistance."
        )
    else:
        text = (
            f"✈️ *Welcome to ZM Elite | Aviator Predator AI!* 🛫\n\n"
            "Our AI engine predicts the next Aviator round multiplier "
            "with high precision.\n\n"
            "📌 *To get started:*\n"
            "▸ Use /signal to request access and verify your membership.\n\n"
            "_Verification is required for first-time users._"
        )

    bot.send_message(message.chat.id, text)


# ---------------------------------------------------------------------------
# /signal
# ---------------------------------------------------------------------------

@bot.message_handler(commands=["signal"])
def handle_signal(message: telebot.types.Message) -> None:
    """
    Delivers an Aviator signal to approved members, or initiates the
    verification flow for users who have not yet been approved.

    Args:
        message (telebot.types.Message): Incoming /signal command.
    """
    if message.chat.type != "private":
        return

    user   = message.from_user
    status = sheets.get_user_status(_SHEET_ID, user.id)

    if status == sheets.STATUS_APPROVED:
        # Deliver signal immediately
        bot.send_message(message.chat.id, signals.generate_aviator_signal())

    elif status == sheets.STATUS_PENDING:
        bot.send_message(
            message.chat.id,
            "⏳ *Verification Pending*\n\n"
            "Your request is still being reviewed by our team.\n"
            "You'll receive a notification once your account is approved. Please wait!",
        )

    elif status == sheets.STATUS_REJECTED:
        bot.send_message(
            message.chat.id,
            "❌ *Access Denied*\n\n"
            "Your verification was not approved.\n"
            "Please contact our support team for assistance.",
        )

    else:
        # User not in sheet → begin verification
        _ask_for_member_id(message)


# ---------------------------------------------------------------------------
# /getlog  (admin group only)
# ---------------------------------------------------------------------------

@bot.message_handler(commands=["getlog"])
def handle_getlog(message: telebot.types.Message) -> None:
    """
    Posts the direct Google Sheets link in the admin group.
    Only responds when the command is sent inside the admin group.

    Args:
        message (telebot.types.Message): Incoming /getlog command.
    """
    if message.chat.id != _GROUP_ID:
        return
    bot.reply_to(
        message,
        f"📊 *Aviator Members Database:*\n[Open Spreadsheet]({_SHEET_URL})",
    )


# ---------------------------------------------------------------------------
# Verification flow  (multi-step conversation)
# ---------------------------------------------------------------------------

def _ask_for_member_id(message: telebot.types.Message) -> None:
    """
    Step 1 of verification: prompts the user to send their Member ID.

    Args:
        message (telebot.types.Message): Trigger message (from /signal).
    """
    prompt = bot.send_message(
        message.chat.id,
        "🔐 *Verification Required*\n\n"
        "To access Aviator signals, you must verify your ZM Elite membership.\n\n"
        "📋 *Step 1 of 2* — Please send your *Member ID* as a text message.",
    )
    bot.register_next_step_handler(prompt, _receive_member_id)


def _receive_member_id(message: telebot.types.Message) -> None:
    """
    Step 2 of verification: stores the Member ID and asks for a photo.

    Loops back to step 1 if the user sends a non-text message.
    Cancels gracefully if the user issues a bot command instead.

    Args:
        message (telebot.types.Message): Message that should contain the Member ID text.
    """
    # Allow the user to restart with a command
    if message.text and message.text.startswith("/"):
        bot.send_message(
            message.chat.id,
            "⚠️ Verification cancelled. Use /signal to start again.",
        )
        return

    if message.content_type != "text":
        prompt = bot.send_message(
            message.chat.id,
            "⚠️ Please send your *Member ID* as a *text message*.",
        )
        bot.register_next_step_handler(prompt, _receive_member_id)
        return

    member_id = message.text.strip()
    prompt = bot.send_message(
        message.chat.id,
        f"✅ Member ID received: `{member_id}`\n\n"
        "📸 *Step 2 of 2* — Now please send a *photo* of your membership "
        "proof or ID card.",
    )
    # Pass the member_id forward to the next handler
    bot.register_next_step_handler(prompt, _receive_verification_photo, member_id)


def _receive_verification_photo(message: telebot.types.Message, member_id: str) -> None:
    """
    Final verification step: forwards the Member ID and photo to the admin
    group with Approve / Reject inline buttons, then notifies the user.

    Args:
        message (telebot.types.Message): Message containing the verification photo.
        member_id (str): Member ID collected in the previous step.
    """
    # Allow the user to restart with a command
    if message.text and message.text.startswith("/"):
        bot.send_message(
            message.chat.id,
            "⚠️ Verification cancelled. Use /signal to start again.",
        )
        return

    if message.content_type != "photo":
        prompt = bot.send_message(
            message.chat.id,
            "⚠️ Please send a *photo* (not a file) for verification.",
        )
        bot.register_next_step_handler(prompt, _receive_verification_photo, member_id)
        return

    user     = message.from_user
    username = f"@{user.username}" if user.username else "No Username"

    # Persist the pending record in the sheet
    sheets.upsert_pending_user(_SHEET_ID, user.id, username, user.first_name, member_id)

    # Build the admin notification with action buttons
    caption = (
        "🔔 *NEW VERIFICATION REQUEST*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 *Bot:* Aviator Predator AI\n"
        f"👤 *Name:* {user.first_name}\n"
        f"🆔 *Telegram ID:* `{user.id}`\n"
        f"👤 *Username:* {username}\n"
        f"📋 *Member ID:* `{member_id}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Please review the photo and take action:"
    )

    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("✅ Approve", callback_data=f"{_CB_APPROVE}{user.id}"),
        InlineKeyboardButton("❌ Reject",  callback_data=f"{_CB_REJECT}{user.id}"),
    )

    # Use the highest-resolution version of the photo
    photo_file_id = message.photo[-1].file_id
    bot.send_photo(_GROUP_ID, photo_file_id, caption=caption, reply_markup=markup)

    bot.send_message(
        message.chat.id,
        "📤 *Verification Submitted!*\n\n"
        "Your Member ID and photo have been forwarded to our team for review.\n"
        "You will receive a notification here once your account is approved. ⏳",
    )


# ---------------------------------------------------------------------------
# Admin callback: Approve / Reject
# ---------------------------------------------------------------------------

@bot.callback_query_handler(func=lambda call: call.data.startswith(_CB_APPROVE) or
                                               call.data.startswith(_CB_REJECT))
def handle_admin_callback(call: telebot.types.CallbackQuery) -> None:
    """
    Handles Approve / Reject button presses from the admin group.

    Updates the member's status in Google Sheets and notifies the user
    of the outcome via a private message.

    Args:
        call (telebot.types.CallbackQuery): Callback triggered by the inline button.
    """
    data          = call.data
    admin_name    = call.from_user.first_name

    if data.startswith(_CB_APPROVE):
        target_id  = int(data[len(_CB_APPROVE):])
        action     = "approve"
    else:
        target_id  = int(data[len(_CB_REJECT):])
        action     = "reject"

    if action == "approve":
        success = sheets.approve_user(_SHEET_ID, target_id)
        if success:
            bot.answer_callback_query(call.id, "✅ User approved!")
            # Update the group message caption to show who took action
            updated_caption = (
                call.message.caption +
                f"\n\n✅ *APPROVED* by {admin_name}"
            )
            bot.edit_message_caption(
                caption=updated_caption,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
            )
            # Notify the user
            bot.send_message(
                target_id,
                "🎉 *Congratulations! Your Account is Approved!* ✅\n\n"
                "You are now a verified *ZM Elite* member.\n"
                "Use /signal to receive live Aviator predictions! ✈️",
            )
        else:
            bot.answer_callback_query(call.id, "⚠️ Could not update the sheet — user may not exist.")

    else:  # reject
        success = sheets.reject_user(_SHEET_ID, target_id)
        if success:
            bot.answer_callback_query(call.id, "❌ User rejected.")
            updated_caption = (
                call.message.caption +
                f"\n\n❌ *REJECTED* by {admin_name}"
            )
            bot.edit_message_caption(
                caption=updated_caption,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
            )
            bot.send_message(
                target_id,
                "❌ *Verification Not Approved*\n\n"
                "Unfortunately, your verification request was rejected.\n"
                "Please contact our support team for further assistance.",
            )
        else:
            bot.answer_callback_query(call.id, "⚠️ Could not update the sheet — user may not exist.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run() -> None:
    """
    Starts the Aviator bot with long-polling.
    Intended to be called from main.py inside a daemon thread.
    """
    print("✅ [Aviator] ZM Elite | Aviator Predator AI is running...")
    bot.infinity_polling(timeout=30, long_polling_timeout=20)
