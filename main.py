from telegram import *
from telegram.constants import ParseMode
from telegram.ext import *
import requests
from datetime import *


BOT_TOKEN = "8729082010:AAERl8fn28B7uEKp8NWq5bw0DtsTMa6iwko"

API_WEATHER_KEY = "b4406ca484ba7dd95280a03c2125959b"

bot_name = "Бот"

keyboards = {"start": [["Погода 🌤️"], ["Калькулятор 📱"]],
             "calculator": [["Назад"]],
             "weather": [["Назад"]]
             }
markups = {"start": ReplyKeyboardMarkup(keyboards["start"], one_time_keyboard=False, resize_keyboard=True),
           "calculator": ReplyKeyboardMarkup(keyboards["calculator"], one_time_keyboard=False, resize_keyboard=True),
           "weather": ReplyKeyboardMarkup(keyboards["weather"], one_time_keyboard=False, resize_keyboard=True)
           }

icon_to_emoji = {
    '01d': '☀️',  # Ясно, день
    '01n': '🌙',  # Ясно, ночь
    '02d': '⛅',  # Малооблачно, день
    '02n': '☁️',  # Малооблачно, ночь
    '03d': '⛅️',  # Переменная облачность, день
    '03n': '⛅️',  # Переменная облачность, ночь
    '04d': '☁️',  # Облачно, день
    '04n': '☁️',  # Облачно, ночь
    '09d': '🌦',  # Дождь, день
    '09n': '🌧',  # Дождь, ночь
    '10d': '🌧',  # Дождь с грозой, день
    '10n': '🌩',  # Дождь с грозой, ночь
    '11d': '⛈',  # Гроза, день
    '11n': '⛈',  # Гроза, ночь
    '13d': '❄️',  # Снег, день
    '13n': '❄️',  # Снег, ночь
    '50d': '😶‍🌫️',  # Туман, день
    '50n': '😶‍🌫️'   # Туман, ночь
}

location = {"latitude": None, "longitude": None}

async def start(update, context):
    await update.message.reply_text(f"""
*Привет\\! Я {bot_name}\\.*
• Меня можно перезапустить командой /start
• Информацию об использовании можно получить командой /help
""",
parse_mode=ParseMode.MARKDOWN_V2)
    await main_menu_output(update, context)

async def main_menu_output(update, context):
    await update.message.reply_text(
f"""
❓ <b>Этот бот умеет:</b>
• Показывать <b>погоду</b> по местоположению 🌤️
• Выполнять функцию <b>калькулятора</b> 📱
""",
reply_markup=markups["start"],
parse_mode=ParseMode.HTML)

async def main_massage_handler(update, context):
    if update.message.text == "Калькулятор 📱":
        await update.message.reply_text("Введите пример:", reply_markup=markups["calculator"])
        return "calculator"
    elif update.message.text == "Погода 🌤️":
        await update.message.reply_text("Пришлите геолокацию:", reply_markup=markups["weather"])
        return "weather"
    else:
        await main_menu_output(update, context)


async def calculator(update, context):
    if update.message.text != "Назад":
        try:
            await update.message.reply_text(f"{update.message.text} = {eval(update.message.text.replace('÷', '/'))}", reply_markup=markups["calculator"])
        except:
            await update.message.reply_text("Неверный ввод", reply_markup=markups["calculator"])

        await update.message.reply_text("Введите пример:", reply_markup=markups["calculator"])
    else:
        await main_menu_output(update, context)
        return ConversationHandler.END

async def weather(update, context):
    if update.message.text != None:
        if update.message.text == "Назад":
            await main_menu_output(update, context)
            return ConversationHandler.END

    if update.message.location != None:

        wait_message = await update.message.reply_text("Получение данных...")


        latitude=update.message.location["latitude"]
        longitude=update.message.location["longitude"]

        URL = (
            f"https://api.openweathermap.org/data/2.5/weather?"
            f"lat={latitude}&lon={longitude}&"
            f"appid={API_WEATHER_KEY}&"
            f"units=metric&"
            f"lang=ru"
        )

        response = requests.get(URL)
        # print(f"Статус-код: {response.status_code}")  # для диагностики
        # print(response.json())
        try:
            file = open("logs.txt", "a+")
            file.write(f"{update.message.chat.username}, {update.message.location.latitude}, {update.message.location.longitude}, \
{datetime(year=update.message.date.year, month=update.message.date.month, day=update.message.date.day, hour=update.message.date.hour, minute=update.message.date.minute, second=update.message.date.second) + timedelta(hours=3)}\n")
            file.close()
        except:
            pass

        await context.bot.delete_message(chat_id=wait_message.chat.id, message_id=wait_message.message_id)

        if response.status_code == 200:
            data = response.json()
            await update.message.reply_text(
f"""
{icon_to_emoji[data['weather'][0]['icon']]} <b>{data['weather'][0]['description'].title()}</b>

🌡️ Температура <b>{round(data['main']['temp'])} °C</b>
🤔 Ощущается как <b>{round(data['main']['feels_like'])} °C</b>
💨 Скорость ветра <b>{round(data['wind']['speed'], 1)} м/с</b>
""",
reply_markup=markups["weather"], parse_mode=ParseMode.HTML)
            # "🎚 Давление <b>{round(data['main']['pressure'] * 0.75006)} мм рт. ст.</b>"
        else:
            await update.message.reply_text(f'{"Ошибка:"}, {response.text}')





    await update.message.reply_text("Пришлите геолокацию:", reply_markup=markups["weather"])


async def help(update, context):
    await update.message.reply_text("Я пока не умею помогать...")

async def stop(update, context):
    await update.message.reply_text("Всего доброго!")
    return ConversationHandler.END



conv_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, main_massage_handler)],

    states={
        "calculator": [MessageHandler(filters.TEXT & ~filters.COMMAND, calculator)],
        "weather": [MessageHandler((filters.LOCATION | filters.TEXT) & ~filters.COMMAND, weather)]
    },
    fallbacks=[CommandHandler('stop', stop)]
)



application = Application.builder().token(BOT_TOKEN).build()

application.add_handler(conv_handler)
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help))

application.run_polling()