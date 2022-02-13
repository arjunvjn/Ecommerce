from decouple import config
from twilio.rest import Client
import os

# To send OTP
def send(num):
    try:
        account_sid = os.environ[config('ACCOUNT_SID')] = config('ACCOUNT_SID')
        auth_token = os.environ[config('AUTH_TOKEN')] = config('AUTH_TOKEN')
        client = Client(account_sid, auth_token)

        verification = client.verify \
                            .services(config('SERVICE_ID')) \
                            .verifications \
                            .create(to='+91'+num, channel='sms')

        print(verification.status)
        return True
    except:
        return False

# To verify OTP
def verify(otp,num):
    account_sid = os.environ[config('ACCOUNT_SID')] = config('ACCOUNT_SID')
    auth_token = os.environ[config('AUTH_TOKEN')] = config('AUTH_TOKEN')
    client = Client(account_sid, auth_token)

    verification_check = client.verify \
                            .services(config('SERVICE_ID')) \
                            .verification_checks \
                            .create(to='+91'+num, code=otp)

    print(verification_check.status)
    return verification_check.status