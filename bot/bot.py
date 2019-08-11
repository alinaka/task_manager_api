import logging
import pickle
from datetime import datetime, timedelta
from time import sleep, time
from threading import Event

from django.conf import settings
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (CallbackQueryHandler, CommandHandler,
                          ConversationHandler, Filters, MessageHandler,
                          RegexHandler, Updater)

from bot import telegramcalendar
from core.models import Task
from user.models import User

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="bot.log"
)
logger = logging.getLogger(__name__)


def deadline_handler(bot, update, user_data):
    selected, date = telegramcalendar.process_calendar_selection(bot, update)

    task = user_data["task"]
    task.due_date = date
    task.save(update_fields=["due_date"])
    reply_keyboard = [["Yes", "No"]]
    bot.send_message(chat_id=update.callback_query.from_user.id,
                     text=f"""You selected {date}.
                     Do you want to get notification?""",
                     reply_markup=ReplyKeyboardMarkup(
                         reply_keyboard,
                         one_time_keyboard=True)
                     )
    return ADD_NOTIFICATION


def notification_handler(bot, update, user_data):
    selected, date = telegramcalendar.process_calendar_selection(bot, update)
    user_data.update(notification_date=date)
    bot.send_message(chat_id=update.callback_query.from_user.id,
                     text=f"""You selected {date}.
                     Enter notification time in format 'HH:MM'""",
                     reply_markup=ReplyKeyboardRemove())
    return ADD_NOTIFICATION_TIME


def get_username(update):
    return update.effective_user.username


def start(bot, update):
    reply_keyboard = [["Create Task", "List All Tasks"]]
    username = get_username(update)
    User.objects.get_or_create(username=username)
    update.message.reply_text("Hi! I'm your task manager."
                              "Send /cancel to stop talking to me."
                              "What would you like to do?",
                              reply_markup=ReplyKeyboardMarkup(
                                  reply_keyboard,
                                  one_time_keyboard=True)
                              )
    return GET_COMMAND


def add_task(bot, update):
    reply_markup = ReplyKeyboardRemove()
    update.message.reply_text(
        "Please send me a tasks's title",
        reply_markup=reply_markup
    )
    return TASK_CREATE


def get_tasks_list(user: User):
    tasks = Task.objects.filter(reporter=user)
    keyboard = [[InlineKeyboardButton(task.title, callback_data=task.id)]
                for task in tasks]
    keyboard_markup = InlineKeyboardMarkup(keyboard)
    return keyboard_markup


def list_tasks(bot, update):
    user = update.message.from_user
    user, _ = User.objects.get_or_create(
        username=user.username, defaults={
            "telegram_id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name
        }
    )
    reply_markup = ReplyKeyboardRemove()
    message = update.message.reply_text(
        "Getting tasks list ...", reply_markup=reply_markup
    )
    message.reply_text("Choose a task to view:", reply_markup=get_tasks_list(user))
    return TASK_VIEW


def get_task_fields():
    fields = [field.name for field in Task._meta.get_fields() if field.name not in (
        "id", "reporter", "created"
    )]
    keyboard = [[InlineKeyboardButton(name, callback_data=name)]
                for name in fields]
    keyboard_markup = InlineKeyboardMarkup(keyboard)
    return keyboard_markup


def task_view(bot, update, user_data):
    task_id = update.callback_query.data
    task = Task.objects.get(id=task_id)
    reply_keyboard = [["Edit", "Delete"]]
    user_data["task"] = task
    bot.send_message(chat_id=update.callback_query.from_user.id,
                     text=f"Task {task.title}\nDescription: {task.description}\n"
                     f"Due date: {task.due_date}\nNotification: {task.notification}"
                     f"Status: {task.status}",
                     reply_markup=ReplyKeyboardMarkup(
                         reply_keyboard,
                         one_time_keyboard=True)
                     )
    return SELECT_ACTION


def list_edit_options(bot, update, user_data):
    update.message.reply_text("Choose a property to edit:", reply_markup=get_task_fields())
    return GET_EDIT_ACTION


def delete_task(bot, update, user_data):
    task = user_data["task"]
    title = task.title
    task.delete()
    user_data.clear()
    update.message.reply_text(
        f"The task {title} is deleted.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def add_deadline(bot, update):
    update.message.reply_text("Please select a date: ",
                              reply_markup=telegramcalendar.create_calendar())
    return GET_DEADLINE


def task_create(bot, update, user_data):
    user = update.message.from_user
    user, _ = User.objects.get_or_create(
        username=user.username, defaults={
            "telegram_id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name
        }
    )
    task_title = update.message.text
    task = Task.objects.create(reporter=user, title=task_title)
    user_data.update(task=task)
    reply_keyboard = [["Yes", "No"]]
    update.message.reply_text(
        "Does the task have the deadline?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True)
    )
    return ADD_DEADLINE


def cancel(bot, update):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.username)
    update.message.reply_text(
        "Bye! I hope we can talk again some day.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def say_goodbye(bot, update, user_data):
    user_data.clear()
    update.message.reply_text("Thank you! I hope we can talk again some day.")
    return ConversationHandler.END


def add_notification(bot, update, user_data):
    update.message.reply_text("Please select a date: ",
                              reply_markup=telegramcalendar.create_calendar())
    return GET_NOTIFICATION


def get_edit_action(bot, update, user_data):
    field = update.callback_query.data
    user_data["edit"] = field
    bot.send_message(chat_id=update.callback_query.from_user.id,
                     text=f"Please, send a new value for the task`s {field}.")
    return GET_NEW_VALUE


def edit_task(bot, update, user_data):
    task = user_data["task"]
    field = user_data["edit"]
    value = update.message.text
    try:
        setattr(task, field, value)
        task.save()
    except ValueError:
        update.message.reply_text("Please send a valid value")
        return
    update.message.reply_text(f"The task {task.title} is updated.")
    user_data.clear()
    return ConversationHandler.END


def alarm(bot, job):
    """Send the alarm message."""
    bot.send_message(job.context["chat_id"], text=job.context["task_data"])


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
        update.message.reply_text(
            "Please enter a valid time in format 'HH:MM'"
        )
        return None
    task = user_data["task"]
    task.notification = notification
    task.save(update_fields=["notification"])
    chat_id = update.message.chat_id
    job_queue.run_once(alarm, notification, context={
        "chat_id": chat_id,
        "task_data": f"""You have a task {task.title} {task.description}
                     to do before {task.due_date}!"""
    })
    update.message.reply_text(
        f"""Thanks! I'll send you a notification
        on your task on {notification:%A}, {notification}.""")
    return ConversationHandler.END


def no_deadline(bot, update):
    reply_keyboard = [["Yes", "No"]]
    update.message.reply_text(
        "Do you want to get notification?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True
        )
    )
    return ADD_NOTIFICATION


