import json
import hmac
import hashlib
import logging
import boto3
import os
import re

log = logging.getLogger()
log.setLevel(logging.INFO)
ssm = boto3.client('ssm')

def lambda_handler(event, context):
    try:
        validate_sig(event['headers']['X-Hub-Signature-256'], event['body'])
    except Exception as e:
        api_exception_json = json.dumps(
            {
                "isError": True,
                "type": e.__class__.__name__,
                "message": str(e)
            }
        )
        raise LambdaException(api_exception_json)
    print("Request was successful")
    return {"message": "Request was successful"}
def validate_sig(header_sig, payload):
    github_secret = ssm.get_parameter(Name=os.environ['GITHUB_WEBHOOK_SECRET_SSM_KEY'], WithDecryption=True)['Parameter']['Value']
    try:
        sha, sig = header_sig.split('=')
    except ValueError:
        raise ClientException("Signature not signed with sha256 (e.g. sha256=123456)")

    if sha != 'sha256':
        raise ClientException('Signature not signed with sha256 (e.g. sha256=123456)')

    expected_sig = hmac.new(bytes(github_secret, 'utf-8'), bytes(str(payload), 'utf-8'), hashlib.sha256).hexdigest()

    authorized = hmac.compare_digest(str(sig), str(expected_sig))

    if not authorized:
       raise ClientException('Header signature and expected signature do not match')
    
    return authorized

class LambdaException(Exception):
    pass

class ClientException(Exception):
    pass