from Flask import Flask, request, Response
import jsonpickle

app=Flask(__name__)

# routes for services
# tag end point
def response200():
    response = {'"success":true'}
    response_pickled = jsonpickle.encode(response)
    return Response(respose=response_pickled,status=200,mimetype="application/json")

@app.route('/api/tag', methods=['POST'])
def tag():
    # tagon
    #check card exists
    # call fare deduction after the r
    #double commit after call the endpoints

    # tagoff
    # check card exists
    #
    return response200()

#topup endpoint
@app.route('/api/topup',methods=['POST'])
def topup():
    return  response200()





