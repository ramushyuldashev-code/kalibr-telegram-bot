import logging
from datetime import datetime

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

TOKEN = "8626944757:AAEjOZzbSAeHs3rBkvJp8f_3WP-fJAQO_tU"

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    "kalibr-report-bot-d2831c1be293.json",
    scope
)

client = gspread.authorize(creds)
sheet = client.open("Изделний_23.01.2026").worksheet("Telegram bot")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

WORK_TYPES = [
    "Печат (1+1)",
    "Печат (4+4)",
    "Печат (Solna)",
    "Печат (STAR 30)",
    "Фальсовка",
    "Подбор",
    "Термаклей",
    "Термаклей (yordamchi)",
    "Резка",
    "Стреч",
    "Ломинация",
    "Швейка",
    "Форзас",
    "Биговка",
    "Обложка (solish)",
    "Обложка (buklash)",
]


def build_worktype_keyboard():
    keyboard = []
    row = []

    for work_type in WORK_TYPES:
        row.append(InlineKeyboardButton(work_type, callback_data=work_type))
        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)


def get_user_full_name(user) -> str:
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    full_name = f"{first_name} {last_name}".strip()

    if full_name:
        return full_name

    if user.username:
        return user.username

    return str(user.id)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Assalomu alaykum.\n\nKitob nomini yuboring."
    )


async def route_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("waiting_for_number"):
        await handle_number(update, context)
    else:
        await handle_book_name(update, context)


async def handle_book_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if not text:
        await update.message.reply_text("Iltimos, kitob nomini yuboring.")
        return

    context.user_data["book_name"] = text
    context.user_data["waiting_for_number"] = False

    await update.message.reply_text(
        "Ish turini tanlang:",
        reply_markup=build_worktype_keyboard()
    )


async def handle_work_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    work_type = query.data
    context.user_data["work_type"] = work_type
    context.user_data["waiting_for_number"] = True

    await query.message.reply_text("Raqamni kiriting:")


async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().replace(" ", "").replace(",", "")

    if not text.isdigit():
        await update.message.reply_text("Iltimos, faqat raqam kiriting.")
        return

    quantity = int(text)

    book_name = context.user_data.get("book_name")
    work_type = context.user_data.get("work_type")

    if not book_name or not work_type:
        context.user_data.clear()
        await update.message.reply_text(
            "Ma'lumotlar topilmadi. Qaytadan boshlang.\n\nKitob nomini yuboring."
        )
        return

    employee_name = get_user_full_name(update.effective_user)
    date_str = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    total_sum = quantity * 100

    row_data = [
        employee_name,  # Xodimlar
        date_str,       # Sana
        book_name,      # Kitobning nomi
        work_type,      # Ish turi
        quantity,       # Soni
        total_sum       # Summasi
    ]

    try:
        sheet.append_row(row_data)
        await update.message.reply_text("Rahmat")
        context.user_data.clear()

    except Exception as e:
        logging.exception("Google Sheetga yozishda xatolik: %s", e)
        await update.message.reply_text(
            "Ma'lumotni Google Sheetga yozishda xatolik bo‘ldi."
        )


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_work_type))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, route_text))

    print("Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":

    main()
