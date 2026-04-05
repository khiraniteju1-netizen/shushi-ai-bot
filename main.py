import telebot
from telebot import types
import sqlite3
import datetime
import requests
import time
from flask import Flask
from threading import Thread

# --- RENDER PE BOT KO ZINDA RAKHNE KE LIYE WEB SERVER ---
app = Flask('')

@app.route('/')
def home():
    return "Shushi AI is Running Live!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- CONFIGURATION ---
API_TOKEN = '8679668152:AAEpAbyM_LhbOMsqRgcQdpJw_kpCnkMnwpQ'
ADMIN_ID = 8339811190
INSTA_API_KEY = 'ec56bead17ec0c19fbce60162398e71f'
INSTA_AUTH_TOKEN = '53f08f4abc54aab71aac9bee30152df7'
ELEVENLABS_KEY = 'sk_ced05ddbdec658b4f964962ee90787631a6e16682baa5545'
VOICE_ID = '21m0pSpHZps94fKNbcnm' 

bot = telebot.TeleBot(API_TOKEN)

# Aapki Media IDs
VOICE_DEMO_1 = 'CQACAgUAAxkBAAMCadDdvqiEHrIch7cSu1hMgB1ZNKUAArsdAAKf9IlWVYEDfQGQgvM7BA'
VOICE_DEMO_2 = 'CQACAgUAAxkBAAMDadDdyhTk8o5zag9uZGSnJ8aXjrQAArwdAAKf9IlWyx8DJAz-S147BA'
QR_30 = 'AgACAgUAAxkBAAMEadDd39cuX1OyBFAJUpLjt3N4fUoAAq4Oaxuf9IlWWtbv1akAAVSUAQADAgADeQADOwQ'
QR_150 = 'AgACAgUAAxkBAAMFadDd--nSZq61MqUKllvu1Y4c_JoAArEOaxuf9IlWtzGR3YpHzXYBAAMCAAN5AAM7BA'
QR_700 = 'AgACAgUAAxkBAAMGadDeEEXHbE5HmVpu-mDo5l9nQL0AArMOaxuf9IlWprNA-dcQZpcBAAMCAAN5AAM7BA'

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('shushi_pro_original.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, expiry TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS used_payments (payment_id TEXT PRIMARY KEY)')
    conn.commit()
    conn.close()

def verify_payment(payment_id):
    url = f"https://www.instamojo.com/api/1.1/payments/{payment_id}/"
    headers = {"X-Api-Key": INSTA_API_KEY, "X-Auth-Token": INSTA_AUTH_TOKEN}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()['success']
    except:
        return False
    return False

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ I Agree", callback_data="agree"))
    welcome_text = "🌟 **Welcome to Shushi AI Bot!**\n\nKya aap agree hain?"
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "agree":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔊 Yes, Check Demo", callback_data="send_demo"))
        bot.edit_message_text("Kya aap Demo check karna chahte hain?", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data == "send_demo":
        bot.send_voice(call.message.chat.id, VOICE_DEMO_1, caption="🌸 Demo 1")
        bot.send_voice(call.message.chat.id, VOICE_DEMO_2, caption="🌸 Demo 2")
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💎 Choose Plan", callback_data="show_plans"))
        bot.send_message(call.message.chat.id, "Ab apna plan select kijiye:", reply_markup=markup)

    elif call.data == "show_plans":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⚡ 1 Day - ₹30", callback_data="buy_30"))
        markup.add(types.InlineKeyboardButton("💎 1 Week - ₹150", callback_data="buy_150"))
        markup.add(types.InlineKeyboardButton("🔥 1 Month - ₹700", callback_data="buy_700"))
        bot.send_message(call.message.chat.id, "👑 **Premium Plans**", reply_markup=markup)

    elif call.data.startswith("buy_"):
        plan_price = call.data.split("_")[1]
        qr_map = {"30": QR_30, "150": QR_150, "700": QR_700}
        instr = f"✅ **₹{plan_price} Plan Selected.**\n\nPay karke Payment ID bhejein."
        bot.send_photo(call.message.chat.id, qr_map[plan_price], caption=instr, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text and len(m.text) >= 10)
def handle_payment(message):
    pay_id = message.text
    user_id = message.from_user.id
    conn = sqlite3.connect('shushi_pro_original.db')
    c = conn.cursor()
    c.execute("SELECT payment_id FROM used_payments WHERE payment_id=?", (pay_id,))
    if c.fetchone():
        bot.reply_to(message, "❌ Yeh ID use ho chuki hai!")
    else:
        if verify_payment(pay_id):
            expiry = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
            c.execute("INSERT OR REPLACE INTO users (user_id, expiry) VALUES (?, ?)", (user_id, expiry))
            c.execute("INSERT INTO used_payments (payment_id) VALUES (?)", (pay_id,))
            conn.commit()
            bot.send_message(ADMIN_ID, f"💰 **VERIFIED!** User: {user_id}")
            bot.reply_to(message, "🎉 **Plan Started!** Ab voice bhejein!")
        else:
            bot.reply_to(message, "❌ Payment ID galat hai!")
    conn.close()

@bot.message_handler(content_types=['voice'])
def voice_engine(message):
    user_id = message.from_user.id
    conn = sqlite3.connect('shushi_pro_original.db')
    c = conn.cursor()
    c.execute("SELECT expiry FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()

    if row and datetime.datetime.now() < datetime.datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S'):
        bot.reply_to(message, "🔄 **Converting...**")
        file_info = bot.get_file(message.voice.file_id)
        audio_data = bot.download_file(file_info.file_path)
        
        res = requests.post(
            f"https://api.elevenlabs.io/v1/speech-to-speech/{VOICE_ID}",
            headers={"xi-api-key": ELEVENLABS_KEY},
            files={"audio": ("voice.ogg", audio_data, "audio/ogg")}
        )
        if res.status_code == 200:
            bot.send_voice(message.chat.id, res.content, caption="✨ Result")
        else:
            bot.reply_to(message, "❌ Server Error.")
    else:
        bot.reply_to(message, "❌ Access Denied! Please pay first.")

if __name__ == "__main__":
    init_db()
    keep_alive()
    print("🚀 BOT LIVE!")
    bot.infinity_polling()
