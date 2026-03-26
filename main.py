from telegram import *
from telegram.constants import ParseMode
from telegram.ext import *
import requests
from datetime import *
import json
import os
from warnings import *

filterwarnings(action="ignore", message=r".*CallbackQueryHandler") # убирает предупреждение, для удобства не удалять!

os.makedirs("users_data/tasks", exist_ok=True)

BOT_TOKEN = "8682452278:AAHi7CQC86R06CL3ZtqUVVF2sXfVtil5sEg"

markups = {
    "main_menu": InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Мои задачи", callback_data="my_tasks")],
        [InlineKeyboardButton("➕ Добавить задачу", callback_data="add_task")],
        [InlineKeyboardButton("⚙️ Настройки", callback_data="settings")]
    ]),
    "my_tasks": InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Активные", callback_data="active")],
        [InlineKeyboardButton("⏰ Просроченные", callback_data="overdue")],
        [InlineKeyboardButton("✔️ Выполненные", callback_data="complete")],
        [InlineKeyboardButton("🔙 Назад", callback_data="beck_main_menu_my_tasks")]
    ]),
    "add_task": InlineKeyboardMarkup([
        [InlineKeyboardButton("Отмена", callback_data="cancel_add_task")]
    ]),
    "add_task_name": InlineKeyboardMarkup([
        [InlineKeyboardButton("⏩ Пропустить", callback_data="skip_description_add_task")],
        [InlineKeyboardButton("Отмена", callback_data="cancel_add_task")]
    ]),
    "task_info": InlineKeyboardMarkup([
        [InlineKeyboardButton("✔️ Отметить выполненной", callback_data="delete_task")],
        [InlineKeyboardButton("❌ Удалить задачу", callback_data="delete_task")],
        [InlineKeyboardButton("🔙 Назад", callback_data="beck_main_menu_my_tasks")]
    ]),
    "back_main_menu_my_tasks": InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Назад", callback_data="beck_main_menu_my_tasks")]
    ]),
}

def create_user_data_file(update):
    try:
        file = open(f"users_data/tasks/{update.effective_user.id}_tasks.json", "r", encoding="utf-8")
        file.close()
    except FileNotFoundError:
        file = open(f"users_data/tasks/{update.effective_user.id}_tasks.json", "w+", encoding="utf-8")
        json.dump([], file, indent=4, ensure_ascii=False)
        file.close()

def task_from_file(user_id, task_id):
    file = open(f"users_data/tasks/{user_id}_tasks.json", "r", encoding="utf-8")
    data = json.load(file)
    file.close()
    this_task = None
    for task in data:
        if task["id"] == int(task_id):
            this_task = task
            break
    return this_task

def date_to_str(date):
    return date.strftime("%d-%m-%Y %H:%M")

def str_to_date(string):
    return datetime.strptime(string, "%d-%m-%Y %H:%M")

def update_status_user_data_file(id_user):
    all_tasks = []
    file = open(f"users_data/tasks/{id_user}_tasks.json", "r", encoding="utf-8")
    for task in json.load(file):
        if str_to_date(task["date"]) <= datetime.now() and task["status"] == "active":
            task["status"] = "overdue"
        all_tasks.append(task)
    file.close()
    file = open(f"users_data/tasks/{id_user}_tasks.json", "w+", encoding="utf-8")
    json.dump(all_tasks, file, indent=4, ensure_ascii=False)
    file.close()
    return all_tasks


async def create_main_menu(update, context):
    create_user_data_file(update)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="""
🏁 Главное меню

Что хотите сделать?
    """, reply_markup=markups["main_menu"])

async def main_menu(update, context):
    create_user_data_file(update)
    await update.callback_query.edit_message_text("""
🏁 Главное меню

Что хотите сделать?
""", reply_markup=markups["main_menu"])

    # return ConversationHandler.END


async def start(update, context):
    create_user_data_file(update)
    await update.message.reply_text("""
👋 Добро пожаловать в Планировщик задач!

Я помогу вам организовать время: создавать задачи, устанавливать дедлайны и получать напоминания.

Чтобы начать, воспользуйтесь меню ниже или введите команду /help для ознакомления со всеми возможностями.
""")
    await create_main_menu(update, context)

