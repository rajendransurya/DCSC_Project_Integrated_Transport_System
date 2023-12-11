# get value from message queue and send email
import json
import os

import redis
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv
load_dotenv()



LOG_KEY= 'logging'
EMAIL_KEY ='mail'
redisHost = os.getenv("REDIS_HOST")
redisPort = os.getenv("REDIS_PORT")

sendgrid_key =  os.getenv('SENDGRID_API_KEY')
# connect to redis
r = redis.StrictRedis(host=redisHost, port=redisPort, db=1, decode_responses=True)



def send_mail():
    try:
        print("Looking for a message")
        #
        record_details_json = r.blpop([EMAIL_KEY])
        record_details = json.loads(record_details_json[1])

        message = Mail(
            from_email='itsboulderco@gmail.com',
            to_emails=f'{record_details.get("email")}',
            subject='Transaction updates',
            html_content=f'Dear {record_details.get("name")},<br>Your transaction {record_details.get("transaction_id")} for {record_details.get("amount")} was a {record_details.get("status")}.<br>Regards,<br> ITS Boulder Team')
        sg = SendGridAPIClient(sendgrid_key)
        print(sendgrid_key)
        response = sg.send(message)
        if response.status_code==200 or response.status_code==202:
            r.lpush(LOG_KEY, f"Mail sent successfully")
            print("Message sent successfully")
        else:
            r.lpush(LOG_KEY,f"An error occured while sending message. Status: {response.status_code},message: {response.body}")
            print(f"An error occured while sending message. Status: {response.status_code},message: {response.body},{response}")

    except Exception as exp:
        r.lpush(LOG_KEY, f"Exception raised in worker loop")
        print(f"Exception raised in worker loop: {str(exp)}")

while True:
    send_mail()