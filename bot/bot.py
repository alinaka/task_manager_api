from telegram.ext import Updater, CommandHandler, ConversationHandler, RegexHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
import logging
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "task_manager_api.settings")
import django
django.setup()
from datetime import datetime
from time import sleep
from django.contrib.auth.models import User
from django.conf import settings
from bot import telegramcalendar

from core.models import Task


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    filename="bot.log")
logger = logging.getLogger(__name__)


def deadline_handler(bot,update, user_data):
    selected, date = telegramcalendar.process_calendar_selection(bot, update)

    task = user_data["task"]
    task.due_date = date
    task.save(update_fields=["due_date"])
    reply_keyboard = [['Yes', 'No']]
    bot.send_message(chat_id=update.callback_query.from_user.id,
                     text=f"You selected {date}. Do you want to get notification?",
                     reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return ADD_NOTIFICATION


def notification_handler(bot,update, user_data):
    selected, date = telegramcalendar.process_calendar_selection(bot, update)
    user_data.update(notification_date=date)
    bot.send_message(chat_id=update.callback_query.from_user.id,
                     text=f"You selected {date}. Enter notification time in format 'HH:MM'",
                     reply_markup=ReplyKeyboardRemove())
    return ADD_NOTIFICATION_TIME


def hello(bot, update):
    update.message.reply_text(
        'Hello {}'.format(update.message.from_user.first_name))


def get_username(update):
    return update.effective_user.username


def start(bot, update):
    reply_keyboard = [['Create Task', 'List All Tasks']]
    username = get_username(update)
    User.objects.get_or_create(username=username)
    update.message.reply_text("Hi! I'm your task manager."
                              "Send /cancel to stop talking to me."
                              "What would you like to do?",
                              reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return GET_COMMAND


def add_task(bot, update):
    reply_markup = ReplyKeyboardRemove()
    update.message.reply_text("Please send me a tasks's title", reply_markup=reply_markup)
    return TASK_CREATE


def get_tasks_list():
    tasks = Task.objects.all()
    keyboard = [[InlineKeyboardButton(task.title, callback_data=task.title)]
                for task in tasks]
    keyboard_markup = InlineKeyboardMarkup(keyboard)
    return keyboard_markup


def list_tasks(bot, update):
    reply_markup = ReplyKeyboardRemove()
    message = update.message.reply_text("Getting tasks list ...", reply_markup=reply_markup)
    message.reply_text("Choose a task to view:", reply_markup=get_tasks_list())
    return


def add_deadline(bot, update):
    update.message.reply_text("Please select a date: ",
                              reply_markup=telegramcalendar.create_calendar())
    return GET_DEADLINE


def task_create(bot, update, user_data):
    username = update.message.from_user.username
    user, _ = User.objects.get_or_create(username=username)
    task_title = update.message.text
    task = Task.objects.create(reporter=user, title=task_title)
    user_data.update(task=task)
    reply_keyboard = [['Yes', 'No']]
    update.message.reply_text("Does the task have the deadline?", reply_markup=ReplyKeyboardMarkup(
        reply_keyboard, one_time_keyboard=True))
    return ADD_DEADLINE


def cancel(bot, update):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.username)
    update.message.reply_text('Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def say_goodbye(bot, update, user_data):
    user_data.clear()
    update.message.reply_text('Thank you! I hope we can talk again some day.')
    return ConversationHandler.END


def add_notification(bot, update, user_data):
    update.message.reply_text("Please select a date: ",
                              reply_markup=telegramcalendar.create_calendar())
    return GET_NOTIFICATION


def alarm(bot, job):
    """Send the alarm message."""
    bot.send_message(job.context, text='Beep!')


def add_notification_date(bot, update, job_queue, user_data):
    notification_time = update.message.text
    notification_date = user_data["notification_date"]
    try:
        hour, minutes = map(int, notification_time.split(":"))
        notification = datetime(year=notification_date.year,
                                month=notification_date.month,
                                day=notification_date.day,
                                hour=hour,
                                minute=minutes)
    except ValueError:
        update.message.reply_text("Please enter a valid time in format 'HH:MM'")
        return None
    task = user_data["task"]
    task.notification = notification
    task.save(update_fields=["notification"])
    chat_id = update.message.chat_id
    job_queue.run_once(alarm, notification, context=chat_id)
    update.message.reply_text(
        f"Thanks! I'll send you a notification on your task on {notification:%A}, {notification}.")
    return ConversationHandler.END


def no_deadline(bot, update):
    reply_keyboard = [['Yes', 'No']]
    update.message.reply_text("Do you want to get notification?", reply_markup=ReplyKeyboardMarkup(
        reply_keyboard, one_time_keyboard=True))
    return ADD_NOTIFICATION


GET_COMMAND, TASK_CREATE, GET_DEADLINE, ADD_NOTIFICATION, ADD_DEADLINE, GET_NOTIFICATION, ADD_NOTIFICATION_TIME = range(7)


def launch_bot():
    updater = Updater(settings.TELEGRAM_BOT_TOKEN)

    conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler('start', start),
            ],
            states={
                GET_COMMAND: [
                    RegexHandler('^Create Task$', add_task),
                    RegexHandler('^List All Tasks$', list_tasks),
                ],
                TASK_CREATE: [
                    MessageHandler(Filters.text, task_create, pass_user_data=True),
                ],
                ADD_DEADLINE: [
                    RegexHandler('^Yes$', add_deadline),
                    RegexHandler('^No$', no_deadline),
                ],
                GET_DEADLINE: [
                    CallbackQueryHandler(deadline_handler, pass_user_data=True)
                ],
                ADD_NOTIFICATION: [
                    RegexHandler('^Yes$', add_notification, pass_user_data=True),
                    RegexHandler('^No$', say_goodbye, pass_user_data=True),
                ],
                GET_NOTIFICATION: [
                    CallbackQueryHandler(notification_handler, pass_user_data=True)
                ],
                ADD_NOTIFICATION_TIME: [
                    MessageHandler(Filters.text, add_notification_date, pass_user_data=True, pass_job_queue=True),
                ]
            },
            fallbacks=[
                CommandHandler('cancel', cancel),
            ],
            allow_reentry=True
        )

    updater.dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()
    logger.info("Started bot")


def bot_loop():
    while True:
        try:
            launch_bot()
        except Exception as e:
            logger.warning(e)
        logger.info("Bot has finished")
        sleep(5)


if __name__ == '__main__':
    launch_bot()
