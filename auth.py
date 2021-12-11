from datetime import datetime, timedelta
from functools import wraps, lru_cache
from flask import request
from jose import jwt

import functools
import requests


REQUIRES_AUTH = True
PAYLOAD = {}
AUTH0_DOMAIN = ''
AUTH0_WELL_KNOWN = ''
ALGORITHMS = []
API_AUDIENCE = ''

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def timed_cache(**timedelta_kwargs):
    """Timed cache decorator, uses timedelta class for expiration"""
    def _wrapper(f):
        update_delta = timedelta(**timedelta_kwargs)
        next_update = datetime.utcnow() + update_delta
        f = lru_cache(None)(f)

        @functools.wraps(f)
        def _wrapped(*args, **kwargs):
            nonlocal next_update
            now = datetime.utcnow()
            if now >= next_update:
                f.cache_clear()
                next_update = now + update_delta
            return f(*args, **kwargs)
        return _wrapped
    return _wrapper


# --------------------------------------------------------------------------- #
# Custom error classes
# --------------------------------------------------------------------------- #

class AuthError(Exception):
    """A standardized way to communicate auth failure modes"""

    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

# --------------------------------------------------------------------------- #
# Authentication helper functions
# --------------------------------------------------------------------------- #


def get_token_auth_header(headers):
    """
    Attempts to get the header from the (Flask) request
        - raises an AuthError if no header is present

    Attempts to split bearer and the token
        - raises an AuthError if the header is malformed

    Returns:
        - the token part of the header
    """
    if not headers.get('Authorization'):
        raise AuthError({
            'code': 'no_auth_header',
            'description': 'Authorization header is missing.'
        }, 401)

    try:
        bearer, token = headers.get('Authorization').split(' ')
    except BaseException:
        raise AuthError({
            'code': 'invalid_auth_header',
            'description': 'Invalid authorization header.'
        }, 400)

    if bearer != 'Bearer':
        raise AuthError({
            'code': 'invalid_auth_header',
            'description': 'Invalid authorization header.'
        }, 400)

    return token


def decode_token(token, key):
    """
    Decodes the payload from the token, validates the claims

    Arguments:
        - token: jwt token
        - key: rsa key

    Returns
        - payload: the decoded payload
    """
    try:
        payload = jwt.decode(
            token=token,
            key=key,
            algorithms=ALGORITHMS,
            audience=API_AUDIENCE,
            issuer=AUTH0_DOMAIN
        )
        return payload

    except jwt.ExpiredSignatureError:
        raise AuthError({
            'code': 'token_expired',
            'description': 'Token expired.'
        }, 401)

    except jwt.JWTClaimsError:
        raise AuthError({
            'code': 'invalid_claims',
            'description': 'Incorrect claims. Please, check the audience \
                and issuer.'
        }, 401)

    except BaseException:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Unable to parse authentication token.'
        }, 400)


def check_permissions(permission, payload):
    """
        Arguments:
            - permission: string permission (i.e. 'post:drink')
            - payload: decoded jwt payload

        - Raises an AuthError if permissions are not included in the payload
        - Raises an AuthError if the requested permission string is not in
        the payload permissions array

        Returns:
            - True: if permission exists
    """
    if not payload.get('permissions'):
        raise AuthError({
            'code': 'invalid_claims',
            'description': 'Permissions not included in JWT.'
        }, 400)

    if not payload.get('sub'):
        raise AuthError({
            'code': 'unauthorized',
            'description': 'Unable to find the subect ID.'
        }, 400)

    if permission not in payload.get('permissions'):
        raise AuthError({
            'code': 'unauthorized',
            'description': 'Permission not found.'
        }, 403)

    return True


@timed_cache(days=1)
def get_jwks(url):
    """
    Retrieves the jason web keys from Auth0

    Argumens:
        - url: Auth0 /.well-known/jwks.json address

    Returns:
        - dictionary with jw keys
    """
    return requests.get(url).json()


def verify_jwt(token):
    """
    Arguments:
        - token: a json web token (string)

    - It should be an Auth0 token with key id (kid)
    - Verifies the token using Auth0 /.well-known/jwks.json

    Returns:
        - rsa_key: key for decoding jwt
    """
    rsa_key = {}
    jw_keys = get_jwks(AUTH0_WELL_KNOWN)
    unverified_header = jwt.get_unverified_header(token)
    if not unverified_header.get('kid'):
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization malformed.'
        }, 401)

    for key in jw_keys.get('keys'):
        if key.get('kid') == unverified_header.get('kid'):
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }

    if not rsa_key:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Unable to find the appropriate key.'
        }, 400)

    return rsa_key

# --------------------------------------------------------------------------- #
# Authentication wrapper function
# --------------------------------------------------------------------------- #


def requires_auth(permission=''):
    """
    Arguments:
        - permission: string permission (i.e. 'post:drink')

    - Uses the get_token_auth_header method to get the token
    - Uses the verify_decode_jwt method to decode the jwt
    - Uses the check_permissions method validate claims and check the
        requested permission

    Returns:
        - the decorator which passes the decoded payload to the decorated
            method
    """
    def requires_auth_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            payload = PAYLOAD
            if REQUIRES_AUTH:
                token = get_token_auth_header(request.headers)
                key = verify_jwt(token)
                payload = decode_token(token, key)
                check_permissions(permission, payload)
            return func(*args, payload, **kwargs)
        return wrapper
    return requires_auth_decorator
