import hashlib, hmac, json
from decimal import Decimal

import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .client import FintechhubClient
# Order importini hozirgi views.py dagidek qoldiring (from apps.... import Order)

PAYMENT_BASE_URL = "http://159.223.145.49:3079"


# ---------- LOGIN / REGISTER (ustoz usuli) ----------
def _forward_auth(request, path):
    if request.method != "POST":
        return JsonResponse({"error": "Faqat POST"}, status=405)
    try:
        data = json.loads(request.body) if request.body else request.POST.dict()
    except ValueError:
        return JsonResponse({"error": "Noto'g'ri JSON"}, status=400)
    try:
        resp = requests.post(f"{PAYMENT_BASE_URL}{path}", json=data, timeout=20)
    except requests.exceptions.Timeout:
        return JsonResponse({"error": "Fintechhub javob bermadi"}, status=504)
    except requests.exceptions.RequestException as e:
        return JsonResponse({"error": str(e)}, status=502)
    try:
        return JsonResponse(resp.json(), status=resp.status_code, safe=False)
    except ValueError:
        return JsonResponse({"error": "Noto'g'ri javob", "raw": resp.text}, status=502)


@csrf_exempt
def login(request):
    return _forward_auth(request, "/api/auth/login/")


@csrf_exempt
def register(request):
    return _forward_auth(request, "/api/auth/register/")


# ---------- TO'LOV PROXY ----------
class FintechProxy(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    path = None

    def post(self, request):
        body = {k: v for k, v in request.data.items()}
        body["service_id"] = int(settings.FHP_SERVICE_ID)
        try:
            resp = FintechhubClient().request("POST", self.path, json_data=body)
        except requests.exceptions.Timeout:
            return Response({"error": "Fintechhub javob bermadi (timeout)"}, status=504)
        except requests.exceptions.RequestException as e:
            return Response({"error": str(e)}, status=502)
        try:
            data = resp.json()
        except ValueError:
            data = {"error": "Noto'g'ri javob", "raw": resp.text}
        return Response(data, status=resp.status_code)


class PayInitView(FintechProxy):
    path = "/v2/pay/init"

class CardRequestView(FintechProxy):
    path = "/v2/merchant/card_token/request"

class CardVerifyView(FintechProxy):
    path = "/v2/merchant/card_token/verify"

class CardPaymentView(FintechProxy):
    path = "/v2/merchant/card_token/payment"


# ---------- CALLBACKLAR (Fintechhub chaqiradi) ----------
def make_sign(*parts):
    return hashlib.md5("".join(str(p) for p in parts).encode()).hexdigest()


class PrepareCallbackView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        d = request.data
        expected = make_sign(
            d.get("click_trans_id"), d.get("service_id"),
            settings.FHP_SERVICE_SECRET_KEY, d.get("merchant_trans_id"),
            d.get("amount"), d.get("action"), d.get("sign_time"),
        )
        if not hmac.compare_digest(expected, str(d.get("sign_string", ""))):
            return Response({"error": -1, "error_note": "SIGN CHECK FAILED"})
        try:
            order = Order.objects.get(id=d.get("merchant_trans_id"))
        except Order.DoesNotExist:
            return Response({"error": -5, "error_note": "Order not found"})
        # amount maydoni nomini o'zingizniki bilan almashtiring (masalan total_price)
        if Decimal(str(d.get("amount"))) != Decimal(str(order.total_price)):
            return Response({"error": -2, "error_note": "Incorrect amount"})
        return Response({
            "click_trans_id": d.get("click_trans_id"),
            "merchant_trans_id": d.get("merchant_trans_id"),
            "merchant_prepare_id": order.id,
            "error": 0, "error_note": "Success",
        })


class CompleteCallbackView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        d = request.data
        expected = make_sign(
            d.get("click_trans_id"), d.get("service_id"),
            settings.FHP_SERVICE_SECRET_KEY, d.get("merchant_trans_id"),
            d.get("merchant_prepare_id"), d.get("amount"),
            d.get("action"), d.get("sign_time"),
        )
        if not hmac.compare_digest(expected, str(d.get("sign_string", ""))):
            return Response({"error": -1, "error_note": "SIGN CHECK FAILED"})
        try:
            order = Order.objects.get(id=d.get("merchant_trans_id"))
        except Order.DoesNotExist:
            return Response({"error": -5, "error_note": "Order not found"})
        if str(d.get("error")) == "0":
            order.status = "paid"
            order.save()
        return Response({
            "click_trans_id": d.get("click_trans_id"),
            "merchant_trans_id": d.get("merchant_trans_id"),
            "merchant_confirm_id": order.id,
            "error": 0, "error_note": "Success",
        })