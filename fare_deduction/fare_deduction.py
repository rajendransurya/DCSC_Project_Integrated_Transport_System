import os
import sys
import uuid

import jsonpickle
import redis
from flask import Flask, request, Response
from decimal import Decimal
from datetime import datetime, timedelta
from .. import cache
import datetime

import db
import logging

log = logging.getLogger('werkzeug')
log.setLevel(logging.DEBUG)

redisHost = os.getenv("CACHE_HOST") or "localhost"
redisPort = os.getenv("CACHE_PORT") or 6379
JOURNEY_KEY = 'journeys'
LOG_KEY = 'logging'

# connect to redis

message_queue = redis.StrictRedis(host=redisHost, port=redisPort, db=1, decode_responses=True)

base_url = "http://localhost:7000/"
app = Flask(__name__)
dbconn = None
cur = None


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
def response500():
    response = {"success": False,
                "message": "unable to connect to db"}
    response_pickled = jsonpickle.encode(response)
    return Response(response=response_pickled, status=500, mimetype="application/json")


def response200():
    response = {"success": True}
    response_pickled = jsonpickle.encode(response)
    return Response(response=response_pickled, status=200, mimetype="application/json")


def response404(message):
    response = {"success": False,
                "message": message}
    response_pickled = jsonpickle.encode(response)
    return Response(response=response_pickled, status=404, mimetype="application/json")


def response400(message):
    response = {"success": False,
                "message": message}
    response_pickled = jsonpickle.encode(response)
    return Response(response=response_pickled, status=400, mimetype="application/json")


@app.route('/api/card/fare/fare_deduction', methods=['GET'])
def fare_deduction():
    request_data = request.get_json()
    if request_data and 'card_id' in request_data and 'zone' in request_data and 'timestamp' in request_data:
        card_id = request_data["card_id"]
        zone_no = request_data["zone_no"]
        timestamp = request_data["timestamp"]
        fare_id = -1
        fare_capping_id = -1
        fare_amount = -1
        tocap = True
        final_fare = -1
        capping_time_period = -1
        capping_max_amount = -1.00
        within_time_limit = True
        mode_id = -1
        mode_of_transport = None

        log.debug("Trying to get fare details from Cache")
        fare_details = cache.get_fare_details(zone_no)
        if fare_details:
            log.debug("Fare details were found in Cache")
            zone_no = fare_details.get("zone_no")
            mode_id = fare_details.get("mode_id")
            mode_of_transport = fare_details.get("mode_of_transport")
            fare_amount = fare_details.get("fare_amount")
            capping_time_period = fare_details.get("capping_time_period")
            capping_max_amount = fare_details.get("capping_max_amount")
            tocap = fare_details.get("tocap")

        else:
            log.debug("Fare details were not found in Cache looking into individual tables")
            #         get zone details
            zone_data, status_code, message = get_zone_details(zone_no)
            if status_code == 400:
                log.debug(message)
                return response400(message)
            elif status_code == 404:
                log.debug(message)
                return response404(message)
            elif status_code == 200:
                log.debug("Zone details found in Zone table")
                fare_id = zone_data.get("fare_id")
                fare_capping_id = zone_data.get("fare_capping_id")
                mode_id = zone_data.get("mode_id")
                mode_of_transport = zone_data.get("mode_of_transport")
            else:
                log.debug("Internal server error occured while trying to retrive data from Zone table")
                return response500()

            #         get fare details
            fare_data, status_code, message = get_fare_details(fare_id)
            if status_code == 200:
                log.debug("Fare details found in fare table")
                fare_amount = fare_data.get("amount")
            elif status_code == 400:
                log.debug(message)
                return response400(message)
            elif status_code == 404:
                log.debug(message)
                return response404(message)
            else:
                log.debug("Internal server error occured while trying to retrive data from Fare table")
                return response500()

            #         get fare_capping details
            capping_data, status_code, message = get_capping_details(fare_capping_id)
            if status_code == 404:
                log.debug("Fare capping not needed for this scenario")
                tocap = False
                capping_time_period = 0
                capping_max_amount = -1.00
            elif status_code == 200:
                log.debug("Fare capping details found in fare capping table")
                tocap = True
                capping_time_period = capping_data.get("time_period")
                capping_max_amount = capping_data.get("maxamount")
            else:
                return response500()
            fare_details = {
                "zone_no": zone_no,
                "mode_id": mode_id,
                "mode_of_transport": mode_of_transport,
                "fare_amount": fare_amount,
                "capping_time_period": capping_time_period,
                "capping_max_amount": capping_max_amount,
                "tocap": tocap
            }
            log.debug("Trying to put fare details in cache")
            result = cache.insert_fare_details(fare_details)
            if result is not None:
                log.debug(result)
                return response500()
            else:
                log.debug("Fare details updated in cache")

        #       check if fare can be capped
        if tocap:
            log.debug("Checking if the fare needs to be capped based on previous journeys")
            fare_cap, status_code, message = can_cap(card_id, zone_no, capping_time_period, capping_max_amount,
                                                     timestamp)
            if status_code == 200:
                tocap = fare_cap
            elif status_code == 404:
                log.debug(message)
                return response404(message)
            else:
                log.debug(message)
                return response500()

        #       check if within time limit
        expiration_time = None
        if not tocap:
            log.debug("Checking if the journey exists in the time window")
            within_time_limit, expiration_details, status_code, message = is_within_time_limit(card_id, timestamp)
            if status_code == 200:
                if expiration_details is not None:
                    expiration_time = expiration_details.get("expiration_time")
            elif status_code == 404:
                log.debug(message)
                return response404(message)
            else:
                log.debug("Internal server occured while checking if journey exists in time limit")
                return response500()

        #       check if tagoff
        log.debug("Checking if the journey is a tag off journey")
        tag_off, status_code, message = is_tag_off(card_id, zone_no, timestamp)
        if status_code != 200:
            if status_code == 404:
                log.debug(message)
                return response404(message)
            else:
                log.debug(message)
                return response500()

        #       calculate amount based on conditions like tag off, is within time limit
        if tag_off or within_time_limit:
            final_fare = 0.00
        else:
            final_fare = fare_amount

        response = {
            "amount": final_fare,
            "expiration_time": expiration_time,
            "tagoff": tag_off,
            "mode_id": mode_id,
            "mode_of_transport": mode_of_transport

        }
        response_pickled = jsonpickle.encode(response)
        log.debug("Fare details being returned to caller")
        return Response(response_pickled, status=200, mimetype="application/json")
    else:
        log.debug("Bad input for fare_calculation")
        return response400("Bad input for fare_calculation")


