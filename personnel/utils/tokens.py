# personnel/utils/tokens.py

from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.conf import settings

SIGNER = TimestampSigner(salt='availability-response')
MAX_AGE = 60 * 60 * 24 * 30  # 30 days


def make_response_token(availability_request_id, response):
    """response is 'yes' or 'no'."""
    return SIGNER.sign(f"{availability_request_id}:{response}")


def parse_response_token(token):
    """
    Returns (availability_request_id, response) or raises BadSignature/SignatureExpired.
    """
    value = SIGNER.unsign(token, max_age=MAX_AGE)
    req_id, response = value.split(':', 1)
    return int(req_id), response