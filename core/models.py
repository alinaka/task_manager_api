from django.db import models

from user.models import User


class Task(models.Model):
    IN_PROGRESS = "IN_PROGRESS"
    TO_DO = "TO_DO"
    DONE = "DONE"

    STATUS_CHOICES = (
        (IN_PROGRESS, "In Progress"),
        (TO_DO, "To Do"),
        (DONE, "Done"),
    )

    created = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=120)
    description = models.CharField(max_length=255, blank=True)
    due_date = models.DateField(null=True)
    notification = models.DateTimeField(null=True)
    reporter = models.ForeignKey(to=User, on_delete=models.SET_NULL, null=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=TO_DO)