async def help(update, context):
    await update.message.reply_text("""
📖 Справка по использованию Планировщика задач

Я умею:
• создавать новые задачи с дедлайнами;
• показывать списки задач (активные, выполненные, просроченные);
• редактировать и удалять задачи;
• напоминать о приближении сроков (за 1 час и 15 минут);
• уведомлять о просроченных задачах.

📋 Основные команды:
/start — перезапустить бота
/help — показать эту справку

🔧 Доступные действия через меню:
• «Мои задачи» — просмотреть все задачи
• «Добавить задачу» — создать новую задачу
• «Настройки» — настроить уведомления и часовой пояс

Просто нажмите на нужную кнопку в меню или введите команду!
""")


async def add_task(update, context):
    global new_task
    new_task = {"id": None, "name": None, "description": None, "date": None, "status": None}
    await update.callback_query.edit_message_text("""
➕ Добавление новой задачи

Шаг 1/3:
Пожалуйста, введите название задачи:
""", reply_markup=markups["add_task"])
    return "name_add_task"

async def name_add_task(update, context):
    global new_task
    new_task["name"] = update.message.text
    await update.message.reply_text("""
Шаг 2/3:
📝 Введите описание задачи:
""", reply_markup=markups["add_task_name"])
    return "description_add_task"

async def description_add_task(update, context):
    global new_task
    new_task["description"] = update.message.text
    await update.message.reply_text("""
Шаг 3/3:
⏰ Введите дату и время дедлайна (ДД-ММ-ГГГГ ЧЧ:ММ):
""", reply_markup=markups["add_task"])
    return "date_add_task"

async def skip_description_add_task(update, context):
    global new_task
    new_task["description"] = None
    await context.bot.send_message(chat_id=update.effective_chat.id, text="""
Шаг 3/3:
⏰ Введите дату и время дедлайна (ДД-ММ-ГГГГ ЧЧ:ММ):
""", reply_markup=markups["add_task"])
    return "date_add_task"

async def date_add_task(update, context):
    try:
        create_user_data_file(update)

        new_task["date"] = date_to_str(str_to_date(update.message.text))

        if str_to_date(new_task["date"]) <= datetime.now():
            new_task["status"] = "overdue"
        else:
            new_task["status"] = "active"

        file = open(f"users_data/tasks/{update.effective_user.id}_tasks.json", "r", encoding="utf-8")
        all_tasks = json.load(file)
        file.close()

        all_ids = [i["id"] for i in all_tasks]

        for i in range((max(all_ids) if all_ids != [] else 0) + 2):
            if i not in all_ids:
                new_task["id"] = i
                break

        new_task["notification"] = True

        file = open(f"users_data/tasks/{update.effective_user.id}_tasks.json", "w+", encoding="utf-8")
        json.dump(all_tasks + [new_task], file, indent=4, ensure_ascii=False)
        file.close()

        if new_task["description"] is None:
            await update.message.reply_text(f"""
✅ <b>Задача добавлена!</b>

🏷️ <b>Название:</b> {new_task["name"]}
📝 <b>Описания нет</b>
⏰ <b>Дедлайн:</b> {new_task["date"]}

У задания есть напоминания за 1 час и за 15 минут(их можно отключить в настройках или а списке задач).
""", parse_mode=ParseMode.HTML)
        else:
            await update.message.reply_text(f"""
✅ <b>Задача добавлена!</b>

🏷️ <b>Название:</b> {new_task["name"]}
📝 <b>Описание:</b>
{new_task["description"]}
⏰ <b>Дедлайн:</b> {new_task["date"]}

У задания есть напоминания за 1 час и за 15 минут(их можно отключить в настройках или а списке задач).
""", parse_mode=ParseMode.HTML)

        await set_reminder_task(
            context=context,
            update=update,

            task_id=new_task["id"],
            delta_times=[
                timedelta(
                    seconds=10,
                ),
                timedelta(
                    seconds=20,
                )
            ]
        )

        await create_main_menu(update, context)
        return ConversationHandler.END

    except:
        await update.message.reply_text(f"""
❌ Неверный ввод
Верный формат: ДД-ММ-ГГГГ ЧЧ:ММ
Пример: {date_to_str(datetime.now())}
""")
        await update.message.reply_text("""
⏰ Введите дату и время дедлайна (ДД-ММ-ГГГГ ЧЧ:ММ):
""", reply_markup=markups["add_task"])

