import sys
from decimal import Decimal

from flask import Flask, request, Response
import jsonpickle
import logging

sys.path.append('..')
print(sys.path)
from db import db_utils

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def make_response(data, status_code):
    response_pickled = jsonpickle.encode(data)
    return Response(response=response_pickled, status=status_code, mimetype="application/json")


db_pool = db_utils.DBUtil()  # Initialize the DB connection pool here


def card_exists():
    request_data = request.args
    card_id = request_data.get("card_id")
    print(f"Card id {card_id}")

    if not card_id:
        return make_response({"success": False, "message": "Insufficient or incorrect data"}, 400)

    try:
        with db_pool.get_db_cursor() as cur:
            cur.execute("SELECT card_id, user_id, balance, isActive FROM rfid.card_detail WHERE card_id=%s", (card_id,))
            record = cur.fetchone()

            if record is None:
                return make_response({"success": False, "message": "Card details not found"}, 404)

            card_id, user_id, balance, is_active = record
            balance = str(balance)

            if is_active:
                response = {
                    "card_id": card_id,
                    "user_id": user_id,
                    "balance": balance,
                    "isActive": is_active,
                }
                return make_response(response, 200)
            else:
                return make_response({"success": False, "message": "Card inactive"}, 404)
    except Exception as e:
        logger.error(f"Database execution error: {e}")
        return make_response({"success": False, "message": "Database execution error"},
                             500)  # Can also use 400 Bad Request for database execution issues


@app.route('/api/card/rfid', methods=['GET'])
def card_exists_endpoint():
    return card_exists()


def deduction():
    request_data = request.get_json()

    if request_data and 'card_id' in request_data and 'amount' in request_data:
        card_id = request_data["card_id"]
        amount = float(request_data["amount"])
        print(f'card_id {card_id} --- amount {amount}')

        try:

            with db_pool.get_db_cursor() as cur:
                cur.execute(
                    "UPDATE rfid.card_detail SET balance = balance + %s, updated_at=CURRENT_TIMESTAMP WHERE card_id=%s",
                    (amount, card_id))

            return make_response({"success": True}, 200)

        except Exception as e:
            logger.error(f"Database execution error: {e}")
            return make_response({"success": False, "message": "Database execution error"},
                                 500)  # Can also use 400 Bad Request for database execution issues

    else:
        return make_response({"success": False, "message": "Incorrect or insufficient data in request"}, 400)


@app.route('/api/card/rfid/deduction', methods=['POST'])
def deduction_endpoint():
    return deduction()

@app.route('/api/card/rfid/user',methods=['GET'])
def get_user():
    request_data = request.args
    card_id = request_data.get("card_id")
    print(f"Card id {card_id}")
    if not card_id:
        return make_response({"success": False, "message": "Insufficient or incorrect data"}, 400)
    try:

        with db_pool.get_db_cursor() as cur:
            cur.execute("SELECT user_id FROM rfid.card_detail WHERE card_id=%s", (card_id,))
            record = cur.fetchone()
            if record is None:
                return make_response({"success": False, "message": "Card details not found"}, 404)
            user_id = record
            cur.execute("SELECT first_name ,email from public.users where user_id = %s",(user_id))
            record = cur.fetchone()
            first_name,email = record
            if record is None:
                return make_response({"success": False, "message": "Card details not found"}, 404)
            response = {
                "card_id" : card_id,
                "first_name": first_name,
                "email":email
            }
            return make_response(response, 200)
    except Exception as e:
        logger.error(f"Database execution error: {e}")
        return make_response({"success": False, "message": "Database execution error"},500)

    # get user id from card data
    # get user email from card data
    # and return


@app.teardown_appcontext
def teardown_db(exception=None):
    logger.info("App request tear down")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6300, debug=True)
