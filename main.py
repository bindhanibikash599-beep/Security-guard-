import os
import time
import telebot
import emoji
import random
from flask import Flask
from threading import Thread
from telebot import types
from datetime import datetime

# --- CONFIGURATION ---
BOT_TOKEN = os.environ.get('BOT_TOKEN')
MODERATOR = "@silkroadbikas" 
START_TIME = datetime.now()

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# --- DATABASES (Persistent in runtime) ---
network_db = {} 
purge_queue = [] 
flood_control = {}
active_groups = {} # {chat_id: {'link_block': True, 'gali_block': True, 'scam_alert': True, 'title': ''}}

# --- FILTER LISTS ---
BAD_WORDS = ["fuck", "bitch", "madarchod", "bhenchod", "mc", "bc", "chutiya", "gandu", "loda", "randi", "saala"] 
SCAM_KEYWORDS = ["scam", "fraud", "frod", "fake", "scamer", "scammed", "dhoka"]

BANNER = "🛡️ ------------------------------------ 🛡️\n      S I L K - G U A R D  v4.3     \n      [ MODE: ADMIN-TERMINAL ]         \n      [ STATUS: ACTIVE-SHADOW ]          \n🛡️ ------------------------------------ 🛡️"

SCAM_BANNER = """
🚨🚨🚨 <b>SCAM ALERT</b> 🚨🚨🚨
⚠️ <b>WARNING:</b> Possible Fraud Detected!
👤 <b>REPORTED BY:</b> {name}
📝 <b>MESSAGE:</b> <i>"{text}"</i>

🚫 <b>ADVICE:</b> Do not send money without Escrow.
🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨
"""

# --- UTILS ---

def is_admin(chat_id, user_id):
    try:
        if chat_id > 0: return True # Private chat is always "admin"
        admins = bot.get_chat_administrators(chat_id)
        return any(admin.user.id == user_id for admin in admins)
    except: return False

def get_promo_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("📱 JOIN CHANNEL", url="https://t.me/silkroad105")
    btn2 = types.InlineKeyboardButton("📺 SUBSCRIBE YOUTUBE", url="https://www.youtube.com/@silk_road402")
    btn3 = types.InlineKeyboardButton("📸 FOLLOW INSTAGRAM", url="https://www.instagram.com/arshux._")
    markup.add(btn1, btn2, btn3)
    return markup

# --- THREADS (PURGE & PROMO) ---

def auto_purge_loop():
    while True:
        now = time.time()
        for item in list(purge_queue):
            chat_id, msg_id, timestamp = item
            if now - timestamp > 3600:
                try: bot.delete_message(chat_id, msg_id)
                except: pass
                purge_queue.remove(item)
        time.sleep(30)

def automatic_promotion_thread():
    while True:
        time.sleep(1200) # 20 Minutes
        promo_text = "🔥 <b>SILK ROAD PROMOTION</b> 🔥\n🚀 <i>Join the ecosystem now!</i>"
        for chat_id in active_groups:
            try:
                msg = bot.send_message(chat_id, promo_text, parse_mode="HTML", reply_markup=get_promo_markup())
                purge_queue.append((chat_id, msg.message_id, time.time()))
            except: pass

# --- DM SETTINGS HANDLERS ---

