from celery.bin.control import status
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Payment, PaymentStatus
from .serializers import PaymentCreateSerializer
from .services import PaymentServiceFactory, FulfillmentFactory


class PaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PaymentCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        handler = FulfillmentFactory.get(request.data['service_type'])
        payment = handler.pre_fulfill(serializer)

        service = PaymentServiceFactory.get(payment.method)
        result = service.process(payment)

        payment.gateway_ref = result["gateway_ref"]
        payment.save(update_fields=["gateway_ref"])

        return Response(result, status=status.HTTP_200_OK)


class WebhookView(APIView):

    def post(self, request, method: str):
        service = PaymentServiceFactory.get(method.upper())
        result = service.verify_webhook(request)

        if not result["status"]:
            return Response({"ok": True})

        try:
            payment = Payment.objects.get(transaction_id=result["transaction_id"])
        except Payment.DoesNotExist:
            return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)

        payment.status = result["status"]
        payment.gateway_response = result["raw_response"]
        payment.save(update_fields=["status", "gateway_response"])

        if payment.status == PaymentStatus.COMPLETED:
            handler = FulfillmentFactory.get(payment.service_type)
            handler.fulfill(payment)

        return Response({"ok": True})
