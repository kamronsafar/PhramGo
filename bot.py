import math
import sqlite3
import openai
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ParseMode, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from config import BOT_TOKEN, OPENAI_API_KEY 
from deep_translator import GoogleTranslator
from difflib import get_close_matches
import logging
from aiogram.contrib.fsm_storage.memory import MemoryStorage
storage = MemoryStorage()

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

logging.basicConfig(level=logging.INFO)
# OpenAI API kalitini o'rnating
openai.api_key = OPENAI_API_KEY
class Form(StatesGroup):
    diagnostic = State()
    drug_search = State()
    location = State()

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot, storage=storage)

def get_clinic_data():
    conn = sqlite3.connect('base.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, latitude, longitude, phone, address FROM clinics")
    clinics = cursor.fetchall()
    conn.close()
    return [{"name": row[0], "latitude": float(row[1]), "longitude": float(row[2]), "phone": row[3], "address": row[4]} for row in clinics]

# Aptekalar ma'lumotlarini olish
def get_pharmacy_data():
    conn = sqlite3.connect('base.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, latitude, longitude, phone ,address FROM pharmacy")
    pharmacies = cursor.fetchall()
    conn.close()
    return [{"name": row[0], "latitude": float(row[1]), "longitude": float(row[2]), "phone": row[3], "address": row[4]} for row in pharmacies]

# Masofani hisoblash
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Yerning radiusi, km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (math.sin(delta_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# Menu handler

menu_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
menu_keyboard.add(KeyboardButton("Geolokatsiyani yuborish", request_location=True))
menu_keyboard.add(KeyboardButton("Dorini qidirish"))
menu_keyboard.add(KeyboardButton("Diagnostika"))
menu_keyboard.add(KeyboardButton("favqulodda yordam"))


@dp.message_handler(commands=['start', 'menu', 'exit'])
async def menu(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Geolokatsiyani yuborish", request_location=True))
    keyboard.add(KeyboardButton("Dorini qidirish"))
    keyboard.add(KeyboardButton("Diagnostika"))
    keyboard.add(KeyboardButton("favqulodda yordam"))
    await message.answer("Quyidagi menyudan tanlang:", reply_markup=keyboard)

@dp.message_handler(lambda message: message.text.lower() == "favqulodda yordam")
async def emergency_help(message: types.Message):
    response = (
        "🚨 <b>Favqulodda yordam raqamlari:</b>\n"
        "📞 Tez yordam: 103\n"
        "📞 O't o'chirish: 101\n"
        "📞 Militsiya: 102\n\n"
        "⚠️ Shoshilinch dorilar kerak bo'lsa, dorilar ro'yxatini yuboring yoki aptekalarni qidirib ko'ring."
    )
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("favquotda yordam", request_location=True))
    keyboard.add(KeyboardButton("Bekor qilish"))
    await Form.location.set()
    await message.answer(response, parse_mode="HTML", reply_markup=keyboard)

# Geolokatsiya qabul qilish
@dp.message_handler(content_types=types.ContentType.LOCATION, state=Form.location)
async def handle_location(message: types.Message, state: FSMContext):
    if message.location:
        await message.answer("Favqulotda yordam tez orada sizga yetib boradi", parse_mode="HTML", reply_markup=menu_keyboard)
    else:
        await message.answer("Iltimos, geolokatsiyani yuboring.")
    await state.finish()
    
@dp.message_handler(text="Bekor qilish", state=Form.location)
async def discard_location(message: types.Message, state: FSMContext):
    text = "Favqulotda yordam chaqirish bekor qilindi"
    await message.answer(text, reply_markup=menu_keyboard)
    await state.finish()


# Foydalanuvchi geolokatsiyasini saqlash uchun lug'at
user_locations = {}
def search_drug_keyboard():
    exit_button = KeyboardButton("Exit")
    return ReplyKeyboardMarkup(resize_keyboard=True).add(exit_button)

# Geolokatsiya qabul qilish
@dp.message_handler(content_types=types.ContentType.LOCATION)
async def handle_location(message: types.Message):
    if message.location:
        user_lat, user_lon = message.location.latitude, message.location.longitude
        # Foydalanuvchining geolokatsiyasini saqlash
        user_locations[message.from_user.id] = (user_lat, user_lon)
        conn = sqlite3.connect('base.db')
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO user_data (user_name, latitude, longitude) VALUES (?, ?, ?)",
            (message.from_user.username, user_lat, user_lon),
        )
        conn.commit()
        conn.close()
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("Aptekalarni ko'rsatish", callback_data="show_pharmacies"))
        keyboard.add(InlineKeyboardButton("Klinikalarni ko'rsatish", callback_data="show_clinics"))
        await message.answer("Nimani qidirishni xohlaysiz?", reply_markup=keyboard)
    else:
        await message.answer("Iltimos, geolokatsiyani yuboring.")
 
@dp.callback_query_handler(lambda c: c.data == "show_pharmacies")
async def show_pharmacies(callback_query: types.CallbackQuery):
    user_lat, user_lon = user_locations.get(callback_query.from_user.id, (None, None))
    
    if user_lat is None or user_lon is None:
        # Foydalanuvchidan yana geolokatsiya yuborishni so'rash
        await callback_query.message.answer("Geolokatsiyani yuboring.")
        return

    pharmacies = get_pharmacy_data()
    nearby = [pharmacy for pharmacy in pharmacies if haversine(user_lat, user_lon, pharmacy['latitude'], pharmacy['longitude']) <= 1]
    if nearby:
        nearby.sort(key=lambda x: haversine(user_lat, user_lon, x['latitude'], x['longitude']))
        response = "\n\n".join(
            [f"<b>{i+1}. {pharmacy['name']}</b>\n📍 <a href='http://www.google.com/maps/place/{pharmacy['latitude']},{pharmacy['longitude']}'>Manzil</a>\n📏 {haversine(user_lat, user_lon, pharmacy['latitude'], pharmacy['longitude']):.2f} km \n☎ {pharmacy['phone']}"
             for i, pharmacy in enumerate(nearby)])
    else:
        response = "1 km radiusda aptekalar topilmadi. Radiusni kengaytirish uchun qayta urinib ko'ring."
    await bot.send_message(callback_query.from_user.id, response, parse_mode="HTML",  disable_web_page_preview=True)

@dp.callback_query_handler(lambda c: c.data == "show_clinics")
async def show_clinics(callback_query: types.CallbackQuery):
    user_lat, user_lon = user_locations.get(callback_query.from_user.id, (None, None))
    
    if user_lat is None or user_lon is None:
        # Foydalanuvchidan yana geolokatsiya yuborishni so'rash
        await callback_query.message.answer("Geolokatsiyani yuboring.")
        return

    clinics = get_clinic_data()
    nearby = [clinic for clinic in clinics if haversine(user_lat, user_lon, clinic['latitude'], clinic['longitude']) <= 2]
    if nearby:
        nearby.sort(key=lambda x: haversine(user_lat, user_lon, x['latitude'], x['longitude']))
        response = "\n\n".join(
            [f"<b>{i+1}. {clinic['name']}</b>\n📍 <a href='http://www.google.com/maps/place/{clinic['latitude']},{clinic['longitude']}'>Manzil</a>\n📏 {haversine(user_lat, user_lon, clinic['latitude'], clinic['longitude']):.2f} km \n📞 {clinic['phone']}"
             for i, clinic in enumerate(nearby)])
    else:
        response = "2 km radiusda klinikalar topilmadi. Radiusni kengaytirish uchun qayta urinib ko'ring."
    await bot.send_message(callback_query.from_user.id, response, parse_mode="HTML",  disable_web_page_preview=True)
# Diagnostic rejim bayrog'i
user_diagnostic_mode = set()  # Foydalanuvchi ID larini saqlash uchun

diagnostic_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
diagnostic_keyboard.add(KeyboardButton("exit"))


# Diagnostika rejimiga o'tish
@dp.message_handler(lambda message: message.text.lower() == "diagnostika")
async def ask_diagnostic(message: types.Message):
    user_diagnostic_mode.add(message.from_user.id)
    await message.answer(
        "🔍 Diagnostika rejimiga o'tdingiz. Muammo yoki kasallik alomatlarini kiriting:\n\n'Exit' tugmasi yordamida rejimdan chiqishingiz mumkin.",
        reply_markup=diagnostic_keyboard
    )

# Diagnostika rejimi ichida xabarlarni qayta ishlash
@dp.message_handler(lambda message: message.from_user.id in user_diagnostic_mode)
async def handle_diagnostic(message: types.Message):
    if message.text.lower() == "exit":
        user_diagnostic_mode.remove(message.from_user.id)
        await message.answer("👋 Diagnostika rejimidan chiqdingiz. Boshqa buyruqlar uchun asosiy rejimga qaytdingiz.", )
    else:
        try:
            # OpenAI API chaqiruvi
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": "Siz foydalanuvchilarga yordam beruvchi Telegram botisiz va ularning kasalligini aniqlab qaysi dorilar olishga yordamlashasiz kasalligini aniqlab aytshiz kerak"},
                          {"role": "user", "content": message.text}]
            )
            reply = response['choices'][0]['message']['content']
        except Exception as e:
            logging.error(f"OpenAI API xatosi: {e}")
            reply = "⚠️ Xato yuz berdi. Keyinroq urinib ko'ring."

        await message.reply(reply)


