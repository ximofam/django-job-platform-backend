from django.urls import path

from apps.payments import views

urlpatterns = [
    path('api/payments/', views.PaymentView.as_view(), name='create-payment'),
    path('api/payments/webhook/<str:method>/', views.WebhookView.as_view(), name='payment-callback')
]
