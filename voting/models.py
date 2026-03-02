from django.db import models
from django.utils import timezone
from django.db import models
import uuid

from django.utils import timezone

from django.utils import timezone
from django.db import models

class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    image = models.ImageField(upload_to='event_images/', blank=True, null=True)

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    created_at = models.DateTimeField(default=timezone.now)

    def is_active(self):
        now = timezone.now()
        return self.start_date <= now <= self.end_date

    def __str__(self):
        return self.title

class Category(models.Model):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="categories"
    )

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.event.title} - {self.name}"

class Contestant(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="contestants"
    )

    name = models.CharField(max_length=100)
    photo = models.ImageField(upload_to="contestants/")
    bio = models.TextField(blank=True)

    total_votes = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.name} - {self.category.name}"

class Vote(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Successful", "Successful"),
        ("Failed", "Failed"),
    ]

    contestant = models.ForeignKey(
        Contestant,
        on_delete=models.CASCADE,
        related_name="votes"
    )

    phone_number = models.CharField(max_length=15)

    amount = models.PositiveIntegerField(
        help_text="Amount paid in GHS"
    )

    votes = models.PositiveIntegerField(
        help_text="Number of votes received"
    )

    transaction_id = models.CharField(
        max_length=100,
        unique=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending"
    )

    timestamp = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = f"EDU-{uuid.uuid4().hex[:10].upper()}"

        self.votes = self.amount

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.phone_number} - {self.contestant.name} - {self.status}"