# Dorini qidirish
@dp.message_handler(lambda message: message.text.lower() == "dorini qidirish")
async def ask_drug_search(message: types.Message):
    await message.answer("Dori nomini kiriting:", reply_markup=search_drug_keyboard())

# O'xshash dorilarni qidirish
def get_similar_drugs(drug_name):
    conn = sqlite3.connect('base.db')
    cursor = conn.cursor()
    # Dorilar ro'yxatini bazadan olish
    cursor.execute("SELECT DISTINCT drug_name FROM drugs")
    dru = cursor.fetchall()
    if drug_name not in dru:
        drug_name = GoogleTranslator(source='ru', target='en').translate(drug_name)
    all_drugs = [row[0] for row in cursor.fetchall()]
    conn.close()

    # O'xshash dorilarni topish (masalan, bir xil nomlar yoki yaqin nomlar)
    similar = get_close_matches(drug_name, all_drugs, n=5, cutoff=0.6)  # Maksimal 5 ta o'xshash dori
    return similar

def get_drug_data(drug_name):
    conn = sqlite3.connect('base.db')
    curso2 = conn.cursor()
    curso2.execute("""SELECT drug_name FROM drugs""")
    dru = curso2.fetchall()
    if drug_name not in dru:
        drug_name = GoogleTranslator(source='ru', target='en').translate(drug_name)
    cursor = conn.cursor()
    cursor.execute("""SELECT d.drug_name, p.name, p.address, p.latitude, p.longitude 
                      FROM drugs d
                      JOIN pharmacy p ON d.pharmacy_id = p.id
                      WHERE LOWER(d.drug_name) LIKE ?""",
                   ('%' + drug_name.lower() + '%',))
    drugs = cursor.fetchall()
    conn.close()
    return [{"drug_name": row[0], "pharmacy_name": row[1], "pharmacy_address": row[2], "latitude": row[3], "longitude": row[4]} for row in drugs]

