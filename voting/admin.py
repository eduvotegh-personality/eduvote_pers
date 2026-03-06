from django.contrib import admin
from .models import Event, Category, Contestant, Vote, Payment, ContactMessage


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "start_date", "end_date")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "event")
    list_filter = ("event",)


@admin.register(Contestant)
class ContestantAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "contestant", "amount", "status", "timestamp")
    list_filter = ("status",)
    search_fields = ("phone_number",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("contestant", "amount", "status", "reference", "created_at")
    list_filter = ("status",)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):

    list_display = ("name", "email", "subject", "status", "created_at")

    list_filter = ("status", "created_at")

    search_fields = ("name", "email", "subject")

    list_editable = ("status",)

    readonly_fields = ("name", "email", "phone", "subject", "message", "created_at")

    fieldsets = (
        ("Client Information", {
            "fields": ("name", "email", "phone")
        }),
        ("Request", {
            "fields": ("subject", "message")
        }),
        ("CRM Status", {
            "fields": ("status",)
        }),
        ("System Info", {
            "fields": ("created_at",)
        }),
    )