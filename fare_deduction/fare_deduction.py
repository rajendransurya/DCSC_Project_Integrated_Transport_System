import json
import os
import sys
import uuid
import jsonpickle
import redis
from flask import Flask, request, Response
from decimal import Decimal
from datetime import datetime, timedelta
import logging

sys.path.append('..')
from db import db_utils

from dotenv import load_dotenv

# get environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

redisHost = os.getenv("REDIS_HOST")
redisPort = os.getenv("REDIS_PORT")
JOURNEY_KEY = 'journeys'
LOG_KEY = 'logging'

# connect to redis

redis_cache = redis.StrictRedis(host=redisHost, port=redisPort, db=0, decode_responses=True)
message_queue = redis.StrictRedis(host=redisHost, port=redisPort, db=1, decode_responses=True)

db_pool = db_utils.DBUtil()  # Initialize the DB connection pool here

app = Flask(__name__)


# farecalculation
# get the fare details based on the zone from fare table and calculate fare
# send it to fare deduction

# fare deduction(card info, zone, time) call fare calculation to get the fare based on zone if the user alread has
# any data ad check capping table if there is any capping to be done even if amt is 0 if caping available record
# should be there in fare deductions and there should be no tag on tag of

# if zone same and the last entry also exists in the same zone, the second tap could mean a tag off( in case of train
# ), this is not required for bus based on fare deduct the amount from card


# create endpoint for deduction
#  if amount is zero just create journey

# create journey async

# for tag off
# create new record in journey status to tag off and add status too


@app.route('/api/card/fare', methods=['GET'])
def fare_deduction():
    request_data = request.args
    card_id = request_data.get('card_id')
    zone_no = request_data.get("zone_no", type=int)

    if not card_id and not zone_no:
        logger.debug("Bad input for fare_calculation")
        return buildResponse(400, "Bad input for fare_calculation")

    logger.debug("Trying to get fare details from Cache")
    try:
        zone_details, status_code, message = get_zone_details(zone_no)
        if status_code != 200:
            logger.debug(message)
            return buildResponse(status_code, message)

        fare_details, status_code, message = get_fare_details(zone_details.get("fare_id"))
        if status_code != 200:
            logger.debug(message)
            return buildResponse(status_code, message)

        fare_capping, status_code, message = get_capping_details(zone_details.get("fare_id"))
        if status_code != 200:
            logger.debug(message)
            return buildResponse(status_code, message)

        # check if tagoff
        logger.debug("Checking if the journey is a tag off journey")
        tag_off, status_code, message = is_tag_off(card_id, zone_details.get("mode_id"), datetime.now())
        if status_code != 200:
            logger.debug(message)
            return buildResponse(status_code, message)

        # check if within time limit
        expiration_time = None
        logger.debug("Checking if the journey exists in the time window")
        within_time_limit, expiration_details, status_code, message = is_within_time_limit(card_id, datetime.now())
        if status_code != 200:
            logger.debug(message)
            return buildResponse(status_code, message)
        else:
            if expiration_details is not None:
                expiration_time = datetime.astimezone(expiration_details.get("expiration_time"))

        if fare_capping is None:
            fare_cap = False
        else:
            fare_cap, status_code, message = can_cap(card_id, zone_no, int(fare_capping.get("time_period")),
                                                     Decimal(fare_capping.get("max_amount")), datetime.now())
            if status_code != 200:
                logger.debug(message)
                return buildResponse(status_code, message)

        #       calculate amount based on conditions like tag off, is within time limit
        if tag_off or within_time_limit or fare_cap:
            final_fare = 0.00
        else:
            final_fare = fare_details.get("amount")

        response = {
            "amount": final_fare,
            "expiration_time": str(expiration_time),
            "tagoff": tag_off,
            "fare_cap": fare_cap,
            "mode_id": zone_details.get('mode_id'),
            "mode_of_transport": fare_details.get('mode_of_transport')
        }

        response_pickled = jsonpickle.encode(response)
        logger.debug("Fare details being returned to caller")
        return Response(response_pickled, status=200, mimetype="application/json")
    except Exception as error:
        logger.error(f"Error: Calculting fare {error}")
        return buildResponse(500, "Error occured while calculting fare")


