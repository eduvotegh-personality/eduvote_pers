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

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import ContactMessage
from django.contrib import messages
from django.core.mail import send_mail

from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from .models import Contestant, Payment
import requests
from django.shortcuts import render, redirect

from django.shortcuts import redirect, get_object_or_404
from .models import Payment
from .models import Event, Contestant, Payment

from django.shortcuts import render
from django.http import JsonResponse

import json
import hmac
import hashlib



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

    # contestants for this event
    contestants = Contestant.objects.filter(category__event=selected_event)

    # successful payments for this event
    payments = Payment.objects.filter(
        contestant__category__event=selected_event,
        status="successful"
    )

    # totals
    total_revenue = payments.aggregate(Sum("amount"))["amount__sum"] or 0
    total_votes = payments.aggregate(Sum("votes"))["votes__sum"] or 0
    total_contestants = contestants.count()

    # leaderboard
    leaderboard = contestants.order_by("-total_votes")

    # recent votes (recent successful payments)
    recent_votes = payments.order_by("-created_at")[:10]

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
        email = "vote@eduvote.com"
        amount = float(request.POST.get("amount"))

        votes = int(amount)

        # create payment record
        payment = Payment.objects.create(
            contestant=contestant,
            phone=phone,
            amount=amount,
            votes=votes,
            status="pending"
        )

        url = "https://api.paystack.co/transaction/initialize"

        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }

        callback_url = f"{settings.SITE_URL}/payment/verify/{payment.reference}/"

        payload = {
            "email": email,
            "amount": int(amount * 100),  # convert to kobo
            "reference": str(payment.reference),
            "callback_url": callback_url,
            "metadata": {
                "contestant_id": contestant.id,
                "phone": phone,
                "votes": votes,
            }
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response_data = response.json()
        except requests.exceptions.RequestException:
            return HttpResponse("Unable to reach payment gateway. Try again.")

        if response_data.get("status"):

            payment.authorization_url = response_data["data"]["authorization_url"]
            payment.save()

            return redirect(response_data["data"]["authorization_url"])

        return HttpResponse(f"Payment initialization failed: {response_data}")

    return redirect("home")

def payment_processing(request, reference):
    payment = get_object_or_404(Payment, reference=reference)
    return render(request, "voting/payment_processing.html", {"payment": payment})


def verify_payment(request, reference):

    payment = get_object_or_404(Payment, reference=str(reference))

    verify_url = f"https://api.paystack.co/transaction/verify/{reference}"

    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
    }

    try:
        response = requests.get(verify_url, headers=headers, timeout=30)
        response_data = response.json()
    except requests.exceptions.RequestException:
        messages.error(request, "Payment verification failed. Please contact support.")
        return redirect("home")

    if not response_data.get("status"):
        messages.error(request, "Payment verification error.")
        return redirect("home")

    data = response_data["data"]

    # Payment was successful
    if data["status"] == "success":

        if payment.status != "successful":

            payment.status = "successful"
            payment.save()

            contestant = payment.contestant
            contestant.total_votes += payment.votes
            contestant.save()

        return redirect("vote_success")

    # Payment abandoned or failed
    if data["status"] in ["failed", "abandoned"]:
        messages.error(request, "Payment was not completed.")
        return redirect("home")

    # Pending payments
    messages.warning(request, "Payment is still processing. Please wait.")
    return redirect("home")

def contact(request):

    if request.method == "POST":

        name = request.POST.get("name")
        email = "vote@eduvote.com.gh"
        phone = request.POST.get("phone")
        subject = request.POST.get("subject")
        message = request.POST.get("message")

        ContactMessage.objects.create(
            name=name,
            email=email,
            phone=phone,
            subject=subject,
            message=message
        )

        send_mail(
            subject=f"New EduVote Contact: {subject}",
            message=f"""
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

        messages.success(request, "Message sent successfully!")

        return redirect("contact")

    return render(request, "contact.html")

def vote_success(request):
    return render(request, "vote_success.html")


@login_required
@user_passes_test(is_admin)
def dashboard_live_data(request):

    event_id = request.GET.get("event_id")

    contestants = Contestant.objects.filter(category__event_id=event_id)

    payments = Payment.objects.filter(
        contestant__category__event_id=event_id,
        status="successful"
    )

    total_revenue = payments.aggregate(Sum("amount"))["amount__sum"] or 0
    total_votes = payments.aggregate(Sum("votes"))["votes__sum"] or 0

    leaderboard = list(
        contestants.order_by("-total_votes")
        .values("name", "total_votes")[:10]
    )

    recent_votes = list(
        payments.order_by("-created_at")
        .values("phone", "contestant__name", "amount", "created_at")[:10]
    )

    return JsonResponse({
        "total_revenue": float(total_revenue),
        "total_votes": total_votes,
        "leaderboard": leaderboard,
        "recent_votes": recent_votes
    })


def paystack_webhook(request):

    payload = request.body
    signature = request.headers.get("x-paystack-signature")

    # verify Paystack signature
    computed_signature = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode(),
        payload,
        hashlib.sha512
    ).hexdigest()

    if signature != computed_signature:
        return HttpResponse(status=400)

    event = json.loads(payload)

    if event["event"] == "charge.success":

        reference = event["data"]["reference"]

        try:
            payment = Payment.objects.get(reference=reference)

            if payment.status != "successful":

                payment.status = "successful"
                payment.save()

                contestant = payment.contestant
                contestant.total_votes += payment.votes
                contestant.save()

        except Payment.DoesNotExist:
            pass

    return HttpResponse(status=200)