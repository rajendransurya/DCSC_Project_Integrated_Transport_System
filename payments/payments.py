import json
import os
import sys
import time
import uuid
import jsonpickle
import redis
from flask import Flask, request, Response
from datetime import datetime, timedelta
import logging
sys.path.append('..')
from db import db_utils

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

redisHost = os.getenv("REDIS_HOST")
redisPort = os.getenv("REDIS_PORT")
TRANSACTION_KEY='transactions'
LOG_KEY= 'logging'
EMAIL_KEY ='mail'

message_queue = redis.StrictRedis(host=redisHost, port=redisPort, db=1, decode_responses=True)

def buildResponse(status_code, message):
 response = {"success": status_code == 200,
             "message": message}
 response_pickled = jsonpickle.encode(response)
 return Response(response=response_pickled, status=status_code, mimetype="application/json")

db_pool = db_utils.DBUtil()

@app.route('/api/topup/payment',methods=['POST'])
def payment():
 request_data = request.get_json()
 if request_data and 'card_id' in request_data and 'amount' in request_data and 'payment_method' in request_data:
  card_id = request_data.get("card_id")
  amount = request_data.get("amount")
  payment_method = request_data.get("payment_method")
  email = request_data.get("email")
  name = request_data.get("name")

  try:
   with db_pool.get_db_cursor() as cur:
    payment_status = 'Success'
    if payment_method == 'gpay':
     payment_status = 'Failure'
    insert_script = 'INSERT INTO pmt.payment (card_id, amount, payment_method, payment_status) VALUES (%s, %s, %s, %s)  RETURNING payment_id'
    insert_values = (f'{card_id}', amount, payment_method, payment_status)
    cur.execute(insert_script, insert_values)
    payment_id = cur.fetchone()
    timeout_seconds=5
    time.sleep(timeout_seconds)

    timestamp = datetime.now()
    timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')

    transaction_details = {
     "type": 'T',
     "transaction_id": str(uuid.uuid4()),
     "card_id": card_id,
     "amount": amount,
     "payment_method": payment_method,
     "payment_status": payment_status,
     "created_at": timestamp,
     "updated_at": timestamp
    }
    transaction_details_json = json.dumps(transaction_details)
    message_queue.lpush(LOG_KEY, f"Pushed transaction data to queue {payment_id}")
    message_queue.lpush(TRANSACTION_KEY, transaction_details_json)

    email_details={
     "email" : email,
     "name" : name,
     "amount" : amount,
     "transaction_id":payment_id,
     "status":payment_status
    }

    email_details_json=json.dumps(email_details)
    message_queue.lpush(LOG_KEY, f"Pushed transaction status data to notification queue {payment_id}")
    message_queue.lpush(EMAIL_KEY, email_details_json)

    response = {
     "payment_id":payment_id,
     "amount": amount,
     "payment_method":payment_method,
     "payment_status": payment_status,
    }
    response_pickled = jsonpickle.encode(response)
    logger.debug("Transaction details being returned to caller")
    return Response(response_pickled, status=200, mimetype="application/json")
  except Exception as e:
   logger.error(f"Database execution error in payments: {e}")
   return buildResponse(500, {"success": False, "message": "Database execution error in payments"})# Can also use 400 Bad Request for database execution issues

 else:
  logger.debug("Bad input for payments")
  return buildResponse(400, "Bad input for fare_calculation")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6200, debug=True)

