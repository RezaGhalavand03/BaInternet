from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# شناسه شما به عنوان ادمین (پشتیبان)
ADMIN_ID = 5433860934

# شماره کارت
CARD_NUMBER = "6037-9912-XXXX-XXXX"

# نگه‌داری سفارشات ساده
user_orders = {}

# لیست پلن‌ها
plans = {
    "plan1": {"title": "تک‌کاربره 30 گیگ", "price": "85,000 تومان"},
    "plan2": {"title": "تک‌کاربره 60 گیگ", "price": "120,000 تومان"},
    "plan3": {"title": "دوکاربره 60 گیگ", "price": "160,000 تومان"},
    "plan4": {"title": "دوکاربره 120 گیگ", "price": "220,000 تومان"},
}

# شروع ربات
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(plan["title"], callback_data=key)]
        for key, plan in plans.items()
    ]
    await update.message.reply_text("یکی از پلن‌ها رو انتخاب کن:", reply_markup=InlineKeyboardMarkup(keyboard))

# وقتی روی یک پلن کلیک می‌کنه
async def handle_plan_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    plan_id = query.data
    user_id = query.from_user.id
    user_orders[user_id] = {"plan": plan_id}
    plan = plans[plan_id]

    await query.message.reply_text(
        f"📦 پلن انتخابی: {plan['title']}\n💳 قیمت: {plan['price']}\n\nبرای ادامه، روی دکمه زیر بزن:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 تکمیل سفارش", callback_data="complete_order")]
        ])
    )

# مرحله دریافت شماره تماس
async def handle_complete_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    await query.message.reply_text("📱 لطفاً شماره تماس خود را وارد کنید:")

# گرفتن شماره تماس
async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in user_orders:
        return

    user_orders[user_id]["phone"] = update.message.text
    await update.message.reply_text(f"✅ شماره ثبت شد.\n\n💳 لطفاً مبلغ مربوطه را به شماره کارت زیر واریز کن:\n\n{CARD_NUMBER}\n\nسپس رسید واریز را ارسال کن.")

# رسید واریز
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in user_orders:
        return

    order = user_orders[user_id]
    plan = plans[order["plan"]]
    phone = order.get("phone", "وارد نشده")

    # اطلاع دادن به ادمین
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📥 سفارش جدید:\n👤 یوزر: {update.message.from_user.full_name}\n🆔 آیدی عددی: {user_id}\n📱 شماره: {phone}\n📦 پلن: {plan['title']}\n💳 قیمت: {plan['price']}"
    )

    await update.message.forward(ADMIN_ID)
    await update.message.reply_text("✅ رسید دریافت شد. در حال بررسی توسط پشتیبان...")

# ارسال کانفیگ به صورت پیام متنی توسط ادمین
async def send_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    try:
        user_id = int(context.args[0])
        config_text = " ".join(context.args[1:])
    except (IndexError, ValueError):
        await update.message.reply_text("فرمت دستور اشتباهه. مثال:\n/sendconfig 123456789 vmess://example-config-link")
        return

    if user_id not in user_orders:
        await update.message.reply_text("کاربر مورد نظر در لیست سفارشات یافت نشد.")
        return

    if not config_text:
        await update.message.reply_text("لطفاً کانفیگ را همراه دستور ارسال کنید.")
        return

    # ارسال پیام موفقیت به کاربر
    await context.bot.send_message(chat_id=user_id,
        text=f"✅ سفارش شما با موفقیت ثبت شد.\n\nکانفیگ شما:\n{config_text}"
    )

    await update.message.reply_text("✅ کانفیگ برای کاربر ارسال شد.")

    # حذف سفارش بعد از ارسال کانفیگ
    del user_orders[user_id]

# اجرای ربات
if __name__ == '__main__':
    app = ApplicationBuilder().token("7734854712:AAGmSQLoAb8UtwwWQWJ9TaMEbxW_8gcdlZM").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_plan_selection, pattern="^plan"))
    app.add_handler(CallbackQueryHandler(handle_complete_order, pattern="^complete_order$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CommandHandler("sendconfig", send_config))

    print("🤖 ربات فعال شد...")
    app.run_polling()