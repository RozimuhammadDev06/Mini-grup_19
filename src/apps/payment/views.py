import hashlib
from decimal import Decimal
from datetime import datetime
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from apps.shop.models import Order
from apps.payment.models import Payment, CallbackLog


def build_prepare_sign(click_trans_id, service_id, secret_key, merchant_trans_id, amount, action, sign_time):
    raw = f"{click_trans_id}{service_id}{secret_key}{merchant_trans_id}{amount}{action}{sign_time}"
    return hashlib.md5(raw.encode()).hexdigest()


def build_complete_sign(click_trans_id, service_id, secret_key, merchant_trans_id, merchant_prepare_id, amount, action, sign_time):
    raw = f"{click_trans_id}{service_id}{secret_key}{merchant_trans_id}{merchant_prepare_id}{amount}{action}{sign_time}"
    return hashlib.md5(raw.encode()).hexdigest()


class PrepareCallbackView(APIView):
    def post(self, request):
        data = request.data
        click_trans_id = data.get("click_trans_id")
        service_id = data.get("service_id")
        merchant_trans_id = data.get("merchant_trans_id")
        amount = data.get("amount")
        action = data.get("action")
        sign_time = data.get("sign_time")
        sign_string = data.get("sign_string")

        expected_sign = build_prepare_sign(
            click_trans_id, service_id, settings.FHP_SERVICE_SECRET_KEY,
            merchant_trans_id, amount, action, sign_time
        )

        signature_valid = expected_sign == sign_string

        response_data = {"error": -1, "error_note": "Invalid signature"}

        if signature_valid:
            try:
                order = Order.objects.get(number=merchant_trans_id)
                if Decimal(str(order.total)) == Decimal(str(amount)) and order.status in ("pending", "pending_payment"):
                    payment, created = Payment.objects.get_or_create(
                        order=order,
                        defaults={"fhp_payment_id": click_trans_id, "prepared_at": timezone.now()}
                    )
                    response_data = {
                        "error": 0,
                        "error_note": "Success",
                        "merchant_prepare_id": payment.id,
                    }
                else:
                    response_data = {"error": -5, "error_note": "Order already paid or amount mismatch"}
            except Order.DoesNotExist:
                response_data = {"error": -5, "error_note": "Order not found"}

        CallbackLog.objects.create(
            endpoint="prepare",
            raw_payload=data,
            signature_valid=signature_valid,
            response_sent=response_data,
        )

        return Response(response_data)


class CompleteCallbackView(APIView):
    def post(self, request):
        data = request.data
        click_trans_id = data.get("click_trans_id")
        service_id = data.get("service_id")
        merchant_trans_id = data.get("merchant_trans_id")
        merchant_prepare_id = data.get("merchant_prepare_id")
        amount = data.get("amount")
        action = data.get("action")
        sign_time = data.get("sign_time")
        sign_string = data.get("sign_string")
        error = data.get("error")

        expected_sign = build_complete_sign(
            click_trans_id, service_id, settings.FHP_SERVICE_SECRET_KEY,
            merchant_trans_id, merchant_prepare_id, amount, action, sign_time
        )

        signature_valid = expected_sign == sign_string

        response_data = {"error": -1, "error_note": "Invalid signature"}

        if signature_valid:
            try:
                payment = Payment.objects.get(id=merchant_prepare_id)
                if str(error) == "0":
                    payment.fhp_status = 3
                    payment.confirmed_at = timezone.now()
                    payment.save()
                    payment.order.status = "paid"
                    payment.order.save()
                    response_data = {
                        "error": 0,
                        "error_note": "Success",
                        "merchant_confirm_id": payment.id,
                    }
                else:
                    payment.refunded_at = timezone.now()
                    payment.save()
                    payment.order.status = "refunded"
                    payment.order.save()
                    response_data = {
                        "error": 0,
                        "error_note": "Success",
                        "merchant_confirm_id": payment.id,
                    }
            except Payment.DoesNotExist:
                response_data = {"error": -5, "error_note": "Payment not found"}

        CallbackLog.objects.create(
            endpoint="complete",
            raw_payload=data,
            signature_valid=signature_valid,
            response_sent=response_data,
        )

        return Response(response_data)
    