(
    GET_COMMAND,
    TASK_CREATE,
    GET_DEADLINE,
    ADD_NOTIFICATION,
    ADD_DEADLINE,
    GET_NOTIFICATION,
    ADD_NOTIFICATION_TIME,
    TASK_VIEW,
    SELECT_ACTION,
    GET_EDIT_ACTION,
    GET_NEW_VALUE
) = range(11)


JOBS_PICKLE = 'data/job_tuples.pickle'


def load_jobs(jq):
    now = time()

    with open(JOBS_PICKLE, 'rb') as fp:
        while True:
            try:
                next_t, job = pickle.load(fp)
            except EOFError:
                break  # Loaded all job tuples

            # Create threading primitives
            enabled = job._enabled
            removed = job._remove

            job._enabled = Event()
            job._remove = Event()

            if enabled:
                job._enabled.set()

            if removed:
                job._remove.set()

            next_t -= now  # Convert from absolute to relative time

            jq._put(job, next_t)


def save_jobs(jq):
    if jq:
        job_tuples = jq._queue.queue
    else:
        job_tuples = []

    with open(JOBS_PICKLE, 'wb') as fp:
        for next_t, job in job_tuples:
            # Back up objects
            _job_queue = job._job_queue
            _remove = job._remove
            _enabled = job._enabled

            # Replace un-pickleable threading primitives
            job._job_queue = None  # Will be reset in jq.put
            job._remove = job.removed  # Convert to boolean
            job._enabled = job.enabled  # Convert to boolean

            # Pickle the job
            pickle.dump((next_t, job), fp)

            # Restore objects
            job._job_queue = _job_queue
            job._remove = _remove
            job._enabled = _enabled


def save_jobs_job(bot, job):
    save_jobs(job.job_queue)


def launch_bot():
    updater = Updater(settings.TELEGRAM_BOT_TOKEN)

    job_queue = updater.job_queue

    job_queue.run_repeating(save_jobs_job, timedelta(minutes=1))

    try:
        load_jobs(job_queue)

    except FileNotFoundError:
        # First run
        pass

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
        ],
        states={
            GET_COMMAND: [
                RegexHandler("^Create Task$", add_task),
                RegexHandler("^List All Tasks$", list_tasks),
            ],
            TASK_CREATE: [
                MessageHandler(
                    Filters.text,
                    task_create,
                    pass_user_data=True),
            ],
            ADD_DEADLINE: [
                RegexHandler(
                    "^Yes$",
                    add_deadline),
                RegexHandler(
                    "^No$",
                    no_deadline),
            ],
            GET_DEADLINE: [
                CallbackQueryHandler(
                    deadline_handler,
                    pass_user_data=True)
            ],
            ADD_NOTIFICATION: [
                RegexHandler(
                    "^Yes$",
                    add_notification,
                    pass_user_data=True),
                RegexHandler(
                    "^No$",
                    say_goodbye,
                    pass_user_data=True),
            ],
            GET_NOTIFICATION: [
                CallbackQueryHandler(
                    notification_handler,
                    pass_user_data=True)
            ],
            ADD_NOTIFICATION_TIME: [
                MessageHandler(
                    Filters.text,
                    add_notification_date,
                    pass_user_data=True,
                    pass_job_queue=True),
            ],
            TASK_VIEW: [
                CallbackQueryHandler(
                    task_view,
                    pass_user_data=True)
            ],
            SELECT_ACTION: [
                RegexHandler(
                    "^Edit$",
                    list_edit_options,
                    pass_user_data=True),
                RegexHandler(
                    "^Delete$",
                    delete_task,
                    pass_user_data=True),

            ],
            GET_EDIT_ACTION: [
                CallbackQueryHandler(
                    get_edit_action,
                    pass_user_data=True)
            ],
            GET_NEW_VALUE: [
                MessageHandler(
                    Filters.text,
                    edit_task,
                    pass_user_data=True),
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
        ],
        allow_reentry=True
    )

    updater.dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()

    save_jobs(job_queue)

    logger.info("Started bot")


def bot_loop():
    while True:
        try:
            launch_bot()
        except Exception as e:
            logger.warning(e)
        logger.info("Bot has finished")
        sleep(5)


if __name__ == "__main__":
    launch_bot()
