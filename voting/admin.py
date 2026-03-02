from django.contrib import admin
from .models import Event, Category, Contestant, Vote


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "start_date", "end_date")

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "event")
    list_filter = ("event",)


@admin.register(Contestant)
class ContestantAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "total_votes")
    list_filter = ("category",)


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "contestant", "amount", "status", "timestamp")
    list_filter = ("status",)