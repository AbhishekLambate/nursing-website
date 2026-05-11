from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel
import os
import json
import base64
import hashlib
import requests
import time
from database import get_db
import sqlite3

router = APIRouter()

MERCHANT_ID = os.environ.get('PHONEPE_MERCHANT_ID', 'PGTESTPAYUAT')
SALT_KEY = os.environ.get('PHONEPE_SALT_KEY', '099eb0cd-02cf-4dc2-a4c3-df3f7c1d6b04')
SALT_INDEX = os.environ.get('PHONEPE_SALT_INDEX', '1')
PHONEPE_HOST = os.environ.get('PHONEPE_HOST', 'https://api-preprod.phonepe.com/apis/pg-sandbox')
CALLBACK_URL = os.environ.get('PHONEPE_CALLBACK_URL', 'http://localhost:3000/api/payment/callback')
REDIRECT_URL = os.environ.get('PHONEPE_REDIRECT_URL', 'http://localhost:3000/payment-success')

class PaymentInitiateRequest(BaseModel):
    registration_id: int
    amount: float
    name: str = None
    mobile: str = None
    email: str = None

def generate_checksum(payload: dict, endpoint: str):
    base64_payload = base64.b64encode(json.dumps(payload, separators=(',', ':')).encode()).decode()
    string_to_hash = base64_payload + endpoint + SALT_KEY
    hash_str = hashlib.sha256(string_to_hash.encode()).hexdigest()
    return {
        "base64": base64_payload,
        "checksum": f"{hash_str}###{SALT_INDEX}"
    }

@router.post("/initiate")
def initiate_payment(data: PaymentInitiateRequest, db: sqlite3.Connection = Depends(get_db)):
    if not data.registration_id or not data.amount:
        raise HTTPException(status_code=400, detail="Registration ID and amount are required")

    merchantTransactionId = f"MT{int(time.time()*1000)}{data.registration_id}"
    amountInPaise = int(round(data.amount * 100))
    mobile_cleaned = "".join(filter(str.isdigit, data.mobile)) if data.mobile else ""

    payload = {
        "merchantId": MERCHANT_ID,
        "merchantTransactionId": merchantTransactionId,
        "merchantUserId": f"MU{data.registration_id}",
        "amount": amountInPaise,
        "redirectUrl": f"{REDIRECT_URL}?txnId={merchantTransactionId}",
        "redirectMode": "REDIRECT",
        "callbackUrl": CALLBACK_URL,
        "mobileNumber": mobile_cleaned,
        "paymentInstrument": { "type": "PAY_PAGE" }
    }

    endpoint = "/pg/v1/pay"
    checksum_data = generate_checksum(payload, endpoint)

    headers = {
        "Content-Type": "application/json",
        "X-VERIFY": checksum_data["checksum"],
        "X-MERCHANT-ID": MERCHANT_ID
    }

    from fastapi.responses import JSONResponse

    try:
        response = requests.post(f"{PHONEPE_HOST}{endpoint}", json={"request": checksum_data["base64"]}, headers=headers)
        res_data = response.json()

        if res_data.get("success"):
            cursor = db.cursor()
            cursor.execute('''
                UPDATE registrations SET transaction_id=?, payment_id=? WHERE id=?
            ''', (merchantTransactionId, merchantTransactionId, data.registration_id))
            db.commit()

            return {
                "success": True,
                "paymentUrl": res_data["data"]["instrumentResponse"]["redirectInfo"]["url"],
                "transactionId": merchantTransactionId
            }
        else:
            return JSONResponse(status_code=400, content={"error": "Payment gateway error", "details": res_data.get("message") or "Payment initiation failed"})
    except requests.exceptions.RequestException as e:
        print("PhonePe error:", e.response.json() if e.response else e)
        return JSONResponse(status_code=500, content={"error": "Payment gateway error", "details": str(e)})
    except Exception as e:
        print("PhonePe error:", e)
        return JSONResponse(status_code=500, content={"error": "Payment gateway error", "details": str(e)})

@router.post("/callback")
async def payment_callback(request: Request, db: sqlite3.Connection = Depends(get_db)):
    x_verify = request.headers.get("x-verify")
    body = await request.form()
    response_payload = body.get("response")
    
    # Fastapi might receive it as json depending on how PhonePe sends callback
    if not response_payload:
        try:
            json_body = await request.json()
            response_payload = json_body.get("response")
        except:
            pass

    if not response_payload or not x_verify:
        raise HTTPException(status_code=400, detail="Invalid request")

    string_to_hash = response_payload + SALT_KEY
    expected_hash = hashlib.sha256(string_to_hash.encode()).hexdigest()
    expected_checksum = f"{expected_hash}###{SALT_INDEX}"

    if x_verify != expected_checksum:
        print("Checksum mismatch!")
        raise HTTPException(status_code=400, detail="Checksum mismatch")

    decoded_json = json.loads(base64.b64decode(response_payload).decode("utf-8"))
    payload_data = decoded_json.get("data", {})
    
    merchantTransactionId = payload_data.get("merchantTransactionId")
    transactionId = payload_data.get("transactionId")
    code = payload_data.get("code")
    paymentInstrument = payload_data.get("paymentInstrument", {})

    success = (code == "PAYMENT_SUCCESS")

    status_str = "success" if success else "failed"
    txn_id_val = transactionId or merchantTransactionId
    payment_method = paymentInstrument.get("type", "")
    payment_data_str = json.dumps(payload_data)

    cursor = db.cursor()
    cursor.execute('''
        UPDATE registrations SET 
        payment_status=?, transaction_id=?, payment_method=?, payment_data=?
        WHERE transaction_id=? OR payment_id=?
    ''', (status_str, txn_id_val, payment_method, payment_data_str, merchantTransactionId, merchantTransactionId))
    db.commit()

    print(f"✅ Payment callback: {merchantTransactionId} -> {'SUCCESS' if success else 'FAILED'}")
    return "OK"

@router.get("/status/{txnId}")
def get_payment_status(txnId: str, db: sqlite3.Connection = Depends(get_db)):
    endpoint = f"/pg/v1/status/{MERCHANT_ID}/{txnId}"
    string_to_hash = endpoint + SALT_KEY
    hash_str = hashlib.sha256(string_to_hash.encode()).hexdigest()
    checksum = f"{hash_str}###{SALT_INDEX}"

    headers = {
        "Content-Type": "application/json",
        "X-VERIFY": checksum,
        "X-MERCHANT-ID": MERCHANT_ID
    }

    try:
        response = requests.get(f"{PHONEPE_HOST}{endpoint}", headers=headers)
        data = response.json()
        cursor = db.cursor()

        if data.get("success") and data.get("data", {}).get("responseCode") == "SUCCESS":
            cursor.execute('''
                UPDATE registrations SET payment_status='success', transaction_id=? WHERE transaction_id=? OR payment_id=?
            ''', (data["data"].get("transactionId"), txnId, txnId))
            db.commit()

        reg = cursor.execute('SELECT * FROM registrations WHERE transaction_id=? OR payment_id=?', (txnId, txnId)).fetchone()
        return {
            "success": data.get("success"),
            "code": data.get("data", {}).get("responseCode"),
            "registration": dict(reg) if reg else None
        }
    except Exception as e:
        print("Status check error:", e)
        raise HTTPException(status_code=500, detail="Status check failed")
