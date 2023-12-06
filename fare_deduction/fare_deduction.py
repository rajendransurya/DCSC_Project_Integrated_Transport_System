import sys

import jsonpickle
from flask import Flask, request, Response
from decimal import Decimal
from datetime import datetime, timedelta

import db
import requests

base_url ="http://localhost:7000/"
app = Flask(__name__)
dbconn = None
cur = None
#farecalculation
# get the fare details based on the zone from fare table and calculate fare
#send it to fare deduction

#fare deduction(card info, zone, time)
# call fare calculation to get the fare based on zone if the user alread has any data ad check capping table if there is any capping to be done
# even if amt is 0 if caping available record should be there in fare deductions and there should be no tag on tag of

# if zone same and the last entry also exists in the same zone, the second tap could mean a tag off( in case of train ), this is not required for bus
# based on fare deduct the amount from card


# create endpoint for deduction
#  if amount is zero just create journey

#create journey async

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
    response = {"success":False,
                "message":message}
    response_pickled = jsonpickle.encode(response)
    return Response(response=response_pickled, status=404, mimetype="application/json")

def response400(message):
    response = {"success":False,
                "message":message}
    response_pickled = jsonpickle.encode(response)
    return Response(response=response_pickled, status=400, mimetype="application/json")

@app.route('/api/card/fare/fare_calculation', methods=['GET'])
def fare_deduction():
    request_data = request.get_json()
    if request_data and 'card_id' in request_data and 'zone' in request_data and 'timestamp' in request_data:
        card_id = request_data["card_id"]
        zone_no = request_data["zone_no"]
        timestamp=request_data["timestamp"]

        # get zone details based on zone_no
        zone_detail_url = f"{base_url}api/card/fare/zones/{zone_no}"
        zone_detail_response= requests.get(zone_detail_url)
        fare_id = -1
        fare_capping_id = -1
        fare_amount = -1.00
        fare_capping_maxamount=-1.00
        fare_capping_time=-1
        fare_capping = False
        total_amount_deducted=-1
        can_cap=False
        tagoff= False
        final_fare=0.00
        start_time =''
        end_time=''
        deduct_fare = False
        if zone_detail_response.status_code == 200:
            zone_data = zone_detail_response.json()
            fare_id = zone_data.get("fare_id")
            fare_capping_id = zone_data.get("fare_capping_id")
            # get the fare
            fare_detail_url=f"{base_url}/api/card/fare/fares/{fare_id}"
            fare_detail_response = requests.get(fare_detail_url)
            if fare_detail_response.status_code==200:
                fare_data = fare_detail_response.json()
                fare_amount = fare_data.get("amount")
            else:
                return fare_detail_response
            #get fare capping
            fare_capping_url=f"{base_url}/api/card/fare/fare_capping/{fare_capping_id}"
            fare_capping_response = requests.get(fare_capping_url)
            if fare_capping_response.status_code == 200:
                fare_capping_data = fare_capping_response.json()
                fare_capping_maxamount = fare_capping_data.get("maxamount")
                fare_capping_time=fare_capping_data.get("time_period")
                fare_capping = True
            elif fare_capping_response.status_code == 404:
                fare_capping_maxamount=sys.float_info.max
                fare_capping_time=0
                fare_capping = False
            else:
                return fare_capping_response
            # check if fare capping needs to be done or not

            if fare_capping:
                journey_amount_url=f"{base_url}/api/card/fare/journey_amount/"
                params = {
                            'card_id': f'{card_id}',
                            'zone': {zone_no},
                            'timestamp': {timestamp}  # Replace with your timestamp format
                        }
                journey_amount_response=requests.get(journey_amount_url,params=params)
                if journey_amount_response.status_code==200:
                    journey_amount_data=journey_amount_response.json()
                    total_amount_deducted=journey_amount_data.get("total_fare_deducted")
                    if total_amount_deducted >= fare_capping_maxamount:
                        final_fare=0.00
                        can_cap=True
                    else:
                        final_fare=fare_amount
                        can_cap=False
                else:
                    return journey_amount_response
                # if its not bus zone
            if zone_no != 1:
                tagonoff_url = f"{base_url}/api/card/fare/tagonoff/"
                params = {
                    'card_id': f'{card_id}',
                    'zone': {zone_no},
                    'timestamp': {timestamp}
                }
                tagonoff_response=requests.get(tagonoff_url,params=params)
                if tagonoff_response.status_code==200:
                    tagonoff_data=tagonoff_response.json()
                    tagoff=tagonoff_data.get("tag_off")
                    start_time= tagonoff_data.get("start_time")
                    end_time = tagonoff_data.get("end_time")
                    deduct_fare = tagonoff_data.get("deduct_fare")
                else:
                    return tagonoff_response
            else:
                busfare_url= f"{base_url}/api/card/fare/bus_fare/"
                params = {
                    'card_id': f'{card_id}',
                    'zone': {zone_no},
                    'timestamp': {timestamp}
                }
                busfare_response=requests.get(busfare_url,params=params)
                if busfare_response.status_code==200:
                    busfare_response_data=busfare_response.json()
                    tagoff = busfare_response_data.get("tag_off")
                    start_time = busfare_response_data.get("start_time")
                    end_time = busfare_response_data.get("end_time")
                    deduct_fare = busfare_response_data.get("deduct_fare")










        else:
            return zone_detail_response


    #check if the journey already exists and if it is in the same zone

    else:
        return response400("Bad input for fare_calculation")

    #check if the journey already exists and if it is in the same zone





