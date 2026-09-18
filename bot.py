import telebot
import time
import json
import os

BOT_TOKEN = "8829584999:AAEU25zBkY3UOk9URgsZM0C7pOwWlfLLpoA"
ADMIN_ID = 6163706312

bot = telebot.TeleBot(BOT_TOKEN)

# فایل محصولات
if not os.path.exists("products.json"):
    with open("products.json", "w") as f:
        json.dump({}, f)

def load_products():
    with open("products.json", "r") as f:
        return json.load(f)

def save_products(data):
    with open("products.json", "w") as f:
        json.dump(data, f, indent=4)

waiting_for_receipt = {}
waiting_for_config = {}
admin_state = {}  # حالت ادمین برای افزودن یا حذف محصول


@bot.message_handler(commands=['start'])
def start(msg):
    chat_id = msg.chat.id
    bot.send_message(
        chat_id,
        "سلام 👋\nبه ربات فروش کانفیگ خوش اومدی.",
        reply_markup=main_menu()
    )


def main_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🛒 خرید کانفیگ")
    markup.row("📦 محصولات")
    markup.row("📞 پشتیبانی")
    return markup


# پنل ادمین
@bot.message_handler(commands=['admin'])
def admin_panel(msg):
    if msg.chat.id != ADMIN_ID:
        return

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("➕ افزودن محصول", callback_data="add_product"),
        telebot.types.InlineKeyboardButton("➖ حذف محصول", callback_data="del_product")
    )
    markup.add(
        telebot.types.InlineKeyboardButton("📦 لیست محصولات", callback_data="list_product")
    )

    bot.send_message(msg.chat.id, "پنل مدیریت:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def admin_buttons(call):
    chat_id = call.message.chat.id
    data = call.data

    # افزودن محصول
    if data == "add_product":
        admin_state[chat_id] = "add"
        bot.send_message(chat_id, "نام محصول و قیمت را وارد کن.\nمثال:\nVIP 300000")
        return

    # حذف محصول
    if data == "del_product":
        admin_state[chat_id] = "del"
        bot.send_message(chat_id, "نام محصولی که می‌خوای حذف کنی را وارد کن:")
        return

    # لیست محصولات
    if data == "list_product":
        products = load_products()
        if not products:
            bot.send_message(chat_id, "📦 هیچ محصولی ثبت نشده.")
            return

        text = "📦 لیست محصولات:\n\n"
        for name, price in products.items():
            text += f"🔹 {name}\n💰 {price}\n\n"

        bot.send_message(chat_id, text)
        return

    # خرید محصول
    if data.startswith("buy_"):
        name = data.split("_")[1]
        products = load_products()

        if name not in products:
            bot.send_message(chat_id, "❗ محصول یافت نشد.")
            return

        price = products[name]

        bot.send_message(
            chat_id,
            f"🔹 {name}\n💰 قیمت: {price}\n\n"
            "برای خرید، مبلغ را به کارت زیر واریز کن و رسید را ارسال کن:\n"
            "💳 6274 1211 8541 2365"
        )
        waiting_for_receipt[chat_id] = True
        return

    # تأیید رسید
    if data.startswith("ok_"):
        user_id = int(data.split("_")[1])
        bot.send_message(chat_id, f"رسید کاربر {user_id} تأیید شد ✔️\nکانفیگ را ارسال کن.")
        waiting_for_config[chat_id] = user_id
        bot.send_message(user_id, "✔️ رسید شما تأیید شد.\nمنتظر دریافت کانفیگ باشید.")
        return

    # رد رسید
    if data.startswith("no_"):
        user_id = int(data.split("_")[1])
        bot.send_message(user_id, "❌ رسید شما رد شد.")
        bot.send_message(chat_id, "رسید رد شد.")
        return


@bot.message_handler(func=lambda m: True)
def handle_message(msg):
    chat_id = msg.chat.id
    text = msg.text

    # حالت افزودن محصول
    if chat_id in admin_state and admin_state[chat_id] == "add":
        try:
            name, price = text.split(" ", 1)
            products = load_products()
            products[name] = price
            save_products(products)
            bot.send_message(chat_id, f"✔️ محصول '{name}' با قیمت {price} اضافه شد.")
        except:
            bot.send_message(chat_id, "❗ فرمت درست:\nنام قیمت\nمثال:\nVIP 300000")
        del admin_state[chat_id]
        return

    # حالت حذف محصول
    if chat_id in admin_state and admin_state[chat_id] == "del":
        products = load_products()
        if text in products:
            del products[text]
            save_products(products)
            bot.send_message(chat_id, f"🗑 محصول '{text}' حذف شد.")
        else:
            bot.send_message(chat_id, "❗ همچین محصولی وجود ندارد.")
        del admin_state[chat_id]
        return

    # خرید کانفیگ
    if text == "🛒 خرید کانفیگ":
        send_product_menu(chat_id)
        return

    # لیست محصولات
    if text == "📦 محصولات":
        send_product_list(chat_id)
        return

    # پشتیبانی
    if text == "📞 پشتیبانی":
        bot.send_message(chat_id, "آیدی پشتیبانی:\n@komil_pv")
        return

    # رسید مشتری
    if chat_id in waiting_for_receipt:
        bot.send_message(chat_id, "رسید دریافت شد ✔️")
        bot.send_message(
            ADMIN_ID,
            f"📥 رسید جدید از مشتری:\n\n👤 User ID: {chat_id}\n📨 متن رسید:\n{text}",
            reply_markup=receipt_buttons(chat_id)
        )
        del waiting_for_receipt[chat_id]
        return

    # ارسال کانفیگ توسط ادمین
    if chat_id in waiting_for_config:
        user_id = waiting_for_config[chat_id]
        bot.send_message(user_id, "کانفیگ شما آماده شد:\n\n" + text)
        bot.send_message(chat_id, "کانفیگ برای مشتری ارسال شد ✔️")
        del waiting_for_config[chat_id]
        return


def send_product_menu(chat_id):
    products = load_products()
    markup = telebot.types.InlineKeyboardMarkup()

    if not products:
        bot.send_message(chat_id, "هیچ محصولی ثبت نشده ❗")
        return

    for name, price in products.items():
        markup.add(
            telebot.types.InlineKeyboardButton(
                f"{name} | {price}",
                callback_data=f"buy_{name}"
            )
        )

    bot.send_message(chat_id, "یکی از محصولات زیر را انتخاب کن:", reply_markup=markup)


def send_product_list(chat_id):
    products = load_products()
    if not products:
        bot.send_message(chat_id, "📦 هیچ محصولی ثبت نشده.")
        return

    text = "📦 لیست محصولات:\n\n"
    for name, price in products.items():
        text += f"🔹 {name}\n💰 {price}\n\n"

    bot.send_message(chat_id, text)


def receipt_buttons(user_id):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("✔️ تأیید رسید", callback_data=f"ok_{user_id}"),
        telebot.types.InlineKeyboardButton("❌ رد کردن", callback_data=f"no_{user_id}")
    )
    return markup


while True:
    try:
        bot.polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        print("Error:", e)
        time.sleep(3)
