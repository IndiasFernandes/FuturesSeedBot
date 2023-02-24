from twilio.rest import Client
from connect.config import *


def send_message(text):

    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    message = client.messages.create(
        from_='whatsapp:+14155238886',
        body=text,
        to='whatsapp:+351964205522'
    )

    # print(f"Message Sent:\n{message}")