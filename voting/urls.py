from django.urls import path
from . import views


urlpatterns = [
   path('', views.homepage, name='homepage'),
    path('events/', views.event_list, name='event_list'),
    path('event/<int:event_id>/', views.contestant_list, name='contestant_list'),
    path('simulate/<int:contestant_id>/', views.simulate_payment, name='simulate_payment'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('results/<int:event_id>/', views.public_results, name='public_results'),

    path("receipt/<str:transaction_id>/", views.vote_receipt, name="vote_receipt"),

    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms/', views.terms_of_service, name='terms'),

    path("payment/initiate/<int:contestant_id>/", views.initiate_payment, name="initiate_payment"),
    path("payment/processing/<uuid:reference>/", views.payment_processing, name="payment_processing"),
    path("payment/verify/<str:reference>/", views.verify_payment, name="verify_payment"),
    path("vote-success/", views.vote_success, name="vote_success"),
    path("dashboard/live-data/", views.dashboard_live_data, name="dashboard_live_data"),
]