@bot.message_handler(func=lambda m: m.chat.type == 'private', commands=['start', 'settings'])
def dm_start(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_add = types.InlineKeyboardButton("➕ ADD TO GROUP", url=f"https://t.me/{bot.get_me().username}?startgroup=true")
    btn_sets = types.InlineKeyboardButton("⚙️ MY GROUP SETTINGS", callback_data="list_groups")
    markup.add(btn_add, btn_sets)
    
    bot.send_message(message.chat.id, f"<code>{BANNER}</code>\n\nWelcome to the <b>Silk-Guard Admin Terminal</b>. Use the buttons below to manage your groups.", parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "list_groups")
def list_user_groups(call):
    markup = types.InlineKeyboardMarkup(row_width=1)
    found = False
    for chat_id, data in active_groups.items():
        if is_admin(chat_id, call.from_user.id):
            markup.add(types.InlineKeyboardButton(f"🏰 {data['title']}", callback_data=f"manage_{chat_id}"))
            found = True
    
    if not found:
        bot.answer_callback_query(call.id, "No active groups found where you are an admin.", show_alert=True)
    else:
        bot.edit_message_text("🛡️ <b>Select a group to manage:</b>", call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("manage_"))
def manage_group(call):
    chat_id = int(call.data.split("_")[1])
    data = active_groups[chat_id]
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    l_status = "✅ ON" if data['link_block'] else "❌ OFF"
    g_status = "✅ ON" if data['gali_block'] else "❌ OFF"
    s_status = "✅ ON" if data['scam_alert'] else "❌ OFF"
    
    markup.add(
        types.InlineKeyboardButton(f"Link Block: {l_status}", callback_data=f"toggle_link_{chat_id}"),
        types.InlineKeyboardButton(f"Gali Block: {g_status}", callback_data=f"toggle_gali_{chat_id}"),
        types.InlineKeyboardButton(f"Scam Alert: {s_status}", callback_data=f"toggle_scam_{chat_id}"),
        types.InlineKeyboardButton("⬅️ BACK", callback_data="list_groups")
    )
    
    bot.edit_message_text(f"🏰 <b>Managing: {data['title']}</b>\n\nAdjust the security protocols below:", call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("toggle_"))
def toggle_setting(call):
    _, feature, chat_id = call.data.split("_")
    chat_id = int(chat_id)
    
    if feature == "link": active_groups[chat_id]['link_block'] = not active_groups[chat_id]['link_block']
    if feature == "gali": active_groups[chat_id]['gali_block'] = not active_groups[chat_id]['gali_block']
    if feature == "scam": active_groups[chat_id]['scam_alert'] = not active_groups[chat_id]['scam_alert']
    
    bot.answer_callback_query(call.id, "Setting Updated!")
    manage_group(call)

# --- GROUP MONITORING ENGINE ---

@bot.message_handler(content_types=['new_chat_members'])
def on_join(message):
    for member in message.new_chat_members:
        if member.id == bot.get_me().id:
            active_groups[message.chat.id] = {'link_block': True, 'gali_block': True, 'scam_alert': True, 'title': message.chat.title}
            bot.send_message(message.chat.id, f"<code>{BANNER}</code>\n\n🟢 <b>SYSTEM_READY.</b> Admins can manage settings in my DM.", parse_mode="HTML")

@bot.message_handler(func=lambda m: m.chat.type in ['group', 'supergroup'], content_types=['text', 'photo', 'video', 'sticker', 'document'])
def group_engine(message):
    chat_id = message.chat.id
    if chat_id not in active_groups:
        active_groups[chat_id] = {'link_block': True, 'gali_block': True, 'scam_alert': True, 'title': message.chat.title}
    
    settings = active_groups[chat_id]
    uid = message.from_user.id
    text = message.text.lower() if message.text else ""

    if not is_admin(chat_id, uid):
        # 1. SCAM ALERT
        if settings['scam_alert'] and any(word in text for word in SCAM_KEYWORDS):
            msg = bot.send_message(chat_id, SCAM_BANNER.format(name=message.from_user.first_name, text=message.text), parse_mode="HTML")
            purge_queue.append((chat_id, msg.message_id, time.time()))

        # 2. GALI BLOCK
        if settings['gali_block'] and any(word in text for word in BAD_WORDS):
            try:
                bot.delete_message(chat_id, message.message_id)
                return
            except: pass

        # 3. LINK BLOCK
        if settings['link_block'] and message.entities and any(e.type in ['url', 'text_link'] for e in message.entities):
            try:
                bot.delete_message(chat_id, message.message_id)
                return
            except: pass

        # AUTO-PURGE
        purge_queue.append((chat_id, message.message_id, time.time()))

# --- SERVER ---
@app.route('/')
def home(): return "SILK-GUARD v4.3 Live"

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))

if __name__ == "__main__":
    Thread(target=auto_purge_loop, daemon=True).start()
    Thread(target=automatic_promotion_thread, daemon=True).start()
    Thread(target=run_flask).start()
    bot.infinity_polling()
