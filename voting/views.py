from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test

from .models import Event, Contestant, Vote
from django.shortcuts import get_object_or_404
from .models import Event, Category
from django.shortcuts import get_object_or_404, render
from django.shortcuts import get_object_or_404, redirect
from .models import Contestant, Vote
from .models import Vote
from django.db.models import Sum, Count
from django.shortcuts import render
from .models import Event, Vote, Contestant
from .models import Category

#.....HUBTEL.....#
from django.shortcuts import render, redirect, get_object_or_404
from .models import Contestant, Payment
from django.conf import settings
import requests

from .models import ContactMessage
from django.contrib import messages
from django.core.mail import send_mail


def event_list(request):
    now = timezone.now()
    events = Event.objects.filter(end_date__gt=now).order_by('end_date')

    return render(request, 'voting/event_list.html', {
        'events': events
    })

def contestant_list(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    categories = Category.objects.filter(
        event=event
    ).prefetch_related("contestants")

    return render(request, "voting/contestant_list.html", {
        "event": event,
        "categories": categories
    })

def simulate_payment(request, contestant_id):
    contestant = get_object_or_404(Contestant, id=contestant_id)
    event = contestant.category.event

    # 🔒 Stop voting if event is not active
    if not event.is_active():
        messages.error(request, "Voting has ended for this event.")
        return redirect('contestant_list', event_id=event.id)

    if request.method == "POST":
        phone = request.POST.get('phone')
        amount = request.POST.get('amount')

        # 🔒 Validation
        if not phone or not amount:
            messages.error(request, "All fields are required.")
            return redirect('contestant_list', event_id=event.id)

        try:
            amount = int(amount)
            if amount < 1:
                messages.error(request, "Amount must be at least 1 GHS.")
                return redirect('contestant_list', event_id=event.id)
        except ValueError:
            messages.error(request, "Invalid amount entered.")
            return redirect('contestant_list', event_id=event.id)

        # 💾 Create Vote
        vote = Vote.objects.create(
            contestant=contestant,
            phone_number=phone,
            amount=amount,
            status="Successful"
        )

        # 📈 Update contestant total votes
        contestant.total_votes += amount
        contestant.save()

        messages.success(request, "Vote Successful!")
        return redirect("vote_receipt", transaction_id=vote.transaction_id)

    return redirect('contestant_list', event_id=event.id)

def vote_receipt(request, transaction_id):
    vote = get_object_or_404(Vote, transaction_id=transaction_id)

    contestant = vote.contestant
    category = contestant.category
    event = category.event

    return render(request, 'voting/vote_receipt.html', {
        'vote': vote,
        'contestant': contestant,
        'category': category,
        'event': event
    })


def is_admin(user):
    return user.is_superuser


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    events = Event.objects.all()

    selected_event_id = request.GET.get("event_id")

    if selected_event_id:
        selected_event = Event.objects.get(id=selected_event_id)
    else:
        selected_event = events.first()

    # Filter data per event
    contestants = Contestant.objects.filter(category__event=selected_event)
    votes = Vote.objects.filter(contestant__category__event=selected_event)

    total_revenue = votes.aggregate(Sum("amount"))["amount__sum"] or 0
    total_votes = votes.aggregate(Sum("votes"))["votes__sum"] or 0
    total_contestants = contestants.count()

    leaderboard = contestants.order_by("-total_votes")
    recent_votes = votes.order_by("-timestamp")[:10]

    context = {
        "events": events,
        "selected_event": selected_event,
        "total_revenue": total_revenue,
        "total_votes": total_votes,
        "total_contestants": total_contestants,
        "leaderboard": leaderboard,
        "recent_votes": recent_votes,
    }

    return render(request, "voting/admin_dashboard.html", context)

def public_results(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    categories = event.categories.prefetch_related('contestants')

    for category in categories:
        contestants = category.contestants.all()
        total_votes = sum(c.total_votes for c in contestants)

        for contestant in contestants:
            if total_votes > 0:
                contestant.percentage = round((contestant.total_votes / total_votes) * 100, 2)
            else:
                contestant.percentage = 0

    return render(request, 'voting/public_results.html', {
        'event': event,
        'categories': categories
    })

def homepage(request):
    return render(request, "homepage.html")

def about(request):
    return render(request, "about.html")

def privacy_policy(request):
    return render(request, "privacy_policy.html")

def terms_of_service(request):
    return render(request, "terms.html")

def initiate_payment(request, contestant_id):
    contestant = get_object_or_404(Contestant, id=contestant_id)

    if request.method == "POST":
        phone = request.POST.get("phone")
        amount = float(request.POST.get("amount"))

        # Define votes logic (example: 1 GHS = 1 vote)
        votes = int(amount)

        payment = Payment.objects.create(
            contestant=contestant,
            phone=phone,
            amount=amount,
            votes=votes
        )

        # 🔥 HUBTEL INTEGRATION PLACEHOLDER
        # When Hubtel gives credentials, replace below

        hubtel_payload = {
            "amount": amount,
            "customerNumber": phone,
            "description": f"Vote for {contestant.name}",
            "callbackUrl": settings.SITE_URL + "/payment/callback/",
            "returnUrl": settings.SITE_URL + "/payment/verify/" + str(payment.reference)
        }

        # For now simulate redirect
        return redirect("payment_processing", payment.reference)

    return redirect("home")

def payment_processing(request, reference):
    payment = get_object_or_404(Payment, reference=reference)
    return render(request, "voting/payment_processing.html", {"payment": payment})

def verify_payment(request, reference):
    payment = get_object_or_404(Payment, reference=reference)

    # 🔥 HERE we will verify with Hubtel API later

    # For now simulate success
    payment.status = "successful"
    payment.save()

    # Add votes
    payment.contestant.total_votes += payment.votes
    payment.contestant.save()

    return redirect("vote_success")

def contact(request):

    if request.method == "POST":

        name = request.POST.get("name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        subject = request.POST.get("subject")
        message = request.POST.get("message")

        # Save message
        ContactMessage.objects.create(
            name=name,
            email=email,
            phone=phone,
            subject=subject,
            message=message
        )

        # Send Email Notification
        send_mail(
            subject=f"New EduVote Contact: {subject}",
            message=f"""
New Contact Message

Name: {name}
Email: {email}
Phone: {phone}

Message:
{message}
""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=["eduvote.gh@gmail.com"],
            fail_silently=True,
        )

        messages.success(request, "✅ Your message has been sent successfully!")

        return redirect("contact")

    return render(request, "contact.html")