@app.route('/api/card/fare/deduct', methods=['POST'])
def deduction():
    request_data = request.get_json()
    if request_data and 'card_id' in request_data and 'zone_no' in request_data and 'mode_id' in request_data and 'amount' in request_data and 'timestamp' in request_data and 'expiration_time' in request_data and 'mode_of_transport' in request_data:
        card_id = request_data.get("card_id")
        zone_no = request_data.get("zone_no")
        mode_id = request_data.get("mode_id")
        amount = request_data.get("amount")
        tag_on = request_data.get("tag_on")
        tagged_on_timestamp = request_data.get("timestamp")
        expiration_time = request_data.get("expiration_time")
        mode_of_transport = request_data.get("mode_of_transport")
        end_time = tagged_on_timestamp
        tagging_status = 'ON'
        if tag_on:
            end_time = ""
            tagging_status = 'OFF'

        if expiration_time is None:
            expiration_time = f"{tagged_on_timestamp}+INTERVAL '90 minutes'"
        try:
            with db_pool.get_db_cursor() as cur:
                insert_script = 'INSERT INTO fare.Fare_Deduction (card_id, zone_no, mode_id, amount, tagged_on_timestamp, expiration_time) VALUES (%s, %s, %s, %s,%s,%s) RETURNING deduction_id'
                insert_values = (f'{card_id}', zone_no, mode_id, amount, f'{tagged_on_timestamp}', f'{expiration_time}')
                cur.execute(insert_script, insert_values)
                record = cur.fetchone()
            if not record:
                raise Exception("Failed to inserted failed with no row id")

            # last inserted id
            deducted_id = record[0]

            timestamp = datetime.now()
            timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
            journey_id = str(uuid.uuid4())
            journey_details = {
                "type": 'J',
                "journey_id": journey_id,
                "card_id": card_id,
                "mode_of_transport": mode_of_transport,
                "start_time": tagged_on_timestamp,
                "end_time": end_time,
                "fare_deducted": amount,
                "tagging_status": tagging_status,
                "created_at": timestamp,
                "updated_at": timestamp
            }
            journey_details_json = json.dumps(journey_details)
            # Add values to the message queue
            message_queue.lpush(LOG_KEY, f"Pushed journey data to queue {journey_id}")
            message_queue.lpush(JOURNEY_KEY, journey_details_json)
            return Response(jsonpickle.encode({'deducted_id': deducted_id}), status=200, mimetype="application/json")
        except Exception as error:
            logger.error(f"Error: Deducting fare {error}")
            return buildResponse(500, "Server error")
    else:
        return buildResponse(400, "Insufficient or incorrect data to post data to fare deductions table")


@app.route('/api/card/fare/deduct', methods=['DELETE'])
def deductionDelete():
    request_data = request.args
    if request_data and 'deducted_id':
        deducted_id = request_data.get('deducted_id')
        try:
            with db_pool.get_db_cursor() as cur:
                cur.execute("DELETE FROM fare.Fare_Deduction WHERE deduction_id = %s", (deducted_id,))

            logs.info(f'Deduction reverted for {deducted_id}')
            return buildResponse(200, "Successful")
        except Exception as error:
            logger.error(f"Error: Reverting deduction fare {error}")

    return buildResponse(500, "Server error")


# get zone details
def get_zone_details(zone_no):
    logger.debug("Entering method for getting zone details")
    try:
        zone_details = getCached_value(zone_no)
        if not zone_details:
            with db_pool.get_db_cursor() as cur:
                cur.execute("SELECT * from fare.zone_detail where zone_no=%s", (zone_no,))
                record = cur.fetchone()
            if not record:
                return None, 404, "Zone Details Not Found"
            else:
                zone_details = dict()
                zone_details["zone_id"] = record[0]
                zone_details["zone_no"] = record[1]
                zone_details["fare_id"] = record[2]
                zone_details["mode_id"] = record[3]
                logger.info(
                    f"{zone_details.get('fare_id')} --- {zone_details.get('zone_id')} -- {zone_details.get('mode_id')} -- {zone_details.get('zone_no')}")
                setCached_value(zone_no, zone_details)
        return zone_details, 200, None
    except Exception as error:
        logger.error(error)
        return None, 500, "Error Connecting to database"


# get fare details
def get_fare_details(fare_id):
    try:
        fare_details = getCached_value(fare_id)
        if not fare_details:
            with db_pool.get_db_cursor() as cur:
                cur.execute("SELECT amount, mode_of_transport from fare.fare_detail where fare_id= %s", (fare_id,))
                record = cur.fetchone()
            if not record:
                return None, 404, "Fare Details Not Found"
            else:
                amount = Decimal(record[0])
                fare_details = {
                    "amount": str(amount),
                    "mode_of_transport": str(record[1])
                }
                setCached_value(fare_id, fare_details)
        return fare_details, 200, None
    except Exception as error:
        logger.debug(error)
        return None, 500, "Error Connecting to database"


