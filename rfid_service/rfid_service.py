from flask import Flask, request, Response
import jsonpickle
import db
from fare_deduction import fare_deduction

app = Flask(__name__)
dbconn = None
cur = None


def response500():
    response = {"success": False,
                "message": "unable to connect to db"}
    response_pickled = jsonpickle.encode(response)
    return Response(response=response_pickled, status=500, mimetype="application/json")


def response200():
    response = {"success": True}
    response_pickled = jsonpickle.encode(response)
    return Response(response=response_pickled, status=200, mimetype="application/json")


def response404():
    response = {'"success":false'}
    response_pickled = jsonpickle.encode(response)
    return Response(response=response_pickled, status=404, mimetype="application/json")


# get card info based on rfid number

@app.route('/api/card/rfid', methods=['GET'])
def card_exists():
    request_data = request.get_json()
    card_id = ''
    if request_data and 'card_id' in request_data :
        card_id = request_data['card_id']
    global dbconn, cur
    if dbconn is None:
        dbconn, cur = db.get_db()
    if dbconn is not None:
        get_script = f"SELECT * from rfid.card_detail where card_id='{card_id}'"
        cur.execute(get_script)
        record = cur.fetchall()
        if cur.rowcount == 0:
            return response404()
        response={}
        card_id = record[0][0]
        user_id = record[0][1]
        balance = str(record[0][2])
        isActive =record[0][3]
        response = {
                "card_id":card_id,
                "user_id":user_id,
                "balance":balance,
                "isActive":isActive,
        }

        response_pickled = jsonpickle.encode(response)
        return Response(response=response_pickled,status=200,mimetype ="application/json")
    else:
        return response500()


#     # tagon
#     #check card exists
#     # call fare deduction after the r
#     #double commit after call the endpoints
#
#     # tagoff
#     # check card exists
#     #
#     return response200()
@app.route('/api/card/rfid/deduction', methods=['POST'])
def deduction():
    request_data = request.get_json()
    card_id=request_data["card_id"]
    amount=request_data["amount"]
    global dbconn, cur
    if dbconn is None:
        dbconn, cur = db.get_db()
    update_script = f"UPDATE rfid.card_detail SET balance = balance-{amount},updated_at=CURRENT_TIMESTAMP where card_id='{card_id}'"
    cur.execute(update_script)
    if dbconn is not None:
        dbconn.commit()

    # if cur is not None:
    #     cur.close()
    # if dbconn is not None:
    #     dbconn.close()
    return response200()
@app.teardown_appcontext
def teardown_db(exception=None):
    global cur,dbconn
    if cur is not None:
        cur.close()
        cur = None
    if dbconn is not None:
        dbconn.close()
        dbconn = None
    print("tearing_down")


# create endpoint(deduction)
# to commit data
app.run(host="0.0.0.0", port=8080)
