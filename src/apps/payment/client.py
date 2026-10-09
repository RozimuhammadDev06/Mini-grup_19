import time
import hashlib
import requests
from django.conf import settings


class FintechhubClient:
    def __init__(self):
        self.base_url = settings.FHP_BASE_URL.rstrip('/')
        self.merchant_user_id = settings.FHP_MERCHANT_USER_ID
        self.merchant_secret_key = settings.FHP_MERCHANT_SECRET_KEY

    def _build_auth_header(self):
        timestamp = str(int(time.time()))
        raw = timestamp + self.merchant_secret_key
        digest = hashlib.sha1(raw.encode()).hexdigest()
        return f"{self.merchant_user_id}:{digest}:{timestamp}"

    def login(self, email, password):
        url = f"{self.base_url}/auth/login/"
        response = requests.post(
            url,
            json={"email": email, "password": password},
            headers={"Content-Type": "application/json"},
            timeout=20,
        )
        return response

    def request(self, method, path, json_data=None, params=None):
        url = f"{self.base_url}{path}"
        headers = {
            "Auth": self._build_auth_header(),
            "Content-Type": "application/json",
        }
        response = requests.request(
            method,
            url,
            json=json_data,
            params=params,
            headers=headers,
            timeout=20,
        )
        return response

    def pay_init(self, service_id, merchant_trans_id, amount, phone_number, return_url=None):
        data = {
            "service_id": service_id,
            "merchant_trans_id": merchant_trans_id,
            "amount": str(amount),
            "phone_number": phone_number,
        }
        if return_url:
            data["return_url"] = return_url
        return self.request("POST", "/v2/pay/init", json_data=data)

    def card_token_request(self, service_id, card_number, expire_date, save_card=False):
        data = {
            "service_id": service_id,
            "card_number": card_number,
            "expire_date": expire_date,
            "temporary": not save_card,
        }
        return self.request("POST", "/v2/merchant/card_token/request", json_data=data)

    def card_token_verify(self, service_id, card_token, sms_code):
        data = {
            "service_id": service_id,
            "card_token": card_token,
            "sms_code": sms_code,
        }
        return self.request("POST", "/v2/merchant/card_token/verify", json_data=data)

    def card_token_payment(self, service_id, card_token, amount, merchant_trans_id):
        data = {
            "service_id": service_id,
            "card_token": card_token,
            "amount": str(amount),
            "transaction_parameter": merchant_trans_id,
        }
        return self.request("POST", "/v2/merchant/card_token/payment", json_data=data)

    def payment_status(self, service_id, payment_id):
        return self.request("GET", f"/merchant/payment/status/{service_id}/{payment_id}")

    def payment_status_by_mti(self, service_id, merchant_trans_id):
        return self.request("GET", f"/merchant/payment/status_by_mti/{service_id}/{merchant_trans_id}")

    def refund(self, service_id, payment_id):
        return self.request("DELETE", f"/merchant/payment/reversal/{service_id}/{payment_id}")