import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from datetime import date

TOKEN = "8471405463:AAFi2uwEaEfdMThXB3NtoD1aQlM8ZgYRo-g"

# ---- Basit hafıza (RAM) ----
welcomed_users = set()        # gruba ilk girenler
daily_greet = {}              # {user_id: tarih}

# ---- Çeviri (MyMemory - ücretsiz) ----
def detect_language(text):
    tr_chars = "çğıöşüÇĞİÖŞÜ"
    if any(c in text for c in tr_chars):
        return "tr"
    return "en"

def translate(text, source, target):
    url = "https://api.mymemory.translated.net/get"
    params = {
        "q": text,
        "langpair": f"{source}|{target}"
    }
    r = requests.get(url, params=params, timeout=10)
    return r.json()["responseData"]["translatedText"]

# ---- Yeni katılan karşılama ----
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        if user.id not in welcomed_users:
            welcomed_users.add(user.id)
            username = f"@{user.username}" if user.username else user.full_name

            await update.message.reply_text(
                f"⚔️ Yeni bir savaşçı geldi: {username} 👑\n\n"
                "Çeviri botu aktif\n"
                "Kuralları öğren, keyfine bak 😏"
            )

# ---- Mesaj yakalama ----
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text or update.message.from_user.is_bot:
        return

    user = update.message.from_user
    text = update.message.text
    today = date.today()

    # Günlük ilk mesaj kontrolü
    if daily_greet.get(user.id) != today:
        daily_greet[user.id] = today
        username = f"@{user.username}" if user.username else user.full_name

        await update.message.reply_text(
            f"🔥 {username}\n\n"
            "Bugün etkinlikte ne vardı?\n"
            "Epik düştü mü? 👑"
        )

    # Otomatik çeviri
    try:
        lang = detect_language(text)
        if lang == "en":
            translated = translate(text, "en", "tr")
        else:
            translated = translate(text, "tr", "en")

        await update.message.reply_text(translated)
    except:
        pass

# ---- Botu başlat ----
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("👑 Elit çeviri + karşılama botu çalışıyor")
app.run_polling()
