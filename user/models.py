from django.contrib.auth.models import AbstractUser
from django.db.models import IntegerField


class User(AbstractUser):
    telegram_id = IntegerField(null=True)
