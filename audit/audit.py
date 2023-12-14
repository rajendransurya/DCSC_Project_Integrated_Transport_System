import json
import os


import boto3
import redis
from dotenv import load_dotenv
# get environment variables

load_dotenv()



redisHost = os.getenv("REDIS_HOST")
redisPort = os.getenv("REDIS_PORT")

aws_access_key_id= os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
region = os.getenv('AWS_REGION')

JOURNEY_KEY = 'journeys'
TRANSACTION_KEY='transactions'
LOG_KEY= 'logging'


# connect to redis
r = redis.StrictRedis(host=redisHost, port=redisPort, db=1, decode_responses=True)

journey_table_name = 'journey'
transaction_table_name='transaction'

dynamodb=boto3.client(
            'dynamodb',
            region_name=region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )

def create_audit_records():
    journey_id=""
    try:
        print("Looking for a message")
        record_details_json = r.blpop([JOURNEY_KEY,TRANSACTION_KEY])
        record_details = json.loads(record_details_json[1])
        type = record_details.get("type")
        # print(journey_details)
        record_dict={}
        table_name = ''
        if type=='J':
            table_name = journey_table_name
            record_dict = {
                "journey_id": {'S': record_details.get("journey_id")},
                "card_id" : {'S': str(record_details.get("card_id"))},
                "mode_of_transport": {'S': record_details.get("mode_of_transport")},
                "start_time": {'S': record_details.get("start_time")},
                "end_time": {'S': record_details.get("end_time")},
                "fare_deducted": {'N': str(record_details.get("fare_deducted"))},
                "tagging_status": {'S': record_details.get("tagging_status")},
                "created_at": {'S': record_details.get("created_at")},
                "updated_at": {'S': record_details.get("updated_at")}
            }
        else:
            table_name=transaction_table_name
            record_dict={
                "transaction_id" : {'S':record_details.get("transaction_id")},
                "card_id" : {'S': str(record_details.get("card_id"))},
                "amount":{'N': str(record_details.get("amount"))},
                "payment_method":{'S':str(record_details.get("payment_method"))},
                "payment_status":{'S':str(record_details.get("payment_status"))},
                "created_at": {'S': record_details.get("created_at")},
                "updated_at": {'S': record_details.get("updated_at")}
            }

        response = dynamodb.put_item(TableName=table_name, Item=record_dict)
        if response.get("ResponseMetadata").get("HTTPStatusCode")==200:
            r.lpush(LOG_KEY, f"Created journey details in table for {journey_id}")
            print("Success")
        else:
            r.lpush(LOG_KEY, f"Error trying to create journey {journey_id}")
            print("Error")
    except Exception as exp:
        r.lpush(LOG_KEY, f"Exception raised in worker loop {journey_id}")
        print(f"Exception raised in worker loop: {str(exp)}")

# make the queue listen to keys
while True:
    create_audit_records()
