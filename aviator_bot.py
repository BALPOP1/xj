"""
aviator_bot.py
--------------
All Telegram bot handlers for the ZM Elite | Aviator Predator AI bot.

All messages are formatted with Telegram HTML (parse_mode="HTML") and all
user-supplied strings are sanitised with html.escape() before embedding
them in any message. This prevents Telegram parse errors caused by
underscores, asterisks, or other special characters in user names or IDs.

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

import html
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

import config
import sheets
import signals

# ---------------------------------------------------------------------------
# Bot instance  (parse_mode="HTML" as default for send_message calls)
# ---------------------------------------------------------------------------
bot = telebot.TeleBot(config.AVIATOR_BOT_TOKEN, parse_mode="HTML")

_SHEET_ID  = config.AVIATOR_SHEET_ID
_GROUP_ID  = config.AVIATOR_GROUP_ID
_SHEET_URL = f"https://docs.google.com/spreadsheets/d/{_SHEET_ID}"

# Callback-data prefixes — must be unique across all bots
_CB_APPROVE  = "av_approve_"
_CB_REJECT   = "av_reject_"
_CB_REVERIFY = "av_reverify_"   # lets stuck users re-submit without admin help


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

    user   = message.from_user
    status = sheets.get_user_status(_SHEET_ID, user.id)
    # Always escape user-provided names to prevent HTML injection / parse errors
    name   = html.escape(user.first_name)

    if status == sheets.STATUS_APPROVED:
        text = (
            f"✈️ <b>Welcome back, {name}!</b>\n\n"
            "You are a <b>verified ZM Elite member</b> ✅\n\n"
            "📌 <b>Available Commands:</b>\n"
            "▸ /signal — Get your next Aviator prediction\n\n"
            "<i>Stay focused. Good luck on your next round!</i> 🎯"
        )
    elif status == sheets.STATUS_PENDING:
        text = (
            f"✈️ <b>Welcome, {name}!</b>\n\n"
            "Your verification request is <b>currently under review</b> ⏳\n"
            "Our team will approve your account shortly.\n\n"
            "<i>You'll receive a notification once you're approved.</i>"
        )
    elif status == sheets.STATUS_REJECTED:
        text = (
            f"✈️ <b>Welcome, {name}.</b>\n\n"
            "⚠️ Your previous verification was <b>not approved</b>.\n"
            "Please contact our support team for assistance."
        )
    else:
        text = (
            "✈️ <b>Welcome to ZM Elite | Aviator Predator AI!</b> 🛫\n\n"
            "Our AI engine predicts the next Aviator round multiplier "
            "with high precision.\n\n"
            "📌 <b>To get started:</b>\n"
            "▸ Use /signal to request access and verify your membership.\n\n"
            "<i>Verification is required for first-time users.</i>"
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
        # signals.generate_aviator_signal() already returns HTML-formatted text
        bot.send_message(message.chat.id, signals.generate_aviator_signal())

    elif status == sheets.STATUS_PENDING:
        # Offer a re-submit button in case the previous attempt got stuck mid-flow
        # (e.g. bot restarted before the photo reached the admin group)
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton(
                "🔄 Re-submit Verification",
                callback_data=f"{_CB_REVERIFY}{user.id}",
            )
        )
        bot.send_message(
            message.chat.id,
            "⏳ <b>Verification Pending</b>\n\n"
            "Your request is being reviewed by our team.\n"
            "You'll be notified once your account is approved.\n\n"
            "<i>Did your submission get interrupted? Tap the button below to re-submit.</i>",
            reply_markup=markup,
        )

    elif status == sheets.STATUS_REJECTED:
        # Allow rejected users to re-apply after contacting support
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton(
                "🔄 Re-submit Verification",
                callback_data=f"{_CB_REVERIFY}{user.id}",
            )
        )
        bot.send_message(
            message.chat.id,
            "❌ <b>Access Denied</b>\n\n"
            "Your previous verification was not approved.\n"
            "If you believe this is a mistake, you may re-submit below.",
            reply_markup=markup,
        )

    else:
        # User not in sheet → begin two-step verification
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
        f"📊 <b>Aviator Members Database:</b>\n"
        f"<a href=\"{_SHEET_URL}\">Open Spreadsheet</a>",
    )


# ---------------------------------------------------------------------------
# /myid  (debugging helper — works in any chat)
# ---------------------------------------------------------------------------

@bot.message_handler(commands=["myid"])
def handle_myid(message: telebot.types.Message) -> None:
    """
    Replies with the current chat ID and user ID.

    Use this in your admin group to find the correct GROUP_ID to set as
    the AVIATOR_GROUP_ID environment variable on Railway.

    Args:
        message (telebot.types.Message): Incoming /myid command.
    """
    bot.reply_to(
        message,
        f"🆔 <b>Chat ID:</b> <code>{message.chat.id}</code>\n"
        f"👤 <b>Your User ID:</b> <code>{message.from_user.id}</code>\n\n"
        f"<i>Set AVIATOR_GROUP_ID to the Chat ID above on Railway.</i>",
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
        "🔐 <b>Verification Required</b>\n\n"
        "To access Aviator signals, you must verify your ZM Elite membership.\n\n"
        "📋 <b>Step 1 of 2</b> — Please send your <b>Member ID</b> as a text message.",
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
    # Let users escape by typing a command
    if message.text and message.text.startswith("/"):
        bot.send_message(
            message.chat.id,
            "⚠️ Verification cancelled. Use /signal to start again.",
        )
        return

    if message.content_type != "text":
        prompt = bot.send_message(
            message.chat.id,
            "⚠️ Please send your <b>Member ID</b> as a <b>text message</b>.",
        )
        bot.register_next_step_handler(prompt, _receive_member_id)
        return

    member_id = message.text.strip()
    prompt = bot.send_message(
        message.chat.id,
        f"✅ Member ID received: <code>{html.escape(member_id)}</code>\n\n"
        "📸 <b>Step 2 of 2</b> — Now please send a <b>photo</b> of your membership "
        "proof or ID card.",
    )
    # Pass the member_id forward to the next handler step
    bot.register_next_step_handler(prompt, _receive_verification_photo, member_id)


def _receive_verification_photo(message: telebot.types.Message, member_id: str) -> None:
    """
    Final verification step: forwards the Member ID and photo to the admin
    group with ✅ Approve / ❌ Reject inline buttons, then notifies the user.

    Wrapped in a try/except so any API or Sheets error is logged clearly
    in Railway logs and the user receives an accurate error message rather
    than a false "Submitted!" confirmation.

    Args:
        message (telebot.types.Message): Message containing the verification photo.
        member_id (str): Member ID collected in the previous step.
    """
    # Let users escape by typing a command
    if message.text and message.text.startswith("/"):
        bot.send_message(
            message.chat.id,
            "⚠️ Verification cancelled. Use /signal to start again.",
        )
        return

    if message.content_type != "photo":
        prompt = bot.send_message(
            message.chat.id,
            "⚠️ Please send a <b>photo</b> (not a file) for verification.",
        )
        bot.register_next_step_handler(prompt, _receive_verification_photo, member_id)
        return

    user     = message.from_user
    username = f"@{user.username}" if user.username else "No Username"

    try:
        # Build the admin notification caption using HTML + escaped user content
        caption = (
            "🔔 <b>NEW VERIFICATION REQUEST</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 <b>Bot:</b> Aviator Predator AI\n"
            f"👤 <b>Name:</b> {html.escape(user.first_name)}\n"
            f"🆔 <b>Telegram ID:</b> <code>{user.id}</code>\n"
            f"👤 <b>Username:</b> {html.escape(username)}\n"
            f"📋 <b>Member ID:</b> <code>{html.escape(str(member_id))}</code>\n"
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

        # IMPORTANT: parse_mode must be explicit here — constructor default
        # does NOT apply to send_photo captions in pyTelegramBotAPI.
        # Send to group FIRST — only mark user as Pending in the sheet after
        # success so a failed send never leaves the user permanently stuck.
        bot.send_photo(
            _GROUP_ID,
            photo_file_id,
            caption=caption,
            reply_markup=markup,
            parse_mode="HTML",
        )

        # Photo reached the group — now persist the pending record in Google Sheets
        sheets.upsert_pending_user(
            _SHEET_ID, user.id, username, user.first_name, member_id
        )

        # Confirm to the user only after both the send and the sheet update succeed
        bot.send_message(
            message.chat.id,
            "📤 <b>Verification Submitted!</b>\n\n"
            "Your Member ID and photo have been forwarded to our team for review.\n"
            "You will receive a notification here once your account is approved. ⏳",
        )

    except Exception as exc:
        # Log the full error so it appears in Railway logs for debugging
        print(f"[Aviator] ERROR forwarding verification for user {user.id}: {exc}")
        bot.send_message(
            message.chat.id,
            "❌ <b>Something went wrong</b> while submitting your verification.\n\n"
            "Please tap <b>Re-submit Verification</b> from /signal to try again.\n"
            "If the problem persists, contact our support team.",
        )


# ---------------------------------------------------------------------------
# Admin callback: Approve / Reject
# ---------------------------------------------------------------------------

@bot.callback_query_handler(
    func=lambda call: call.data.startswith(_CB_APPROVE) or call.data.startswith(_CB_REJECT)
)
def handle_admin_callback(call: telebot.types.CallbackQuery) -> None:
    """
    Handles Approve / Reject button presses from the admin group.

    Updates the member's status in Google Sheets and notifies the user
    of the outcome via a private message.

    Args:
        call (telebot.types.CallbackQuery): Callback triggered by the inline button.
    """
    data       = call.data
    admin_name = html.escape(call.from_user.first_name)

    if data.startswith(_CB_APPROVE):
        target_id = int(data[len(_CB_APPROVE):])
        action    = "approve"
    else:
        target_id = int(data[len(_CB_REJECT):])
        action    = "reject"

    if action == "approve":
        success = sheets.approve_user(_SHEET_ID, target_id)
        if success:
            bot.answer_callback_query(call.id, "✅ User approved!")

            # Append approval note to the original caption in the group
            updated_caption = (
                call.message.caption +
                f"\n\n✅ <b>APPROVED</b> by {admin_name}"
            )
            # parse_mode must be explicit — constructor default does not apply here
            bot.edit_message_caption(
                caption=updated_caption,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML",
            )

            # Notify the user in private
            bot.send_message(
                target_id,
                "🎉 <b>Congratulations! Your Account is Approved!</b> ✅\n\n"
                "You are now a verified <b>ZM Elite</b> member.\n"
                "Use /signal to receive live Aviator predictions! ✈️",
            )
        else:
            bot.answer_callback_query(
                call.id, "⚠️ Could not update the sheet — user record not found."
            )

    else:  # reject
        success = sheets.reject_user(_SHEET_ID, target_id)
        if success:
            bot.answer_callback_query(call.id, "❌ User rejected.")

            updated_caption = (
                call.message.caption +
                f"\n\n❌ <b>REJECTED</b> by {admin_name}"
            )
            bot.edit_message_caption(
                caption=updated_caption,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML",
            )

            bot.send_message(
                target_id,
                "❌ <b>Verification Not Approved</b>\n\n"
                "Unfortunately, your verification request was rejected.\n"
                "Please contact our support team for further assistance.",
            )
        else:
            bot.answer_callback_query(
                call.id, "⚠️ Could not update the sheet — user record not found."
            )


# ---------------------------------------------------------------------------
# Callback: Re-submit verification (from Pending / Rejected inline button)
# ---------------------------------------------------------------------------

@bot.callback_query_handler(func=lambda call: call.data.startswith(_CB_REVERIFY))
def handle_reverify_callback(call: telebot.types.CallbackQuery) -> None:
    """
    Triggered when a Pending or Rejected user taps "Re-submit Verification".

    Removes the inline button from the previous message to prevent duplicate
    submissions, then restarts the two-step verification flow from step 1.

    Args:
        call (telebot.types.CallbackQuery): Callback from the inline button.
    """
    bot.answer_callback_query(call.id)

    # Remove the button so it cannot be tapped again
    try:
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=None,
        )
    except Exception:
        pass  # Non-critical — proceed even if the edit fails

    # Restart the verification flow from step 1
    _ask_for_member_id(call.message)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run() -> None:
    """
    Starts the Aviator bot with long-polling.

    Calls remove_webhook() first to clear any lingering webhook or competing
    polling session that would cause a 409 Conflict error.  skip_pending=True
    discards updates that queued up while the bot was offline.

    Intended to be called from main.py inside a daemon thread.
    """
    print("✅ [Aviator] ZM Elite | Aviator Predator AI is running...")
    print(f"   ➤ Forwarding verifications to GROUP_ID: {_GROUP_ID}")
    print("   ➤ Tip: send /myid inside your admin group to confirm the correct ID.")

    # Remove any existing webhook so polling can start without a 409 conflict
    bot.remove_webhook()

    bot.infinity_polling(
        timeout=30,
        long_polling_timeout=20,
        skip_pending=True,       # discard stale updates from while bot was offline
    )