# get zone details
@app.route('/api/card/fare/zones/<int:zone_no>',methods=['GET'])
def get_zone_details(zone_no):
    global dbconn,cur
    if dbconn is None:
        dbconn, cur = db.get_db()
    if dbconn is not None:
        select_script = f"SELECT * from fare.zone_detail where zone_no={zone_no}"
        cur.execute(select_script)
        record = cur.fetchall()
        if cur.rowcount == 0:
            return response404("Zone Details Not Found")
        for row in record:
            zone_no = record[0][0]
            fare_id = record[0][1]
            fare_capping_id = record[0][2]
            response = {
                "zone_no": zone_no,
                "fare_id": fare_id,
                "fare_capping_id": fare_capping_id
            }
        response_pickled = jsonpickle.encode(response)
        return Response(response=response_pickled, status=200, mimetype="application/json")
    else:
        return response500()

# get fare details
@app.route('/api/card/fare/fares/<int:fare_id>',methods=['GET'])
def get_fare_details(fare_id):
    global dbconn,cur
    if dbconn is None:
        dbconn, cur = db.get_db()
    if dbconn is not None:
        select_script = f"SELECT * from fare.fare_detail where fare_id={fare_id}"
        cur.execute(select_script)
        record = cur.fetchall()
        if cur.rowcount == 0:
            return response404("Fare Details Not Found")
        for row in record:
            amount = str(record[0][3])
            response = {
                "fare_id": fare_id,
                "amount": str(amount),
            }
        response_pickled = jsonpickle.encode(response)
        return Response(response=response_pickled, status=200, mimetype="application/json")
    else:
        return response500()

@app.route('/api/card/fare/fare_capping/<int:fare_capping_id>',methods=['GET'])
def get_capping_details(fare_capping_id):
    global dbconn,cur
    if dbconn is None:
        dbconn, cur = db.get_db()
    if dbconn is not None:
        select_script = f"SELECT * from fare.fare_capping where fare_capping_id={fare_capping_id}"
        cur.execute(select_script)
        record = cur.fetchall()
        if cur.rowcount == 0:
            return response404("Fare capping not found")
        for row in record:
            maxamount = str(record[0][4])
            time_period=record[0][3]
            response = {
                "fare_capping_id": fare_capping_id,
                "time_period": time_period,
                "maxamount": str(maxamount),
            }
        response_pickled = jsonpickle.encode(response)
        return Response(response=response_pickled, status=200, mimetype="application/json")
    else:
        return response500()

@app.route('/api/card/fare/journey_amount/',methods=['GET'])
def get_journey_details():
    request_data=request.get_json()
    if request_data and 'card_id' in request_data and 'zone' in request_data and 'timestamp' in request_data:
        card_id=request_data["card_id"]
        zone_no = request_data["zone"]
        timestamp=request_data["timestamp"]
        global dbconn, cur
        if dbconn is None:
            dbconn, cur = db.get_db()
        if dbconn is not None:
            select_script=f"SELECT card_id,zone_no,DATE(start_time),sum(fare_deducted) from fare.Journey where card_id='{card_id}' and zone_no={zone_no} and DATE(start_time) =Date('{timestamp}') group by card_id,zone_no,DATE(start_time)"
            cur.execute(select_script)
            record = cur.fetchall()
            total_fare_deducted=0.00,
            if cur.rowcount != 0:
                for row in record:
                    total_fare_deducted=record[0][3]
            response={
                "total_fare_deducted" :total_fare_deducted
            }
            response_pickled = jsonpickle.encode(response)
            return Response(response=response_pickled, status=200, mimetype="application/json")
        else:
            return response500()
    else:
        return response400("Bad input for getting journey_details")

