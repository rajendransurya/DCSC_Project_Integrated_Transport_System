import jsonpickle
from flask import Flask, request, Response
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
def fare_deductions():
    response = {'"success":true'}
    response_pickled = jsonpickle.encode(response)
    return Response(response=response_pickled, status=200, mimetype="application/json")
