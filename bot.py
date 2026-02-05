import os
import logging

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
)

from deep_translator import GoogleTranslator

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

def env(name: str, default: str | None = None) -> str | None:
    v = os.getenv(name)
    return v if v is not None and v.strip() != "" else default

BOT_TOKEN = env("BOT_TOKEN")
TARGET_LANG = (env("TARGET_LANG", "tr") or "tr").lower()   # hedef dil: tr, en, de...
MAX_LEN = int(env("MAX_MESSAGE_LEN", "3500") or "3500")    # telegram sınırlarına takılmamak için

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN env variable is missing. Set BOT_TOKEN in your host panel.")

translator = GoogleTranslator(source="auto", target=TARGET_LANG)

def split_text(text: str, limit: int = 3500) -> list[str]:
    if len(text) <= limit:
        return [text]
    parts = []
    current = []
    current_len = 0
    for line in text.splitlines(True):
        if current_len + len(line) > limit:
            parts.append("".join(current))
            current = [line]
            current_len = len(line)
        else:
            current.append(line)
            current_len += len(line)
    if current:
        parts.append("".join(current))
    return parts

def should_ignore(text: str) -> bool:
    t = text.strip()
    if not t:
        return True
    # Komutları çevirme
    if t.startswith("/"):
        return True
    return False

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"Merhaba! Bana yazdığın mesajları otomatik olarak '{TARGET_LANG}' diline çeviririm.\n\n"
        "Ayarlar:\n"
        f"- TARGET_LANG={TARGET_LANG}\n"
        "Komutlar: /start /lang <kod> /help"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Kullanım:\n"
        "- Normal mesaj gönder → çeviririm\n"
        "- /lang en  (hedef dili değiştirir)\n\n"
        "Dil kodları örnek: tr, en, de, fr, es, ru, ar"
    )

async def lang_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global translator, TARGET_LANG
    if not context.args:
        await update.message.reply_text(f"Mevcut hedef dil: {TARGET_LANG}\nÖrn: /lang en")
        return

    code = context.args[0].strip().lower()
    if len(code) < 2 or len(code) > 8:
        await update.message.reply_text("Geçersiz dil kodu. Örn: /lang en")
        return

    TARGET_LANG = code
    translator = GoogleTranslator(source="auto", target=TARGET_LANG)
    await update.message.reply_text(f"Hedef dil güncellendi: {TARGET_LANG}")

async def translate_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    if not msg or msg.text is None:
        return

    text = msg.text
    if should_ignore(text):
        return

    try:
        translated = translator.translate(text)
        if not translated:
            return

        # Aynı çıktı geldiyse spam yapma
        if translated.strip() == text.strip():
            return

        for chunk in split_text(translated, MAX_LEN):
            await msg.reply_text(chunk)

    except Exception as e:
        logging.exception("Translation error: %s", e)
        await msg.reply_text("Çeviri sırasında hata oldu. Lütfen tekrar dene.")

def main() -> None:
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("lang", lang_cmd))

    # Sadece yazı mesajları
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate_message))

    app.run_polling(close_loop=False)

if __name__ == "__main__":
    main()
