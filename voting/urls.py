from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),   # NEW homepage
    path('events/', views.event_list, name='event_list'),  # Active elections
    path('event/<int:event_id>/', views.contestant_list, name='contestant_list'),
    path('simulate/<int:contestant_id>/', views.simulate_payment, name='simulate_payment'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('results/<int:event_id>/', views.public_results, name='public_results'),
    path("receipt/<str:transaction_id>/", views.vote_receipt, name="vote_receipt"),
    path('', views.homepage, name='homepage'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms/', views.terms_of_service, name='terms'),
]