from apps.payment.client import FintechhubClient


class CheckoutPayView(APIView):
    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        if order.status == "paid":
            return Response({"error_code": "ORDER_ALREADY_PAID"}, status=400)

        phone_number = request.data.get("phone_number", "")

        client = FintechhubClient()
        response = client.pay_init(
            service_id=settings.FHP_SERVICE_ID,
            merchant_trans_id=order.number,
            amount=order.total,
            phone_number=phone_number,
        )

        if response.status_code != 200:
            return Response({"error": "Fintechhub xatosi", "detail": response.text}, status=502)

        data = response.json()
        order.status = "pending_payment"
        order.save()

        return Response({
            "order_id": order.id,
            "amount": str(order.total),
            "status": order.status,
            "payment_id": data.get("payment_id"),
        })

import re
from apps.payment.models import CardToken


class CardRequestView(APIView):
    def post(self, request):
        order_id = request.data.get("order_id")
        card_number = request.data.get("card_number", "")
        expire_date = request.data.get("expire_date", "")
        save_card = request.data.get("save_card", False)

        if not re.fullmatch(r"\d{16}", card_number):
            return Response({"error_code": "CARD_INVALID"}, status=400)

        if not re.fullmatch(r"(0[1-9]|1[0-2])\d{2}", expire_date):
            return Response({"error_code": "CARD_INVALID"}, status=400)

        month = int(expire_date[:2])
        year = 2000 + int(expire_date[2:])
        now = timezone.now()
        if (year, month) < (now.year, now.month):
            return Response({"error_code": "CARD_EXPIRED"}, status=400)

        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)
        if order.status == "paid":
            return Response({"error_code": "ORDER_ALREADY_PAID"}, status=400)

        client = FintechhubClient()
        response = client.card_token_request(
            service_id=settings.FHP_SERVICE_ID,
            card_number=card_number,
            expire_date=expire_date,
            save_card=save_card,
        )

        if response.status_code != 200:
            return Response({"error": "Fintechhub xatosi", "detail": response.text}, status=502)

        data = response.json()
        card_mask = data.get("card_number", card_number[:6] + "******" + card_number[-4:])

        card_token_obj = CardToken.objects.create(
            user=request.user if request.user.is_authenticated else None,
            card_token=data.get("card_token", ""),
            card_number_masked=card_mask,
            card_expire=expire_date,
            status="pending",
            temporary=not save_card,
        )

        result = {
            "reference_id": card_token_obj.id,
            "card_mask": card_mask,
            "otp_length": data.get("otp_length", 6),
            "resend_after_sec": data.get("resend_after_sec", 60),
        }
        if settings.FHP_RETURN_DEBUG_OTP and data.get("otp"):
            result["debug_otp"] = data["otp"]
        return Response(result)


class CardVerifyView(APIView):
    def post(self, request):
        order_id = request.data.get("order_id")
        reference_id = request.data.get("reference_id")
        sms_code = request.data.get("sms_code")

        try:
            order = Order.objects.get(id=order_id)
            card_token_obj = CardToken.objects.get(id=reference_id)
        except (Order.DoesNotExist, CardToken.DoesNotExist):
            return Response({"error": "Not found"}, status=404)

        if order.status == "paid":
            return Response({"error_code": "ORDER_ALREADY_PAID"}, status=400)

        client = FintechhubClient()
        verify_response = client.card_token_verify(
            service_id=settings.FHP_SERVICE_ID,
            card_token=card_token_obj.card_token,
            sms_code=sms_code,
        )

        if verify_response.status_code != 200:
            code = "OTP_EXPIRED" if "expired" in verify_response.text.lower() else "OTP_INVALID"
            return Response({"error_code": code}, status=400)

        card_token_obj.status = "active"
        card_token_obj.save()

        pay_response = client.card_token_payment(
            service_id=settings.FHP_SERVICE_ID,
            card_token=card_token_obj.card_token,
            amount=order.total,
            merchant_trans_id=order.number,
        )

        if pay_response.status_code != 200:
            return Response({"status": "FAILED", "error_code": "PAYMENT_REJECTED"}, status=400)

        order.refresh_from_db()
        final_status = "PAID" if order.status == "paid" else "PENDING"

        return Response({"status": final_status})