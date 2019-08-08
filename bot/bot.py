from telegram.ext import Updater, CommandHandler, ConversationHandler, RegexHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
import logging
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "task_manager_api.settings")
import django
django.setup()
from datetime import date, timedelta
from time import sleep
from django.contrib.auth.models import User
from django.conf import settings

from core.models import Task


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    filename="bot.log")
logger = logging.getLogger(__name__)


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


def task_deadline(bot, update):

    return GET_NOTIFICATION


def get_dates_list(task_id, days=5):
    current = date.today()
    keyboard = [[InlineKeyboardButton(str(current + timedelta(days=i)), callback_data=task_id)]
                for i in range(days+1)]
    keyboard.append([InlineKeyboardButton("other date", callback_data="other")])
    keyboard_markup = InlineKeyboardMarkup(keyboard)
    return keyboard_markup


def task_create(bot, update):
    username = update.message.from_user.username
    user, _ = User.objects.get_or_create(username=username)
    task_title = update.message.text
    task = Task.objects.create(reporter=user, title=task_title)
    update.message.reply_text("What is the deadline for this one?", reply_markup=get_dates_list(task.id))
    return GET_DEADLINE


GET_COMMAND, TASK_CREATE, GET_DEADLINE, GET_NOTIFICATION = range(4)


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
                    MessageHandler(Filters.text, task_create),
                ],
                GET_DEADLINE: [
                    CallbackQueryHandler(task_deadline)
                ]
            },
            fallbacks=[
                CommandHandler('help', help),
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
