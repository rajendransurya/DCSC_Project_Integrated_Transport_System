import sys
import time
import uuid
import jsonpickle
from flask import Flask, request, Response
import logging
sys.path.append('..')
from db import db_utils

app = Flask(__name__)

logger = logging.getLogger('werkzeug')
logger.setLevel(logging.DEBUG)

def buildResponse(status_code, message):
 response = {"success": status_code == 200,
             "message": message}
 response_pickled = jsonpickle.encode(response)
 return Response(response=response_pickled, status=status_code, mimetype="application/json")

db_pool = db_utils.DBUtil()

@app.route('/api/topup/',methods=['POST'])
def payment():
 request_data = request.get_json()
 if request_data and 'card_id' in request_data and 'amount' in request_data and 'payment_method' in request_data:
  card_id = request_data.get("card_id")
  amount = request_data.get("amount")
  payment_method = request_data.get("payment_method")
  payment_id = str(uuid.uuid4())
  try:
   with db_pool.get_db_cursor() as cur:
    payment_status = 'Success'
    insert_script = 'INSERT INTO pmt.payments (payment_id, card_id, amount, payment_method, payment_status) VALUES (%s, %s, %s, %s,%s)'
    insert_values = (f'{payment_id}',f'{card_id}', amount, payment_method, payment_status)
    cur.execute(insert_script, insert_values)
    timeout_seconds=5
    time.sleep(timeout_seconds)
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