async def cancel_add_task(update, context):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="""
😢 Создание задачи отменено!
""")
    await create_main_menu(update, context)
    return ConversationHandler.END


async def my_tasks(update, context):
    create_user_data_file(update)
    await update.callback_query.edit_message_text("""
📋 Мои задачи

Выберите тип задач для просмотра:
""", reply_markup=markups["my_tasks"])
    return "choice_type_my_tasks"

async def choice_type_my_tasks(update, context):
    keyboards = []

    update_status_user_data_file(update.effective_user.id)
    file = open(f"users_data/tasks/{update.effective_user.id}_tasks.json", "r", encoding="utf-8")

    query = update.callback_query
    await query.answer()

    for task in json.load(file):
        if task["status"] == query.data:
            keyboards.append([InlineKeyboardButton(task["name"], callback_data=task["id"])])

    keyboards.append([InlineKeyboardButton("🔙 Назад", callback_data="beck_main_menu_my_tasks")])

    markup = InlineKeyboardMarkup(keyboards)

    if query.data == "active":
        word = "✅ Ваши активные"
    elif query.data == "complete":
        word = "✔️ Ваши выполненные"
    elif query.data == "overdue":
        word = "⏰ Ваши просроченные"


    if len(keyboards) == 1:
        await update.callback_query.edit_message_text(f"""
🔎 У вас нет задач этого вида
""", reply_markup=markup)
    else:
        await update.callback_query.edit_message_text(f"""
{word} задачи:
""", reply_markup=markup)

    return "choice_task_my_tasks"

