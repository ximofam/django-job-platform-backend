from abc import ABC, abstractmethod

import stripe
from django.conf import settings

from ..models import Payment, PaymentMethod, PaymentStatus


class PaymentService(ABC):
    @abstractmethod
    def process(self, payment: Payment) -> dict:
        pass

    @abstractmethod
    def verify_webhook(self, request) -> dict:
        pass


class StripePaymentService(PaymentService):

    def _get_unit_amount(self, payment: Payment) -> int:
        if payment.currency.upper() == 'VND':
            return int(payment.amount)
        return int(payment.amount * 100)

    def process(self, payment: Payment) -> dict:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        unit_amount = self._get_unit_amount(payment)

        try:
            intent = stripe.PaymentIntent.create(
                amount=unit_amount,
                currency=payment.currency.lower(),
                payment_method_types=['card'],
                metadata={
                    "service_type": payment.service_type,
                    "transaction_id": str(payment.transaction_id)
                },
                idempotency_key=str(payment.transaction_id),
            )
            return {
                "client_secret": intent.client_secret,
                "gateway_ref": intent.id,
            }
        except Exception as e:
            raise ValueError(f"Không thể khởi tạo PaymentIntent: {str(e)}")

    def verify_webhook(self, request) -> dict:
        payload = request.body
        signature = request.headers.get("Stripe-Signature")

        if not signature:
            raise ValueError("Thiếu header Stripe-Signature")

        stripe.api_key = settings.STRIPE_SECRET_KEY
        endpoint_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', None)

        try:
            event = stripe.Webhook.construct_event(payload, signature, endpoint_secret)
        except ValueError:
            raise ValueError("Payload từ Stripe không hợp lệ.")
        except stripe.error.SignatureVerificationError:
            raise ValueError("Chữ ký Webhook không hợp lệ.")

        result = {
            "status": None,
            "transaction_id": None,
            "gateway_ref": None,
        }

        if event.type == 'payment_intent.succeeded':
            intent = event.data.object
            metadata = intent.metadata

            result.update({
                "status": PaymentStatus.COMPLETED,
                "transaction_id": metadata.transaction_id,
                "gateway_ref": intent.id
            })

        elif event.type == 'payment_intent.payment_failed':
            intent = event.data.object
            metadata = intent.metadata
            result.update({
                "status": PaymentStatus.FAILED,
                "transaction_id": metadata.transaction_id,
                "gateway_ref": intent.id
            })

        return result


class PaymentServiceFactory:
    _services = {
        PaymentMethod.STRIPE: StripePaymentService,
    }

    @classmethod
    def get(cls, method) -> PaymentService:
        service_class = cls._services.get(method)

        if not service_class:
            raise ValueError(f'Unsupported payment method: {method}')

        return service_class()