# get zone details
# @app.route('/api/card/fare/zones/<int:zone_no>',methods=['GET'])
def get_zone_details(zone_no):
    log.debug("Entering method for getting zone details")
    global dbconn, cur
    if dbconn is None:
        dbconn, cur = db.get_db()
    if dbconn is not None:
        select_script = f"SELECT * from fare.zone_detail where zone_no={zone_no}"
        try:
            cur.execute(select_script)
            record = cur.fetchall()
            if cur.rowcount == 0:
                return None, 404, "Zone Details Not Found"
            else:
                fare_id = record[0][1]
                fare_capping_id = record[0][2]
                mode_id = record[0][3]
                mode_of_transport = record[0][4]
                zone_details = {
                    "fare_id": fare_id,
                    "fare_capping_id": fare_capping_id,
                    "mode_id": mode_id,
                    "mode_of_transport": mode_of_transport
                }
                return zone_details, 200, None
        except Exception as error:
            log.debug(error)
            return None,500,error

    else:
        return None, 500, "Error Connecting to database"

# get fare details
# @app.route('/api/card/fare/fares/<int:fare_id>',methods=['GET'])
def get_fare_details(fare_id):
    global dbconn, cur
    if dbconn is None:
        dbconn, cur = db.get_db()
    if dbconn is not None:
        select_script = f"SELECT * from fare.fare_detail where fare_id={fare_id}"
        try:
            cur.execute(select_script)
            record = cur.fetchall()
            if cur.rowcount == 0:
                return None, 404, "Fare Details Not Found"
            else:
                amount = str(record[0][3])
                fare_details = {
                    "amount": str(amount),
                }
                return fare_details, 200, None
        except Exception as error:
            log.debug(error)
            return  None,500,error
    else:
        return None, 500, "Error Connecting to database"


# @app.route('/api/card/fare/fare_capping/<int:fare_capping_id>',methods=['GET'])
def get_capping_details(fare_capping_id):
    global dbconn, cur
    if dbconn is None:
        dbconn, cur = db.get_db()
    if dbconn is not None:
        select_script = f"SELECT * from fare.fare_capping where fare_capping_id={fare_capping_id}"
        try:
            cur.execute(select_script)
            record = cur.fetchall()
            if cur.rowcount == 0:
                return None, 404, "Fare capping not found"
            else:
                maxamount = str(record[0][4])
                time_period = record[0][3]
                capping_details = {
                    "time_period": time_period,
                    "maxamount": str(maxamount),
                }
                return capping_details, 200, None
        except Exception as error:
            log.debug(error)
            return None,500,error
    else:
        return None, 500, "Error Connecting to database"