async def choice_task_my_tasks(update, context):
    query = update.callback_query
    await query.answer()

    if query.data == "beck_main_menu_my_tasks":
        await main_menu(update, context)
        return ConversationHandler.END
    elif query.data.split("|", 1)[0] == "reminder_off":
        if task_from_file(update.effective_user.id, int(query.data.split("|", 1)[1]))["notification"]:
            jobs = context.job_queue.get_jobs_by_name(f"{update.effective_user.id}.{query.data.split('|', 1)[1]}")

            if not jobs:
                pass
            else:
                for job in jobs:
                    job.schedule_removal()

            await update.callback_query.edit_message_text(f"""
    🔇 Уведомления отключены!
    """, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="beck_main_menu_my_tasks")]]))

            file = open(f"users_data/tasks/{update.effective_user.id}_tasks.json", "r", encoding="utf-8")
            tasks = json.load(file)
            file.close()
            for i in range(len(tasks)):
                if tasks[i]["id"] == int(query.data.split("|", 1)[1]):
                    task = tasks[i]
                    number_task = i
                    break

            file = open(f"users_data/tasks/{update.effective_user.id}_tasks.json", "w", encoding="utf-8")
            tasks[number_task]["notification"] = False
            json.dump(tasks, file, indent=4, ensure_ascii=False)
        else:
            await set_reminder_task(
                context=context,
                update=update,
                task_id=query.data.split("|", 1)[1],
                delta_times=[
                    timedelta(
                        seconds=10,
                    ),
                    timedelta(
                        seconds=20,
                    )
                ]
            )

            file = open(f"users_data/tasks/{update.effective_user.id}_tasks.json", "r", encoding="utf-8")
            tasks = json.load(file)
            file.close()
            for i in range(len(tasks)):
                if tasks[i]["id"] == int(query.data.split("|", 1)[1]):
                    task = tasks[i]
                    number_task = i
                    break


            file = open(f"users_data/tasks/{update.effective_user.id}_tasks.json", "w", encoding="utf-8")
            tasks[number_task]["notification"] = True
            json.dump(tasks, file, indent=4, ensure_ascii=False)

            await update.callback_query.edit_message_text(f"""
🔊 Уведомления включены!
""", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="beck_main_menu_my_tasks")]]))

    elif query.data.split("|", 1)[0] == "delete_task":
        file = open(f"users_data/tasks/{update.effective_user.id}_tasks.json", "r", encoding="utf-8")
        tasks = json.load(file)
        file.close()
        for i in range(len(tasks)):
            if tasks[i]["id"] == int(query.data.split("|", 1)[1]):
                task = tasks[i]
                number_task = i
                break

        del tasks[number_task]

        file = open(f"users_data/tasks/{update.effective_user.id}_tasks.json", "w", encoding="utf-8")
        json.dump(tasks, file, indent=4, ensure_ascii=False)
        file.close()

        if task["description"] is None:
            await update.callback_query.edit_message_text(f"""
<b>❌ Задача удалена!</b>

🏷️ <b>Название:</b> {task["name"]}
📝 <b>Описания нет</b>
⏰ <b>Дедлайн:</b> {task["date"]}
""", parse_mode=ParseMode.HTML, reply_markup=markups["back_main_menu_my_tasks"])
        else:
            await update.callback_query.edit_message_text(f"""
<b>❌ Задача удалена!</b>

🏷️ <b>Название:</b> {task["name"]}
📝 <b>Описание:</b>
{task["description"]}
⏰ <b>Дедлайн:</b> {task["date"]}
""", parse_mode=ParseMode.HTML, reply_markup=markups["back_main_menu_my_tasks"])
    elif query.data.split("|", 1)[0] == "complete_task":
        file = open(f"users_data/tasks/{update.effective_user.id}_tasks.json", "r", encoding="utf-8")
        tasks = json.load(file)
        file.close()
        for i in range(len(tasks)):
            if tasks[i]["id"] == int(query.data.split("|", 1)[1]):
                task = tasks[i]
                number_task = i
                break

        tasks[number_task]["status"] = "complete"

        file = open(f"users_data/tasks/{update.effective_user.id}_tasks.json", "w", encoding="utf-8")
        json.dump(tasks, file, indent=4, ensure_ascii=False)
        file.close()

        if task["description"] is None:
            await update.callback_query.edit_message_text(f"""
<b>✔️ Задача выполнена!</b>

🏷️ <b>Название:</b> {task["name"]}
📝 <b>Описания нет</b>
⏰ <b>Дедлайн:</b> {task["date"]}
""", parse_mode=ParseMode.HTML, reply_markup=markups["beck_main_menu_my_tasks"])
        else:
            await update.callback_query.edit_message_text(f"""
<b>✔️ Задача выполнена!</b>

🏷️ <b>Название:</b> {task["name"]}
📝 <b>Описание:</b>
{task["description"]}
⏰ <b>Дедлайн:</b> {task["date"]}
""", parse_mode=ParseMode.HTML, reply_markup=markups["back_main_menu_my_tasks"])

    else:
        file = open(f"users_data/tasks/{update.effective_user.id}_tasks.json", "r", encoding="utf-8")
        tasks = json.load(file)
        file.close()
        for i in tasks:
            if i["id"] == int(query.data):
                task = i
                break

        if task["status"] == "active":
            word = "✅ Ваша активная задача"
        elif task["status"] == "complete":
            word = "✔️ Ваша выполненная задача"
        elif task["status"] == "overdue":
            word = "⏰ Ваша просроченная задача"

        if task_from_file(update.effective_user.id, int(task["id"]))["notification"]:
            reminder_name = "🔇 Отключить уведомления"
        else:
            reminder_name = "🔊 Включить уведомления"


        if task["status"] == "complete":
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Удалить задачу", callback_data=f"delete_task|{task['id']}")],
                [InlineKeyboardButton(reminder_name, callback_data=f"reminder_off|{task['id']}")],
                [InlineKeyboardButton("🔙 Назад", callback_data="beck_main_menu_my_tasks")]
            ])
        else:
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("✔️ Отметить выполненной", callback_data=f"complete_task|{task['id']}")],
                [InlineKeyboardButton("❌ Удалить задачу", callback_data=f"delete_task|{task['id']}")],
                [InlineKeyboardButton(reminder_name, callback_data=f"reminder_off|{task['id']}")],
                [InlineKeyboardButton("🔙 Назад", callback_data="beck_main_menu_my_tasks")]
            ])

        if task["description"] is None:
            await update.callback_query.edit_message_text(f"""
<b>{word}</b>

🏷️ <b>Название:</b> {task["name"]}
📝 <b>Описания нет</b>
⏰ <b>Дедлайн:</b> {task["date"]}
""", parse_mode=ParseMode.HTML, reply_markup=markup)
        else:
            await update.callback_query.edit_message_text(f"""
<b>{word}</b>

🏷️ <b>Название:</b> {task["name"]}
📝 <b>Описание:</b>
{task["description"]}
⏰ <b>Дедлайн:</b> {task["date"]}
""", parse_mode=ParseMode.HTML, reply_markup=markup)