@dp.message_handler(lambda message: message.text.lower() == "exit")
async def exit_program(message: types.Message):
    # Foydalanuvchiga menyuni qaytarish
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Geolokatsiyani yuborish", request_location=True))
    keyboard.add(KeyboardButton("Dorini qidirish"))
    keyboard.add(KeyboardButton("Diagnostika"))
    keyboard.add(KeyboardButton("favqulodda yordam"))
    
    await message.answer("Siz bosh menyuga qaytdingiz. Iltimos, biror variantni tanlang:", reply_markup=keyboard)

@dp.message_handler(lambda message: message.text and not message.text.startswith('/'))
async def search_drug(message: types.Message):
    drug_name = message.text
    results = get_drug_data(drug_name)  # Asosiy qidiruv
    if results:
        response = "\n\n".join([ 
            f"<b>Dori:</b> {drug['drug_name']}\n"
            f"<b>Apteka:</b> {drug['pharmacy_name']}\n"
            f"🌍 <a href='http://www.google.com/maps/place/{drug['latitude']},{drug['longitude']}'>Manzil</a>"
            for drug in results
        ])
    else:
        # O‘xshash dorilarni topish
        similar_drugs = get_similar_drugs(drug_name)
        if similar_drugs:
            response = "Bu nomdagi dori topilmadi. Balki siz quyidagilarni qidirayotgandirsiz:\n"
            response += "\n".join([f"- {drug}" for drug in similar_drugs])
        else:
            response = "Bu nomdagi dori topilmadi va boshqa o‘xshash dorilar topilmadi."
    await message.answer(response, disable_web_page_preview=True)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)