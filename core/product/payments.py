import razorpay
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import hmac
import hashlib

# Initialize Razorpay Client
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

@csrf_exempt
def create_order(request):
    if request.method == "POST":
        data = json.loads(request.body)
        amount = data.get("amount")

        payment = razorpay_client.order.create({
            "amount": int(amount) * 100,  # Convert to paise
            "currency": "INR",
            "payment_capture": 1  # Auto capture payment
        })

        return JsonResponse(payment)

@csrf_exempt
def verify_payment(request):
    if request.method == "POST":
        data = json.loads(request.body)
        razorpay_order_id = data.get("razorpay_order_id")
        razorpay_payment_id = data.get("razorpay_payment_id")
        razorpay_signature = data.get("razorpay_signature")

        secret = settings.RAZORPAY_KEY_SECRET
        generated_signature = hmac.new(
            secret.encode(), f"{razorpay_order_id}|{razorpay_payment_id}".encode(), hashlib.sha256
        ).hexdigest()

        if generated_signature == razorpay_signature:
            return JsonResponse({"success": True, "message": "Payment Verified!"})
        else:
            return JsonResponse({"success": False, "message": "Payment Verification Failed!"}, status=400)
