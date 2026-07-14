from telebot import TeleBot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from telebot.handler_backends import State, StatesGroup
from telebot.custom_filters import StateFilter
from telebot.storage import StateMemoryStorage
from datetime import datetime

from database import db

storage = StateMemoryStorage()
bot = TeleBot('8803433177:AAErmrkAkfhrvDzNi1N7Q57ZzJQpCeHDG5Q', state_storage=storage)
bot.add_custom_filter(StateFilter(bot))

db.manager('''
CREATE TABLE IF NOT EXISTS requests (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT,
    client_name TEXT,
    phone TEXT,
    device TEXT,
    problem TEXT,
    created_at TEXT
)
''', commit=True)

class RequestStates(StatesGroup):
    client = State()
    contact = State()
    problem = State()
    confirm = State()

def get_main_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(KeyboardButton("🛠 Mening murojaatlarim"))
    return markup

def get_device_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    devices = ["🖥 Kompyuter", "📱 Telefon", "📺 Televizor", "❄️ Konditsioner"]
    for d in devices:
        markup.add(KeyboardButton(d))
    return markup

def get_confirm_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("✅ Tasdiqlash", callback_data="confirm_yes"),
        InlineKeyboardButton("❌ Bekor qilish", callback_data="confirm_no")
    )
    return markup

@bot.message_handler(commands=['start'])
def start(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    bot.send_message(chat_id, "Assalomu alaykum 👋\nTexnika ta'miri uchun usta chaqiramiz.\n\nIsmingizni kiriting 👇")
    bot.set_state(user_id, RequestStates.client, chat_id)

@bot.message_handler(state=RequestStates.client)
def handle_client_name(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if len(message.text) < 2:
        bot.send_message(chat_id, "Ism kamida 2 harfdan iborat bo'lishi kerak. Qaytadan kiriting:")
        return
    with bot.retrieve_data(user_id, chat_id) as data:
        data['name'] = message.text
    bot.send_message(chat_id, "Telefon raqamingizni kiriting 📞 (+998...)\n\nQaysi texnika nosoz? 🔧", reply_markup=get_device_keyboard())
    bot.set_state(user_id, RequestStates.contact, chat_id)

@bot.message_handler(state=RequestStates.contact)
def handle_contact(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    text = message.text
    with bot.retrieve_data(user_id, chat_id) as data:
        if text in ["🖥 Kompyuter", "📱 Telefon", "📺 Televizor", "❄️ Konditsioner"]:
            data['device'] = text
            bot.send_message(chat_id, "Muammoni qisqacha yozib qoldiring ✍️")
            bot.set_state(user_id, RequestStates.problem, chat_id)
        else:
            if not data.get('phone'):
                data['phone'] = text
                bot.send_message(chat_id, "Qaysi texnika nosoz? 🔧", reply_markup=get_device_keyboard())
            else:
                bot.send_message(chat_id, "Iltimos, texnika turini tanlang 👇", reply_markup=get_device_keyboard())

@bot.message_handler(state=RequestStates.problem)
def handle_problem(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    with bot.retrieve_data(user_id, chat_id) as data:
        data['problem'] = message.text
        text = f"📌 Usta chaqirish ma'lumotlari:\n\n"
        text += f"👤 Ism: {data.get('name')}\n"
        text += f"📞 Telefon: {data.get('phone')}\n"
        text += f"🔧 Texnika: {data.get('device')}\n"
        text += f"⚠️ Muammo: {data.get('problem')}"
        bot.send_message(chat_id, text, reply_markup=get_confirm_keyboard())
        bot.set_state(user_id, RequestStates.confirm, chat_id)

@bot.callback_query_handler(func=lambda call: True, state=RequestStates.confirm)
def handle_callback(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    with bot.retrieve_data(user_id, chat_id) as data:
        if call.data == "confirm_yes":
            db.manager('''
                INSERT INTO requests (telegram_id, client_name, phone, device, problem, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', user_id, data.get('name'), data.get('phone'), data.get('device'), data.get('problem'), datetime.now().strftime("%Y-%m-%d %H:%M"), commit=True)
            bot.send_message(chat_id, "✅ Murojaatingiz qabul qilindi\nUsta siz bilan bog'lanadi 🔧", reply_markup=get_main_keyboard())
        elif call.data == "confirm_no":
            bot.send_message(chat_id, "❌ Murojaat bekor qilindi", reply_markup=get_main_keyboard())
        bot.delete_state(user_id, chat_id)
        bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda m: m.text == "🛠 Mening murojaatlarim")
def my_requests(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    rows = db.manager(
        "SELECT id, device, problem, created_at FROM requests WHERE telegram_id = %s",
        user_id,
        fetchall=True
    )
    if not rows:
        bot.send_message(chat_id, "Sizda hali murojaat mavjud emas ❌")
        return
    text = "🛠 Sizning murojaatlaringiz:\n\n"
    for i, row in enumerate(rows, 1):
        text += f"{i}️⃣ {row[1]} — {row[2]}\n   📅 {row[3]}\n\n"
    bot.send_message(chat_id, text)

bot.infinity_polling()