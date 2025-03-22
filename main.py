import os
from datetime import datetime, timedelta
from dateutil import parser 
#from apscheduler.schedulers.asyncio import AsyncIOScheduler
#from apscheduler.triggers.date import DateTrigger
from telegram import Update, Bot
#import asyncio
from telegram.ext import CommandHandler, Application, ContextTypes
from dotenv import load_dotenv


load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет. Тут ты можешь поставить себе напоминание. "
        "Используй /addtask [описание] [дата ДД.ММ.ГГ ЧЧ:ММ] чтобы добавить задачу.")

tasks = {}
task_id = 0
users_tz = {}

async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global task_id
    # try:
    user_id = update.effective_user.id
    user_tz = users_tz.get(user_id)
    if user_tz:
        task_str = update.message.text.split()
        date_str = task_str[-2].replace('/','.').replace('-','.')
        time_str = task_str[-1].replace('.',':')
        desc = " ".join(task_str[1:-2])
        if len(date_str.split('.')) == 2:
            date_str += f'.{str(datetime.now().year)}'
        usertime_p = parser.parse(f'{date_str} {time_str}', dayfirst=True)
        offset = int(users_tz[user_id])
        datetime_p = usertime_p - timedelta(hours=offset) - timedelta(hours=3)
        #По какому час поясу будет работать? Можно установить timezone=timezone('Europe/Moscow') в trigger. from pytz import timezone
        
        tasks.setdefault(user_id, {})[task_id] = { #Можно без вложенности
            'desc': desc,
            'datetime': usertime_p
        }
        
        context.job_queue.run_once(remind, 
            datetime_p, 
            chat_id=update.effective_message.chat_id, data=task_id, 
            user_id=user_id) 
        
        task_id += 1 # где ставим???
        await update.message.reply_text("Задача успешно добавлена.") 
    else:
        await update.message.reply_text("Давайте определим ваш часовой пояс. Введите /addtz Мск +-?")
    # except:
    #     await update.message.reply_text("Неверный формат. Пример: /addtask Сходить в магазин 20.07.25"
    #        "19:00")     


async def add_tz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    offset = update.message.text.split()[-1]
    users_tz[update.effective_user.id] = offset
    await update.message.reply_text("Запомнил ваш часовой пояс, можете добавить задачу.") 

async def remind(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    task = tasks[job.user_id][job.data]
    if task:
        await context.bot.send_message(chat_id=job.chat_id, text=f"Напоминание: {task['desc']}")
        del tasks[job.user_id][job.data]

async def my_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in tasks:
        all_tasks_str = ''
        for task_id, task_data in tasks[user_id].items():
            datetime_str = datetime.strftime(task_data['datetime'], "%d.%m.%Y %H:%M")
            all_tasks_str += f'{task_data['desc']} {datetime_str} ID[{task_id}]\n'

        await update.message.reply_text(f"Ваши задачи:\n{all_tasks_str}") 
    else:
        await update.message.reply_text("У вас нет запланированных задач.")   

async def del_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        task_id = int(update.message.text.split()[1])
        user_tasks = tasks[update.effective_user.id]
        if task_id in user_tasks:
            del user_tasks[task_id]
            await update.message.reply_text(f"Задача {task_id} удалена")
        else:
           await update.message.reply_text("Такой задачи нет")     
    except:
       await update.message.reply_text("Введите ID задачи") 

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addtask", add_task))
    app.add_handler(CommandHandler("addtz", add_tz))
    app.add_handler(CommandHandler("mytasks", my_tasks))
    app.add_handler(CommandHandler("deltask", del_task))

    app.run_polling()