def can_cap(card_id, zone_no, timeperiod, max_amount, timestamp):
    global dbconn, cur
    if dbconn is None:
        dbconn, cur = db.get_db()
    if dbconn is not None:
        select_script = f"SELECT card_id,zone_no,sum(amount) from fare.fare_deduction where card_id='{card_id}' and zone_no = {zone_no} and date(tagged_on_timestamp) between date({timestamp})-{timeperiod} and date({timestamp}) group by card_id,zone_no"
        try:
            cur.execute(select_script)
            message = None
            if cur.rowcount == 0:
                fare_cap = False
            else:
                record = cur.fetchall()
                fare_deducted = record[0][2]
                if fare_deducted >= max_amount:
                    fare_cap = True
                else:
                    fare_cap = False
            return fare_cap, 200, message
        except Exception as error:
            log.debug(error)
            return None,500,error
    else:
        return None, 500, "Error connecting to db"


def is_within_time_limit(card_id, time_stamp):
    global dbconn, cur
    if dbconn is None:
        dbconn, cur = db.get_db()
    if dbconn is not None:
        select_script = f"SELECT card_id,zone_no,tagged_on_timestamp,expiration_time from fare.fare_deduction where card_id='{card_id}' and DATE(tagged_on_timestamp) =Date('{time_stamp}') SORT BY tagged_on_timestamp DESC LIMIT 1"
        try:
            cur.execute(select_script)
            if cur.rowcount == 0:
                return False, None, 200, None
            else:
                record = cur.fetchall()
                # check if within limit
                if record[0][3] > 'timestamp':
                    result = {
                        "expiration_time": record[0][3]
                    }
                    return True, result, 200, None
                else:
                    return False, None, 200, None
        except Exception as error:
            log.debug(error)
            return None,None,500, error
    else:
        return None, None, 500, "Error trying to connect to db"


def is_tag_off(card_id, zone_no, mode_id, timestamp):
    global dbconn, cur
    if dbconn is None:
        dbconn, cur = db.get_db()
    if dbconn is not None:
        select_script = f"SELECT card_id,zone_no,mode_id,amount,tagged_on_timestamp from fare.fare_deduction where card_id='{card_id}' and DATE(tagged_on_timestamp) =Date('{timestamp}') SORT BY tagged_on_timestamp DESC LIMIT 1"
        try:
            cur.execute(select_script)
            if cur.rowcount == 0:
                return False, 200, None
            else:
                record = cur.fetchall()
                # check if within limit
                if zone_no != 1 and record[0][3] != 0.00 and (record[0][1] == zone_no or record[0][2] == mode_id):
                    return True, 200, None
                else:
                    return False, 200, None
        except Exception as error:
            log.debug(error)
            return None,500,error
    else:
        return None, 500, "Error trying to connect to db"


@app.route('/api/card/fare/deduction_', methods=['POST'])
def deduction():
    request_data = request.get_json()
    if request_data and 'card_id' in request_data and 'zone_no' in request_data and 'amount' in request_data and 'timestamp' in request_data and 'expiration_time' in request_data:
        card_id = request_data.get("card_id")
        zone_no = request_data.get("zone_no")
        mode_id = request_data.get("mode_id")
        amount = request_data.get("amount")
        tag_on = request_data.get("tag_on")
        tagged_on_timestamp = request_data.get("timestamp")
        expiration_time = request_data.get("expiration_time")
        mode_of_transport = request_data.get("mode_of_transport")
        end_time = tagged_on_timestamp
        tagging_status = 'OFF'
        if tag_on:
            end_time = ""
            tagging_status = 'ON'

        if expiration_time is None:
            expiration_time = f"{tagged_on_timestamp}+INTERVAL '90 minutes'"
        global dbconn, cur
        if dbconn is None:
            dbconn, cur = db.get_db()
            insert_script = 'INSERT INTO fare.Fare_Deduction (card_id, zone_no, amount, tagged_on_timestamp, expiration_time) VALUES (%s, %s, %s, %s,%s)'
            insert_values = (f'{card_id}', zone_no, amount, f'{tagged_on_timestamp}', f'{expiration_time}')
            try:
                cur.execute(insert_script, insert_values)
                if dbconn is not None:
                    dbconn.commit()
                    timestamp = datetime.now()
                    timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    journey_id = str(uuid.uuid4())
                    journey_details = {
                        "journey_id": {journey_id},
                        "card_id": {card_id},
                        "mode_of_transport": {mode_of_transport},
                        "start_time": {tagged_on_timestamp},
                        "end_time": {end_time},
                        "fare_deducted": {amount},
                        "tagging_status": {tagging_status},
                        "created_at": {timestamp},
                        "updated_at": {timestamp}
                    }
                    # Add values to the message queue
                    message_queue.lpush(LOG_KEY)
                    message_queue.lpush(LOG_KEY, f"Pushed journey data to queue {journey_id}")
                    return response200()
                else:
                    return response500()
            except Exception as error:
                log.debug(error)
                return response500()
    else:
        return response400("Insufficient or incorrect data to post data to fare deductions table")