async def beck_main_menu_my_tasks(update, context):
    await main_menu(update, context)
    return ConversationHandler.END


async def send_reminder(context):
    task = task_from_file(context.job.data["user_id"], context.job.data["task_id"])
    if task["status"] != "complete":
        if context.job.data["status"] == "active":
            if context.job.data["time"].total_seconds() == 0:
                await context.bot.send_message(chat_id=context.job.chat_id, text=f'''
<b>⏰ Дедлайн на задачу \"{task["name"]}\" вышел!</b>

С этого момента она считается просроченной.
Вы можете отметить её выполненной или удалить, иначе вы будете получать уведомления о просроченном задании.
''', parse_mode=ParseMode.HTML)
            else:
                await context.bot.send_message(chat_id=context.job.chat_id, text=f'''
<b>⏰ До дедлайна осталось {context.job.data["time"].days} дней, {context.job.data['time'].seconds // 3600} час(ов), {context.job.data['time'].seconds // 60 % 60} минут(ы)!</b>

Если задача уже выполнена, её можно отметить выполненной.
''', parse_mode=ParseMode.HTML)
        elif context.job.data["status"] == "overdue":
            await context.bot.send_message(chat_id=context.job.chat_id, text=f"Это просроченное задание {task['name']}")


async def set_reminder_task(context, update, task_id, delta_times):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    time = str_to_date(task_from_file(user_id, task_id)["date"])
    now_time = datetime.now()

    if task_from_file(user_id, task_id)["status"] == "complete":
        return 0



    for i in range(len(delta_times)):
        when_time = int(((time - delta_times[i]) - now_time).total_seconds())

        if when_time >= 0:
            context.job_queue.run_once(
                callback=send_reminder,
                name=f"{user_id}.{task_id}.{i}",
                chat_id=chat_id,
                when=when_time,
                data={
                    "task_id": task_id,
                    "user_id": user_id,
                    "time": delta_times[i],
                    "status": "active",
                },
        )


conv_add_task_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(add_task, pattern="add_task")],
    states={
        "name_add_task": [MessageHandler(filters.TEXT & ~filters.COMMAND, name_add_task)],
        "description_add_task": [
            MessageHandler(filters.TEXT & ~filters.COMMAND, description_add_task),
            CallbackQueryHandler(skip_description_add_task, pattern="skip_description_add_task")
        ],
        "date_add_task": [MessageHandler(filters.TEXT & ~filters.COMMAND, date_add_task)]
    },
    fallbacks=[CallbackQueryHandler(cancel_add_task, pattern="cancel_add_task")]
)


conv_my_tasks_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(my_tasks, pattern="my_tasks")],
    states={"choice_type_my_tasks": [CallbackQueryHandler(beck_main_menu_my_tasks, pattern="beck_main_menu_my_tasks"), CallbackQueryHandler(choice_type_my_tasks)],
            "choice_task_my_tasks": [CallbackQueryHandler(choice_task_my_tasks)]
            },
    fallbacks=[CallbackQueryHandler(beck_main_menu_my_tasks, pattern="beck_main_menu_my_tasks")]
)


application = Application.builder().token(BOT_TOKEN).build()

application.add_handler(CommandHandler('start', start))
application.add_handler(CommandHandler('help', help))


application.add_handler(conv_add_task_handler)
application.add_handler(conv_my_tasks_handler)

application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, create_main_menu))

application.add_handler(CallbackQueryHandler(main_menu, pattern="main_menu"))
