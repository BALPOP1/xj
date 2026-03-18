import telebot
import gspread
import re
import os
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- CONFIGURATION ---
TOKEN = '8646851354:AAEQEIAEpWu_ezYnyfCpnr_JEhLYhffUCA8'
GROUP_ID = -1003714771655
# Pastikan nama file JSON di bawah ini sesuai dengan nama file yang Anda simpan
JSON_FILE = 'C:\\Users\\USER\\Desktop\\PAK\\PYTHON\\fluted-catalyst-490220-v7-d4ad8dc5425e.json'
# Ganti dengan NAMA Google Sheet Anda yang sudah di-share
SHEET_NAME = 'Database Chicken Road 2' 

bot = telebot.TeleBot(TOKEN)

# --- GOOGLE SHEETS SETUP ---
def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_FILE, scope)
    client = gspread.authorize(creds)
    # Membuka sheet pertama
    return client.open(SHEET_NAME).sheet1

def log_to_gsheet(message):
    try:
        sheet = get_sheet()
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        
        user_id = message.from_user.id
        username = f"@{message.from_user.username}" if message.from_user.username else "No Username"
        first_name = message.from_user.first_name
        text = message.text.replace('\n', ' ') if message.text else "N/A"

        # Kirim data ke Google Sheets
        sheet.append_row([date_str, time_str, user_id, username, first_name, text])
    except Exception as e:
        print(f"❌ Gagal update Google Sheet: {e}")

# --- COMMAND ADMIN: GET LINK ---
@bot.message_handler(commands=['getlog'])
def send_sheet_link(message):
    if message.chat.id == GROUP_ID:
        # Karena sudah online, kita cukup kirim link-nya saja
        link = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID_HERE"
        bot.reply_to(message, f"📊 *Data Log Real-time:*\n[Klik di Sini untuk Melihat]({link})", parse_mode='Markdown')

# 1. Pesan saat User klik Start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.type == 'private':
        log_to_gsheet(message)
        welcome_text = (
            "💰 *WELCOME TO CHICKEN ROAD 2* 🐓\n\n"
            "Can we help you? Send your message below, "
            "Our team of analysts will respond as soon as possible.")
        bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown')

# 2. Meneruskan Chat dari Client ke Grup Admin
@bot.message_handler(func=lambda message: message.chat.type == 'private')
def forward_to_group(message):
    log_to_gsheet(message)
    client_info = (
        f"📩 *NEW MESSAGE FROM CLIENT*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👤 Name: {message.from_user.first_name}\n"
        f"🆔 ID: `{message.chat.id}`\n"
        f"💬 Message: {message.text}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👉 *Reply to this message to respond to the client.*"
    )
    bot.send_message(GROUP_ID, client_info, parse_mode='Markdown')

# 3. Membalas dari Grup ke Client
@bot.message_handler(func=lambda message: message.chat.id == GROUP_ID)
def reply_from_group(message):
    if message.reply_to_message:
        try:
            text = message.reply_to_message.text
            match = re.search(r"ID: `?(\d+)`?", text)
            
            if match:
                client_id = match.group(1)
                response_text = f"👩‍💻 *Response from Analyst:*\n\n{message.text}"
                bot.send_message(client_id, response_text, parse_mode='Markdown')
                bot.reply_to(message, "✅ The message has been sent to the client.")
            else:
                bot.reply_to(message, "⚠️ Client ID not found.")
                
        except Exception as e:
            bot.reply_to(message, f"❌ Gagal mengirim: {e}")

print("✅ Chicken Road Bot (G-Sheets Version) is running...")
bot.infinity_polling()