# get fare capping details
def get_capping_details(fare_id):
    try:
        fare_capping_details = getCached_value(str(f"Cap-{fare_id}"))
        if not fare_capping_details:
            with db_pool.get_db_cursor() as cur:
                cur.execute("SELECT time_period, max_amount from fare.fare_capping where fare_id = %s", (fare_id,))
                record = cur.fetchall()
            if not record:
                return None, 200, "Fare capping not found"
            else:
                for cap in record:
                    time_period = int(cap[0])
                    maxamount = Decimal(cap[1])
                    fare_capping_details = {
                        "time_period": time_period,
                        "max_amount": str(maxamount),
                    }
                setCached_value(str(f"Cap-{fare_id}"), fare_capping_details)
                return fare_capping_details, 200, None
        else:
            return fare_capping_details, 200, None
    except Exception as error:
        logger.error(error)
        return None, 500, "Error Connecting to database"


# get is capped fare
def can_cap(card_id, zone_no, timeperiod, max_amount, timestamp):
    try:
        current_date = datetime.now()
        if timeperiod > 1:
            start_day = current_date - timedelta(days=current_date.weekday())
        else:
            start_day = current_date
        with db_pool.get_db_cursor() as cur:
            select_script = f"SELECT sum(amount) from fare.fare_deduction where card_id='{card_id}' and zone_no = {zone_no} and tagged_on_timestamp between '{start_day}' and '{timestamp}' group by card_id, zone_no"
            cur.execute(select_script)
            record = cur.fetchone()
            message = None
        if not record:
            fare_cap = False
        else:
            fare_deducted = Decimal(record[0])
            if fare_deducted >= max_amount:
                fare_cap = True
            else:
                fare_cap = False
        return fare_cap, 200, message
    except Exception as error:
        logger.debug(error)
        return None, 500, "Error connecting to db"


# check the 90 minute window
def is_within_time_limit(card_id, time_stamp):
    try:
        with db_pool.get_db_cursor() as cur:
            select_script = f"SELECT expiration_time from fare.fare_deduction where card_id='{card_id}' and expiration_time > current_timestamp ORDER BY expiration_time DESC LIMIT 1"
            cur.execute(select_script)
            record = cur.fetchone()
        if not record:
            # check if within limit
            print(f'We got no record for expiration time')
            result = {
                "expiration_time": datetime.now() + timedelta(minutes=90)
            }
            return False, result, 200, None
        else:
            # check if within limit
            result = {
                "expiration_time": record[0]
            }
            return True, result, 200, None
    except Exception as error:
        logger.debug(error)
        return None, None, 500, "Error trying to connect to db"


# determine is tag on/off
def is_tag_off(card_id, mode_id, timestamp):
    try:
        with db_pool.get_db_cursor() as cur:
            select_script = f"SELECT mode_id, amount from fare.fare_deduction where card_id='{card_id}' AND mode_id={mode_id} ORDER BY tagged_on_timestamp DESC LIMIT 1"
            cur.execute(select_script)
            record = cur.fetchone()
        if not record:
            return False, 200, None
        else:
            with db_pool.get_db_cursor() as cur:
                cur.execute("Select fare_type from fare.fare_mode where mode_id = %s", (record[0],))
                faremode_record = cur.fetchone()
            if not faremode_record:
                return False, 200, None

            # check if within limit
            if not faremode_record[0]:
                return True, 200, None
            else:
                return False, 200, None
    except Exception as error:
        logger.debug(error)
        return None, 500, "Error trying to connect to db"


def setCached_value(key, value):
    try:
        redis_cache.hset(f"{key}", mapping=value)
        redis_cache.expire(f"{key}", 24 * 60 * 60)
        return None
    except redis.ResponseError as e:
        return e.args[0]
    except ConnectionError as e:
        return e.args[0]


def getCached_value(key):
    try:
        return redis_cache.hgetall(f"{key}")
    except redis.ResponseError as e:
        return e.args[0]
    except ConnectionError as e:
        return e.args[0]


@app.teardown_appcontext
def teardown_db(exception=None):
    logger.info("App request tear down")


# Response builder
def buildResponse(status_code, message):
    response = {"success": status_code == 200,
                "message": message}
    response_pickled = jsonpickle.encode(response)
    return Response(response=response_pickled, status=status_code, mimetype="application/json")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6100, debug=True)