@app.route('/api/card/fare/tagonoff/',methods=['GET'])
def get_tagging_details():
    request_data = request.get_json()
    if request_data and 'card_id' in request_data and 'zone' in request_data and 'timestamp' in request_data:
        card_id=request_data["card_id"]
        zone_no = request_data["zone"]
        timestamp=request_data["timestamp"]
        global dbconn, cur
        if dbconn is None:
            dbconn, cur = db.get_db()
        if dbconn is not None:
            select_script=f"SELECT card_id,zone_no,tagging_status,start_time from fare.Journey where card_id='{card_id}' and DATE(start_time) =Date('{timestamp}') SORT BY start_time DESC"
            cur.execute(select_script)
            tag_off=True
            start_time = "NULL"
            end_time="NULL"
            deduct_fare = False

            if cur.rowcount ==0:
                tag_off=False
                start_time =timestamp
                end_time = "NULL"
                deduct_fare=True
            else:
                record = cur.fetchall()
                if record[0][1] == zone_no:
                    if record[0][2] == 'on':
                        tag_off=True
                        start_time = record[0][3]
                        end_time = timestamp
                        deduct_fare = False
                    else:
                        tag_off = False
                        start_time = timestamp
                        end_time = "NULL"
                        deduct_fare = True
                else:
                    maxtime=record[0][3]+timedelta(minutes=90)
                    if  timestamp <= maxtime:
                        tag_off = False
                        start_time = record[0][3]
                        end_time = "NULL"
                        deduct_fare = False
                    else:
                        tag_off = False
                        start_time = timestamp
                        end_time = "NULL"
                        deduct_fare = False


            response = {
                "card_id" : card_id,
                "tag_off" : tag_off,
                "start_time":start_time,
                "end_time":end_time,
                "deduct_fare":deduct_fare
            }
            response_pickled = jsonpickle.encode(response)
            return Response(response=response_pickled, status=200, mimetype="application/json")
        else:
            return response500()
    else:
        return response400("Bad input for getting tag on off details")


@app.route('/api/card/fare/bus_fare/',methods=['GET'])
def get_bus_fare():
    request_data = request.get_json()
    if request_data and 'card_id' in request_data and 'zone' in request_data and 'timestamp' in request_data:
        card_id = request_data["card_id"]
        zone_no = request_data["zone"]
        timestamp = request_data["timestamp"]
        global dbconn, cur
        if dbconn is None:
            dbconn, cur = db.get_db()
        if dbconn is not None:
            select_script = f"SELECT card_id,zone_no,tagging_status,start_time from fare.Journey where card_id='{card_id}' and DATE(start_time) =Date('{timestamp}') SORT BY start_time DESC"
            cur.execute(select_script)
            tag_off = True
            start_time = "NULL"
            end_time = "NULL"
            deduct_fare=False
            if cur.rowcount == 0:
                tag_off = False
                start_time = timestamp
                end_time = "NULL"
                deduct_fare=True
            else:
                record = cur.fetchall()
                maxtime = record[0][3] + timedelta(minutes=90)
                if timestamp<=maxtime:
                    tag_off = False
                    start_time = record[0][3]
                    end_time = "NULL"
                    deduct_fare = False
                else:
                    tag_off = False
                    start_time = timestamp
                    end_time = "NULL"
                    deduct_fare = True
                response={
                    "card_id" : card_id,
                    "tag_off" : tag_off,
                    "start_time":start_time,
                    "end_time":end_time,
                    "deduct_fare":deduct_fare
                }
                response_pickled = jsonpickle.encode(response)
                return Response(response=response_pickled, status=200, mimetype="application/json")
        else:
            return response500()
    else:
        return response400("Bad input for getting bus timing details")


@app.route('/api/card/fare/deduction/',methods=['POST'])
def perform_deductions():
    request_data = request.get_json()
    if request_data and 'deduction_id' in request_data and 'card_id' in request_data and 'amount' in request_data:
        return response200()
    else:
        return response500()









