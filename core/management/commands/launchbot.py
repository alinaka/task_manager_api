from django.core.management.base import BaseCommand
from bot.bot import bot_loop


class Command(BaseCommand):
    help = 'Launches Telegram Bot'

    def handle(self, *args, **options):
        bot_loop()
