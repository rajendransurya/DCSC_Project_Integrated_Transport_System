from flask import Flask, request, Response
import jsonpickle
import db
from fare_deduction import fare_deduction

app=Flask(__name__)
dbconn = None
cur = None
def response500():
    response = {'"success":false',
                '"message":"unable to connect to db"'}
    response_pickled = jsonpickle.encode(response)
    return Response(response=response_pickled,status=500,mimetype="application/json")

def response200():
    response = {'"success":true'}
    response_pickled = jsonpickle.encode(response)
    return Response(response=response_pickled,status=200,mimetype="application/json")

def return404():
    response={'"success":false'}
    response_pickled = jsonpickle.encode(response)
    return Response(response=response_pickled, status=404, mimetype="application/json")

# get card info based on rfid number

@app.route('/api/card/', methods=['POST'])
def card_exists():
    request_data = request.get_json()
    card_id=''
    zone =0
    if request_data and 'card_id' in request_data and 'zone' in request_data:
        card_id=request_data['card_id' ]
        zone = request_data['zone']
    global  dbconn,curr
    if dbconn is None:
        dbconn,cur= db.get_db()
    else:
        return response500()
    if dbconn is not None:
        get_script= f"SELECT * from rfid.card_detail where card_id='{card_id}'"
        cur.execute(get_script)
        record=cur.fetchall()
        if cur.rowcount==0:
            return  response500()
        for row in record:
            card_id = record[0][0]
            user_id : record[0][1]
            balance : record[0][2]
            isActive : record[0][3]
            created_at : record[0][4]
            updated_at : record[0][5]

        response=fare_deduction.fare_deductions()
        if response.status_code == 200:
            update_script=f"UPDATE rfid.card_detail SET balance = balance-10.00,updated_at=CURRENT_TIMESTAMP where card_id='{card_id}'"
            cur.execute(update_script)
            return response
        # return Response(response=respone_pickled,status=200,mimetype ="application/json")
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
@app.route('/api/card/deduction', methods=['POST'])
def deduction():
    global dbconn,cur
    if dbconn is not None:
        dbconn.commit()

    if cur is not None:
        cur.close()
    if dbconn is not None:
        dbconn.close()
    return response200()


# create endpoint(deduction)
# to commit data
app.run(host="0.0.0.0", port=8000)


