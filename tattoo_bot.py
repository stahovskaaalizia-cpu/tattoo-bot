import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import anthropic

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY")

claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def get_tattoo_ideas(user_request: str):
    response = claude.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": f"""Клієнт хоче тату: {user_request}
            
Дай відповідь у форматі:
ОПИС: (2-3 речення про стиль і ідеї)
ПОШУК: (запит англійською для пошуку зображень, 3-5 слів)"""
        }]
    )
    
    text = response.content[0].text
    lines = text.split("\n")
    
    description = ""
    search_query = ""
    
    for line in lines:
        if line.startswith("ОПИС:"):
            description = line.replace("ОПИС:", "").strip()
        elif line.startswith("ПОШУК:"):
            search_query = line.replace("ПОШУК:", "").strip()
    
    return description, search_query

def search_images(query: str):
    url = "https://api.unsplash.com/search/photos"
    params = {
        "query": f"tattoo {query}",
        "per_page": 3,
        "client_id": UNSPLASH_ACCESS_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    photos = []
    for photo in data.get("results", []):
        photos.append(photo["urls"]["regular"])
    
    return photos

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привіт! Я допомагаю знаходити ідеї для тату.\n\n"
        "Напиши що саме ти хочеш, наприклад:\n"
        "• «хочу тату в стилі графіки»\n"
        "• «маленьке мінімалістичне тату на зап'ясток»\n"
        "• «японський стиль, тигр»"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await update.message.reply_text("🔍 Шукаю ідеї для тебе...")
    
    description, search_query = get_tattoo_ideas(user_text)
    images = search_images(search_query)
    
    await update.message.reply_text(f"✨ {description}\n\nОсь кілька варіантів:")
    
    for image_url in images:
        await update.message.reply_photo(photo=image_url)
    
    await update.message.reply_text(
        "💬 Якщо хочеш щось змінити — просто напиши!\n"
        "Наприклад: «більш детально», «менше деталей», «темніший стиль»"
    )

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Бот запущено!")
app.run_polling()
