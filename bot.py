import os
import requests
from datetime import date
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters
)

# --- TOKEN (ENV) ---
TOKEN = os.getenv("BOT_TOKEN")

# --- Basit hafıza (RAM) ---
welcomed_users = set()      # gruba ilk girenler
daily_greet = {}            # {user_id: tarih}

# --- Dil algılama ---
def detect_language(text: str) -> str:
    tr_chars = "ğüşöçıİĞÜŞÖÇ"
    if any(c in text for c in tr_chars):
        return "tr"
    return "en"

# --- Çeviri (MyMemory - ücretsiz) ---
def translate(text: str, source: str, target: str) -> str:
    url = "https://api.mymemory.translated.net/get"
    params = {
        "q": text,
        "langpair": f"{source}|{target}"
    }
    r = requests.get(url, params=params, timeout=10)
    return r.json()["responseData"]["translatedText"]

# --- Yeni katılan karşılama ---
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        if user.id not in welcomed_users:
            welcomed_users.add(user.id)
            username = f"@{user.username}" if user.username else user.full_name

            msg = (
                f"⚔️ Yeni bir savaşçı geldi: {username} 👑\n\n"
                "Çeviri botu aktif 🌍\n"
                "Kuralları öğren, keyfine bak 😏\n\n"
                f"🔥 {username}\n\n"
                "Bugün etkinlikte ne vardı?\n"
                "Epik düştü mü? 👑"
            )

            await update.message.reply_text(msg)

# --- Günlük ilk mesaj selamı ---
async def daily_hello(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    today = date.today()

    if daily_greet.get(user.id) != today:
        daily_greet[user.id] = today
        await update.message.reply_text(
            f"👋 Selam {user.first_name}!\n"
            "Bugün klana girdin mi?\n"
            "Epik kestin mi? 😎"
        )

# --- Otomatik çeviri ---
async def auto_translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text

    # komutları çevirme
    if text.startswith("/"):
        return

    source = detect_language(text)
    target = "en" if source == "tr" else "tr"

    try:
        translated = translate(text, source, target)
        if translated.lower() != text.lower():
            await update.message.reply_text(
                f"🌍 {translated}"
            )
    except Exception:
        pass

# --- MAIN ---
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, daily_hello))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, auto_translate))

    app.run_polling()

if __name__ == "__main__":
    main()
