from dotenv import load_dotenv
from urllib.parse import urljoin, urlencode

import os

# Reads from the .env file and loads environment variables
# By default, load_dotenv doesn't override existing environment variables.
load_dotenv()

HOST = os.environ.get('HOST')

SQLALCHEMY_TRACK_MODIFICATIONS = os.environ.get('DATABASE_TRACK_CHANGES', False) == 'true'
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)

SECRET_KEY = os.environ.get('SECRET_KEY')

AUTH0_DOMAIN = os.environ.get('AUTH0_DOMAIN')
AUTH0_WELL_KNOWN = os.environ.get('AUTH0_WELL_KNOWN')
ALGORITHMS = os.environ.get('ALGORITHMS').split(';')
API_AUDIENCE = os.environ.get('API_AUDIENCE')

CLIENT_ID = os.environ.get('CLIENT_ID')

LOGIN_URL = urljoin(AUTH0_DOMAIN, 'authorize') + '?' + urlencode({
    'audience': API_AUDIENCE,
    'response_type': 'token',
    'client_id': CLIENT_ID,
    'redirect_uri': HOST,

})
