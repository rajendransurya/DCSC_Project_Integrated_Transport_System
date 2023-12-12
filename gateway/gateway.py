import decimal

from flask import Flask, request, Response
import jsonpickle
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


# routes for services
# tag end point


# Mock services
# rfid_card_service_url = 'http://localhost:6300/api/card/rfid'  # Replace with actual RFID Card Service URL
# fare_deduction_service_url = 'http://localhost:6100/api/card/fare'  # Replace with actual Fare Deduction Service URL
# payment_service_url = 'http://localhost:6200'  # Replace with actual Payment Service URL


@app.route('/api/tag', methods=['POST'])
def tag():
    # tagon
    # check card exists
    # call fare deduction after the r
    # double commit after call the endpoints

    # tagoff
    # check card exists

    card_id = request.json.get('card_id')
    zone_no = request.json.get('zone_no')
    response = Response

    # Validation of parameters
    if not card_id or not isinstance(zone_no, int):
        logger.debug('Invalid parameters provided for card details')
        response = Response(jsonpickle.encode({'error': 'Invalid parameters provided'}), status=400,
                            mimetype='application/json')

    try:

        # Call RFID Card Service to check card validity
        rfid_card_check = requests.get(f"{rfid_card_service_url}?card_id={card_id}")
        if rfid_card_check.status_code != 200 or not rfid_card_check.json().get('isActive'):
            logger.debug('RFID card validation failed')
            response = Response(jsonpickle.encode({'error': 'RFID card validation failed'}), status=400,
                                mimetype='application/json')
            return response
        # Call Fare Deduction Service to calculate fare
        fare_calculation = requests.get(f"{fare_deduction_service_url}?card_id={card_id}&zone_no={zone_no}")
        if fare_calculation.status_code != 200:
            logger.debug('Fare calculation failed')
            response = Response(jsonpickle.encode({'error': 'Fare calculation failed'}), status=400,
                                mimetype='application/json')
            return response

        fare_amount = fare_calculation.json().get('amount')
        # return error when balance is lower than fare amount
        # Perform fare deduction transactions
        balance = rfid_card_check.json().get('balance')
        if balance < fare_amount:
            logger.debug('Insufficient balance')
            response = Response(jsonpickle.encode({'error': 'Insufficient balance'}), status=400,
                                mimetype='application/json')
            return response
        try:
            rfid_deduct = requests.post(f"{rfid_card_service_url}/deduction",
                                        json={'amount': -fare_amount, 'card_id': card_id})
            fare_deduct = requests.post(f"{fare_deduction_service_url}/deduct", json=fare_calculation.json())

            # Check if both transactions were successful
            if rfid_deduct.status_code != 200 or fare_deduct.status_code != 200:
                # Revert transactions if either failed
                # Implement logic to revert transactions
                if rfid_deduct.status_code != 200:
                    # call delete of the fare_deduct with the value returned from the response
                    # {"deducted_id": 7} /api/card/fare/deduct?deducted_id = 7  => delete call
                    logger.debug('Handling error cases for fare deduction')
                    # print(f'Handling error cases for fare deduction')
                    deducted_id = fare_deduct.json().get('deducted_id')
                    fare_revert = requests.delete(f"{fare_deduction_service_url}/deduct?deducted_id={deducted_id}")
                    if fare_revert.status_code != 200:
                        return response

                if fare_deduct.status_code != 200:
                    # call revert of card balance
                    # amount from the response /api/card/rfid/deduct json={'amount': fare_amount}
                    card_revert = requests.post(f"{rfid_card_service_url}/deduction",
                                                json={'amount': fare_amount, 'card_id': card_id})
                    if card_revert.status_code != 200:
                        return card_revert

                    logger.debug(f'Handling error cases for card deduction')

                logger.debug('Transaction failed. Reverting changes...')
                response = Response(jsonpickle.encode({'error': 'Transaction failed. Reverting changes...'}),
                                    status=500, mimetype='')
                return response
            else:
                response = Response(jsonpickle.encode({'message': 'Transaction successful'}), status=200,
                                    mimetype='application/json')
                return response
        except Exception as e:
            # Handle exceptions
            logger.debug('An error occurred during transaction')
            response = Response(jsonpickle.encode({'error': 'An error occurred during transaction'}), status=500,
                                mimetype='application/json')
            return response

    except Exception as e:
        response = Response(jsonpickle.encode(f'error: {e}'), status=500, mimetype='application/json')
        return response
    # finally:
    #     return response


# topup endpoint
@app.route('/api/topup', methods=['POST'])
def topup():
    card_id = request.json.get("card_id")
    amount = request.json.get("amount")
    payment_method = request.json.get("payment_method")
    if not card_id or not payment_method or not isinstance(amount, decimal.Decimal):
        logger.debug('Invalid parameters provided for topup')
        response = Response(jsonpickle.encode({'error': 'Invalid parameters provided'}), status=400,
                            mimetype='application/json')
    try:
        # Call RFID Card Service to check card validity
        get_user = requests.get(f"{rfid_card_service_url}?card_id={card_id}")
        if get_user.status_code != 200:
            response = Response(jsonpickle.encode({'error': 'User not found'}), status=400,
                                mimetype='application/json')
            return response
        post_payment = requests.post(f"{payment_service_url}/api/topup/payment",
                                     json={'card_id': card_id, 'amount': amount, 'payment_method': payment_method,
                                           'email': get_user.json().get('email'),
                                           'name': get_user.json().get('name')}
                                     )
        if post_payment.status_code != 200:
            logger.debug('En error occured while trying to process payment')
            return post_payment
        if post_payment.json().get('status') == 'Success':
            rfid_topup = requests.post(f"{rfid_card_service_url}/deduction",
                                       json={'amount': amount, 'card_id': card_id})
            if rfid_topup.status_code != 200:
                logger.debug('En error occured while trying to topup')
                return rfid_topup
        response = Response(jsonpickle.encode({'message': 'Payment processed and email has been sent with status '
                                                          'successfully'}), status=200,
                            mimetype='application/json')
        return response

    except Exception as e:
        response = Response(jsonpickle.encode(f'error: {e}'), status=500, mimetype='application/json')
        return response
@app.route('/', methods=['GET'])
def hello():
    return '<h1> Music Separation Server</h1><p> Use a valid endpoint </p>'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9000, debug=True)
